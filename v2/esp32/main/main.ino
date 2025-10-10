// Board: ESP32 D1 Mini

// Sensors:
// - AS7341 (I2C, 0x39)
// - DS3231 (I2C, 0x68)
// - Moisture Sensor (Digital, IO5)
// - SK6812 (Digital, IO23), 2 leds, RGBW

// Goals:
// - On boot:
//   - Initialize the I2C bus
//   - Initialize the AS7341 sensor
//   - Initialize the DS3231 RTC
//   - Initialize the LED strip, turned off
//   - Set IO5 as input for the moisture sensor and wake up interrupt mode on HIGH signal
// - In the loop:
//   - Flash de led red, green, blue, white, off, each color for 500ms
//   - For each flash, read the AS7341 sensor and print the colors and values to the Serial Monitor
//   - Print the current date and time from the DS3231 to the Serial Monitor
//   - Enter deep sleep mode waiting for the moisture sensor to trigger an interrupt

#include <Wire.h>
#include <Adafruit_AS7341.h>
// #include <RTClib.h>
#include <Adafruit_NeoPixel.h>
#include "esp_sleep.h"

// ---- DEFINES ----
#define MOISTURE_SENSOR_PIN 34
#define LED_PIN 23
#define NUM_LEDS 2

// ---- OBJETOS ----
Adafruit_AS7341 as7341;
// RTC_DS3231 rtc;
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_RGBW + NEO_KHZ800);

// ---- FUNÇÕES ----
void flashColor(uint32_t color)
{
    strip.fill(color, 0, NUM_LEDS);
    strip.show();
    delay(200);
    strip.clear();
    strip.show();
}

// ---- INTERRUPÇÃO DE WAKE-UP ----
void setupWakeup()
{
    pinMode(MOISTURE_SENSOR_PIN, INPUT);
    esp_sleep_enable_ext0_wakeup((gpio_num_t)MOISTURE_SENSOR_PIN, 0); // Wake on LOW
}

void printAS7341Data()
{
    if (!as7341.readAllChannels())
    {
        Serial.println("Erro ao ler AS7341");
        return;
    }
    // Serial.print("AS7341 - F1: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_415nm_F1));
    // Serial.print(" F2: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_445nm_F2));
    // Serial.print(" F3: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_480nm_F3));
    // Serial.print(" F4: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_515nm_F4));
    // Serial.print(" F5: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_555nm_F5));
    // Serial.print(" F6: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_590nm_F6));
    // Serial.print(" F7: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_630nm_F7));
    // Serial.print(" F8: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_680nm_F8));

    // Serial.print(" Clear: ");
    // Serial.print(as7341.getChannel(AS7341_CHANNEL_CLEAR));

    // Serial.print(" NIR: ");
    // Serial.println(as7341.getChannel(AS7341_CHANNEL_NIR));

    // Serial.println();
}

// void printDateTime()
// {
//     DateTime now = rtc.now();
//     Serial.print("Data/Hora DS3231: ");
//     Serial.print(now.year(), DEC);
//     Serial.print('/');
//     Serial.print(now.month(), DEC);
//     Serial.print('/');
//     Serial.print(now.day(), DEC);
//     Serial.print(' ');
//     Serial.print(now.hour(), DEC);
//     Serial.print(':');
//     Serial.print(now.minute(), DEC);
//     Serial.print(':');
//     Serial.println(now.second(), DEC);
// }

void setup()
{
    Serial.begin(115200);
    delay(2000);

    // I2C Bus
    Wire.begin();

    // AS7341
    if (!as7341.begin())
    {
        Serial.println("AS7341 não encontrado!");
        while (1)
            delay(10);
    }
    else
    {
        Serial.println("AS7341 iniciado.");
    }

    // // DS3231
    // if (!rtc.begin())
    // {
    //     Serial.println("DS3231 não encontrado.");
    //     while (1)
    //         delay(10);
    // }
    // if (rtc.lostPower())
    // {
    //     rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    //     Serial.println("DS3231 ajustado para hora do compilador.");
    // }

    // SK6812 LEDs
    strip.begin();
    strip.show(); // Apaga todos

    // Moisture Sensor como wake-up
    setupWakeup();
}

void loop()
{
    // Sequência de flashes
    Serial.println("R");
    flashColor(strip.Color(255, 0, 0, 0));
    printAS7341Data();
    // printDateTime();

    Serial.println("G");
    flashColor(strip.Color(0, 255, 0, 0));
    printAS7341Data();
    // printDateTime();

    Serial.println("B");
    flashColor(strip.Color(0, 0, 255, 0));
    printAS7341Data();
    // printDateTime();

    Serial.println("W");
    flashColor(strip.Color(0, 0, 0, 255));
    printAS7341Data();
    // printDateTime();

    Serial.println("OFF");
    strip.clear();
    strip.show();
    printAS7341Data();
    // printDateTime();

    Serial.println("Sleep");
    // delay(100);
    // esp_deep_sleep_start();
    esp_light_sleep_start();
}
