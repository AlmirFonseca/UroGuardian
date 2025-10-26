/**
 * Sistema de Aquisição de Dados do ESP32 para Sensor de Cor
 *
 * Funcionalidade:
 *  - Leitura do sensor AS7341 (I2C, 0x39) para espectro de cor.
 *  - Registro de data/hora com RTC DS3231 (I2C, 0x68).
 *  - Controle de LED SK6812 RGBW para sinalização das capturas.
 *  - Acorda do modo light sleep via trigger no pino IO34 (LOW).
 *  - Conectividade WiFi e envio dos dados coletados para broker MQTT.
 *  - Envia dados nos tópicos: spectrumdatapoints (amostras), logs (erros/boot), telemetry (RAM, uptime, sinal WiFi).
 * 
 * Fluxo operacional:
 *   1. Inicialização dos sensores e entrada em light sleep.
 *   2. Ao detectar trigger LOW, acorda e realiza sequência de leituras, ativando LED e coletando espectro.
 *   3. Armazena amostras em batch para envio posterior.
 *   4. Quando o trigger volta para HIGH, conecta WiFi/MQTT, envia dados e encerra conexão.
 *   5. Após envio do batch, publica telemetria.
 *   6. Se acordar por timer, envia apenas telemetria.
 *
 * Observações:
 *   - Parâmetros configuráveis destacados em defines.
 *   - Estrutura modular para fácil manutenção.
 */

#include <ArduinoJson.h>
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_AS7341.h>
#include <Adafruit_NeoPixel.h>
#include <RTClib.h>
#include <PubSubClient.h>
#include "esp_sleep.h"

// === DEFINES E CONFIGURAÇÕES ===

// Pinos e parâmetros de hardware
#define TRIGGER_PIN 6          // Pino digital para trigger de consulta (LOW ativa coleta)
#define LED_PIN 7              // Pino de controle do LED SK6812
#define NUM_LEDS 1             // Número de LEDs RGBW no sistema
#define LED_INTENSITY_PCT 100   // Intensidade do LED (em %)
#define I2C_SDA 9              // Pino I2C - SDA
#define I2C_SCL 8              // Pino I2C - SCL

// Sensor AS7341
#define AS7341_GAIN AS7341_GAIN_512X // Ganho em 0_5X, 1X, 2X, 4X, 8X, 16X, 32X, 64X, 128X, 256X, 512X
// #define AS7341_ASTEP 999 // Integration time ((ASTEP_VALUE+1) * 2.78 uS)
// #define AS7341_ATIME 100 // Integration step count (Total = (ATIME + 1) * (ASTEP + 1) * 2.78µS)

// Parâmetros de temporização e buffer
#define DEEP_SLEEP_SEC 600     // Intervalo do timer para telemetria (em segundos)
#define BUFFER_SIZE 50         // Tamanho máximo de amostras em um batch
#define BATCH_SIZE 3           // Número de amostras por cor em cada batch

// Rede WiFi e MQTT
#define WIFI_SSID "VIVOFIBRA-6824"
#define WIFI_PASSWORD "N5Qfqaufwb"
#define MQTT_BROKER_IP "192.168.0.168"
#define MQTT_PORT 1883
#define MQTT_TOPIC_DATA "spectrumdatapoints"
#define MQTT_TOPIC_LOG "logs"
#define MQTT_TOPIC_TELEMETRY "telemetry"

// === OBJETOS GLOBAIS E ESTRUTURAS ===

/**
 * Objeto para sensor espectral AS7341.
 * Comunica via I2C e fornece canais do espectro óptico.
 */
Adafruit_AS7341 as7341;

/**
 * Objeto para RTC DS3231.
 * Gerencia data/hora real para timestamp de amostras.
 */
RTC_DS3231 rtc;

/**
 * Objeto para strip de LED SK6812 RGBW.
 * Controla as cores de sinalização durante ciclo de coleta.
 */
Adafruit_NeoPixel led(NUM_LEDS, LED_PIN, NEO_RGBW + NEO_KHZ800);

/**
 * Cliente de rede para comunicação com broker MQTT.
 */
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

/**
 * Estrutura para armazenar dados de espectro por amostra.
 * Cada amostra inclui data/hora, batch, flag de início/fim, cor do LED, intensidade e todos os canais espectrais.
 */
struct SpectrumDatapoint
{
    uint32_t timestamp;        // Registro de data/hora (UNIX time)
    uint8_t batch;             // Identificação do batch de coleta
    int8_t flag;               // Flag: 1=primeira, 0=intermediária, -1=última amostra do lote
    String ledcolor;           // Cor do LED utilizada ("R", "G", "B", "W")
    uint8_t ledintensity;      // Intensidade do LED (0-100)
    uint16_t channels[12];     // Valores de cada canal óptico do AS7341
};

// Buffer de armazenamento dos dados coletados
SpectrumDatapoint batchData[BUFFER_SIZE]; // Array real de structs
uint8_t bufferHead = 0;      // Índice onde será inserida a próxima amostra
uint8_t bufferCount = 0;     // Número atual de elementos válidos (até BUFFER_SIZE)

uint8_t ledIntensity = map(LED_INTENSITY_PCT, 0, 100, 0, 255);   // Intensidade do LED convertida para escala 0-255
String macAddress = "";        // MAC Address do dispositivo, preenchido pós WiFi


// === FUNÇÕES DE LOG

/**
 * Envia mensagem de log localmente (Serial) e para o broker MQTT (tópico de logs).
 *
 * @param msg Mensagem do log
 * @param code Código identitário do evento/erro
 * @param timestamp (Opcional) Define uso de timestamp ou zero
 */
void logMsg(String msg, String code, bool timestamp=true)
{
    Serial.println(msg);

    if (mqttClient.connected())
    {
        String payload = "{";
        payload += "\"mac_address\":\"" + macAddress + "\",";
        payload += "\"timestamp\":" + String(timestamp ? rtc.now().unixtime() : 0) + ",";
        payload += "\"error_code\":\"" + code + "\",";
        payload += "\"error_message\":\"" + msg + "\"";
        payload += "}";
        mqttClient.publish(MQTT_TOPIC_LOG, payload.c_str());
    }
}


// === FUNÇÕES DE HARDWARE E SENSORES ===

/**
 * Adiciona uma nova amostra ao buffer circular.
 * Se o buffer estiver cheio, sobrescreve a amostra mais antiga.
 */
void addDatapoint(const SpectrumDatapoint &dp) {
    // Adiciona nova amostra na posição do head
    batchData[bufferHead] = dp;
    // Atualiza head e count
    bufferHead = (bufferHead + 1) % BUFFER_SIZE;
    if (bufferCount < BUFFER_SIZE)
        bufferCount++;
    // Se passar do tamanho, sobrescreve os mais antigos; bufferCount fica sempre <= BUFFER_SIZE
    else logMsg("Buffer full, overwriting oldest data", "BUFFER_OVR");
}

/**
 * Itera sobre os dados no buffer circular em ordem cronológica.
 * Executa a função callback para cada amostra válida.
 */
void forEachDatapoint(void (*callback)(const SpectrumDatapoint &)) {
    // Itera do mais antigo (bufferHead - bufferCount) até o mais recente (bufferHead - 1)
    for (uint8_t i = 0; i < bufferCount; i++) {
        // Calcula índice circular
        uint8_t idx = (bufferHead + BUFFER_SIZE - bufferCount + i) % BUFFER_SIZE;
        // Chama a função de callback com a amostra atual
        callback(batchData[idx]);
    }
}

/**
 * Inicializa o barramento I2C e sensores (AS7341, LED).
 * Retorna true se tudo OK, false se houve erro.
 */
bool setupSensors()
{
    // Verificação do sensor AS7341
    if (!as7341.begin())
    {
        logMsg("AS7341 não encontrado!", "ERR_AS7341");
        return false;
    }

    // as7341.setATIME(AS7341_ATIME);
    // as7341.setASTEP(AS7341_ASTEP);
    as7341.setGain(AS7341_GAIN);

    // Print gain, time, astep and tint
    Serial.print("AS7341 Gain: ");
    Serial.println(as7341.getGain());
    Serial.print("AS7341 ATIME: ");
    Serial.println(as7341.getATIME());
    Serial.print("AS7341 ASTEP: ");
    Serial.println(as7341.getASTEP());
    Serial.print("AS7341 TINT: ");
    Serial.println(as7341.getTINT());

    // Inicialização do LED
    led.begin();
    led.clear();
    led.show();

    return true;
}

/**
 * Inicializa o RTC DS3231 e ajusta data/hora se perdeu energia.
 * Retorna true se tudo OK, false em caso de erro.
 */
bool setupRTC()
{
    if (!rtc.begin())
    {
        logMsg("DS3231 não encontrado!", "ERR_RTC", false);
        return false;
    }
    if (rtc.lostPower())
    {
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
    return true;
}

/**
 * Ativa o LED na cor especificada, com breve sinalização.
 *
 * @param color String: "R", "G", "B" ou "W", cor do LED a acender.
 */
void setLedColor(const String &color)
{
    uint32_t rgbw = 0;
    if (color == "R")
        rgbw = led.Color(ledIntensity, 0, 0, 0);
    else if (color == "G")
        rgbw = led.Color(0, ledIntensity, 0, 0);
    else if (color == "B")
        rgbw = led.Color(0, 0, ledIntensity, 0);
    else if (color == "W")
        rgbw = led.Color(0, 0, 0, ledIntensity);

    led.fill(rgbw, 0, NUM_LEDS);
    led.show();
    delay(50); // Delay para estabilizar
    led.clear(); // Apaga LED após sinalização
    led.show();
}

/**
 * Realiza leitura do AS7341 para todos os canais, registra a cor do LED e armazena no buffer.
 *
 * @param color Cor do LED utilizada ("R", "G", "B", "W")
 * @param batch Identificador do lote de coleta
 * @param flag Identificador da posição (1=primeira, 0=intermediária, -1=última)
 */
void collectDatapoint(const String &color, uint8_t batch, int8_t flag)
{
    // setLedColor(color);
    SpectrumDatapoint dp;

    delay(100);

    as7341.readAllChannels(dp.channels);



    dp.timestamp = rtc.now().unixtime();
    dp.batch = batch;
    dp.flag = flag;
    dp.ledcolor = color;
    dp.ledintensity = LED_INTENSITY_PCT;

    addDatapoint(dp);
}

/**
 * Monta e envia ao broker pacote JSON com dados de telemetria:
 * - RAM, PSRAM, heap, uptime, espaço sketch, sinal WiFi, IP e MAC.
 */
void sendTelemetry()
{
    logMsg("Sending telemetry...", "TELEMETRY_START");

    StaticJsonDocument<384> doc; // ajuste conforme campos

    doc["mac_address"] = macAddress;
    doc["timestamp"] = rtc.now().unixtime();
    doc["uptime_ms"] = millis();
    doc["cpu_frequency"] = ESP.getCpuFreqMHz();
    doc["ram_usage"] = (float)ESP.getFreeHeap() / (float)ESP.getHeapSize() * 100.0;
    doc["temp"] = rtc.getTemperature();
    doc["wifi-ssid"] = WiFi.SSID();
    doc["wifi_signal"] = WiFi.RSSI();
    doc["ip"] = WiFi.localIP().toString();
    doc["sketch_md5"] = ESP.getSketchMD5();
    doc["sketch_size"] = ESP.getSketchSize();

    char payload[384];
    size_t n = serializeJson(doc, payload, sizeof(payload));

    // Envia telemetria via MQTT se a conexão estiver OK
    if (mqttClient.connected()) {
        mqttClient.publish(MQTT_TOPIC_TELEMETRY, payload, n);
        Serial.println(payload);
    } else {
        Serial.println("Telemetry not sent, MQTT not connected");
    }
}

/**
 * Envia os dados coletados, amostra por amostra, para o broker no tópico spectrumdatapoints.
 */
void sendBatchData(uint8_t batchCount) {
    // Calcula o tamanho apropriado do documento
    StaticJsonDocument<2048> doc; // tamanho grande para muitos pontos; ajuste conforme o uso
    JsonArray arr = doc.createNestedArray("batch");

    uint8_t num_datapoints = batchCount * 4; // 4 cores por batch

    // Constrói array JSON a partir do buffer circular
    for (uint8_t i = 0; i < num_datapoints; i++) {
        uint8_t idx = (bufferHead + BUFFER_SIZE - num_datapoints + i) % BUFFER_SIZE;
        const SpectrumDatapoint &data = batchData[idx];
        JsonObject dp = arr.createNestedObject();
        dp["timestamp"] = data.timestamp;
        dp["batch"] = data.batch;
        dp["flag"] = data.flag;
        dp["ledcolor"] = data.ledcolor;
        dp["ledintensity"] = data.ledintensity;
        // Adiciona os canais como array
        JsonArray chArr = dp.createNestedArray("channels");
        for (uint8_t c = 0; c < 12; c++) {
            chArr.add(data.channels[c]);
        }
    }

    char payload[2048];
    size_t n = serializeJson(doc, payload, sizeof(payload));

    if (mqttClient.connected()) {
        mqttClient.publish(MQTT_TOPIC_DATA, payload, n);
        Serial.println("spectrum_datapoint sent: " + String(payload));
    } else {
            Serial.println("spectrum_datapoint not sent, MQTT not connected");
    }

    delay(50);
}

// === FUNÇÕES DE CONEXÃO E REDES ===

/**
 * Garante conexão WiFi. Realiza tentativa de conexão e atualiza MAC Address global.
 *
 * @param timeoutSec Tempo máximo em segundos para tentativas
 * @return true se conectado, false caso contrário
 */
bool ensureWiFi(uint16_t timeoutSec = 20) {
    logMsg("Connecting to WiFi...", "WIFI_CONN");
    if (WiFi.status() == WL_CONNECTED) return true;
    WiFi.disconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    uint16_t retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < timeoutSec) {
        Serial.print(".");
        delay(1000);
        retry++;
    }
    Serial.println();
    macAddress = WiFi.macAddress();
    logMsg(WiFi.status() == WL_CONNECTED ? "WiFi connected" : "WiFi connection failed",
           WiFi.status() == WL_CONNECTED ? "WIFI_OK" : "WIFI_FAIL");
    return WiFi.status() == WL_CONNECTED;
}

/**
 * Garante conexão MQTT. Realiza tentativas de reconexão e ajusta buffer.
 *
 * @param retries Número de tentativas
 * @return true se conectado, false caso contrário
 */
bool ensureMQTT(uint8_t retries = 5) {
    mqttClient.setServer(MQTT_BROKER_IP, MQTT_PORT);
    for (uint8_t i = 0; i < retries; i++) {
        if (mqttClient.connect("ESP32Client")) {
            Serial.println("MQTT connected");
            mqttClient.setBufferSize(4096); // Ajusta buffer para payloads grandes
            logMsg("MQTT connected", "MQTT_OK");
            return true;
        }
        Serial.println("MQTT connection failed, retrying...");
        delay(1000);
    }
    return false;
}

/**
 * Garante que todos os dados MQTT foram enviados antes de desconectar.
 * Aguarda um curto período para processar envios pendentes.
 */
void mqttFlushAndDisconnect() {
    unsigned long start = millis();
    // ESP32 PubSubClient não tem flush, mas garantir o envio: aguarde algum tempo
    while (mqttClient.connected() && millis() - start < 1000) {
        mqttClient.loop(); // processa envios
        delay(10);
    }
    mqttClient.disconnect();
    delay(100); // pequeno intervalo para liberar buffer do socket
}

// === FLUXO PRINCIPAL ===

/**
 * Função de setup do sistema. 
 * Responsável por inicializar sensores, RTC, conexões e configurar modes de wake up.
 */
void setup() {
    Serial.begin(115200); // Inicializa comunicação serial (debug)
    Wire.begin(I2C_SDA, I2C_SCL);

    int setupResults = 1;

    // Configura pino do trigger
    pinMode(TRIGGER_PIN, INPUT);

    // Inicializa RTC e sensores, conecta WiFi e MQTT
    setupResults *= setupRTC();
    setupResults *= ensureWiFi();
    setupResults *= ensureMQTT();

    logMsg("Device booting...", "BOOT_START");
    sendTelemetry();
    logMsg("Initializing sensors...", "SENS_INIT");
    setupResults *= setupSensors();

    if (setupResults != 1) {
        logMsg("Setup encountered errors", "BOOT_ERR");
        delay(3000);
        ESP.restart(); // Reinicia para tentar recuperar
    } else {
        logMsg("Setup completed successfully", "BOOT_OK");
    }

    // Configura acordes (external trigger e timer)
    esp_sleep_enable_ext0_wakeup((gpio_num_t)TRIGGER_PIN, 0);   // Wake LOW trigger
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_SEC * 1000000LL);  // Wake por timer (10min)

}

/**
 * Função principal do loop; gerencia trigger para coleta ou envio de telemetria e controla ciclos de sono leve.
 */
void loop()
{
    bool triggerLow = digitalRead(TRIGGER_PIN) == LOW;
    uint8_t batchCount = 0; // Reinicia batch ao acordar

    // Turn on as7341 led on maximum brightness
    // as7341.enableLED(true); // Liga LED interno do AS7341
    // as7341.setLEDCurrent(100); // Máxima corrente (100mA)

    // Turn on RGBW led on maximum brightness
    // rgbw.setBrightness(100); // Máxima intensidade (100%)
    // rgbw.show();


    uint32_t rgbw = led.Color(255, 255, 255, 255);
    led.fill(rgbw, 0, NUM_LEDS);
    led.show();

    if (triggerLow || bufferCount > 0)
    {
        // Coleta automática enquanto trigger está ativo (LOW)
        while (digitalRead(TRIGGER_PIN) == LOW && batchCount < BATCH_SIZE)
        {
            int8_t flag = batchCount == 0 ? 1 : 0;
            if (batchCount == BATCH_SIZE - 1)
                flag = -1;
            collectDatapoint("R", batchCount, flag);
            collectDatapoint("G", batchCount, flag);
            collectDatapoint("B", batchCount, flag);
            collectDatapoint("W", batchCount, flag);
            
            // led.clear();
            batchCount++;
            
            delay(400);
        }

        // Ao finalizar batch, garante conexão e envia dados + telemetria
        if (ensureWiFi() && ensureMQTT()) {
            sendBatchData(batchCount);
            sendTelemetry();
        } else {
            logMsg("WiFi/MQTT send failed", "SEND_FAIL");
        }
    }
    else
    {
        // Se acordou por timer, apenas envia telemetria
        if (ensureWiFi() && ensureMQTT()) {
            sendTelemetry();
            mqttClient.disconnect();
        } else {
            logMsg("WiFi/MQTT telemetry failed", "SEND_FAIL");
        }
    }

    logMsg("Going to sleep", "SLEEP");
    // as7341.enableLED(false); // Desliga LED interno do AS7341
    mqttFlushAndDisconnect();
    WiFi.disconnect(true); // Otimiza consumo
    led.clear(); // Apaga LED
    esp_light_sleep_start(); // Entra em modo de sono leve
}

// Todo:
// - Implementar QoS 1 MQTT (futuro)