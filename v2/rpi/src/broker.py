# broker.py

import json
import paho.mqtt.client as mqtt
import subprocess
import os
import signal
import time
import psutil
from typing import Callable, Optional, Dict, Any

from src.config_manager import ConfigManager
from src.database import Database
from src.logger import Logger
from src.sample_handler import SampleHandler


class Broker:
    """
    Classe responsável por gerenciar o cliente MQTT (Mosquitto) no Raspberry Pi.
    Permite inicializar o broker local, conectar, inscrever-se em tópicos, publicar mensagens
    e registrar eventos no banco de dados SQLite.
    
    Attributes:
        config_manager (ConfigManager): Instância do gerenciador de configuração.
        database (Database): Instância do gerenciador de banco de dados.
        client (mqtt.Client): Cliente MQTT.
        logger (Logger): Instância do logger para registrar eventos.
        broker_host (str): Endereço do broker MQTT.
        broker_port (int): Porta do broker MQTT.
        keepalive (int): Intervalo de keepalive em segundos.
        topics (Dict[str, int]): Tópicos para inscrição com seus respectivos QoS.
    """

    def __init__(self, config_manager: ConfigManager, database: Database, sample_handler: SampleHandler) -> None:
        """
        Inicializa a classe Broker com as configurações fornecidas.
        
        Args:
            config_manager (ConfigManager): Instância do gerenciador de configuração.
            database (Database): Instância do gerenciador de banco de dados.
        
        Returns:
            None
        """       
        self.config_manager = config_manager
        self.database = database
        self.logger = Logger()
        self.sample_handler = sample_handler

        # Configurações do MQTT carregadas via YAML
        mqtt_conf = self.config_manager.get("conf").get("mqtt")
        self.broker_host = mqtt_conf.get("host", "localhost")
        self.broker_port = mqtt_conf.get("port", 1883)
        self.keepalive = mqtt_conf.get("keepalive", 0)
        self.qos = mqtt_conf.get("qos", 1)
        self.topics = mqtt_conf.get("topics", {})

        # Cliente MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self._mosquitto_pid: Optional[int] = None
        
        # Inicia o broker local ao criar a instância
        self.start_broker()
        
        # Conecta ao broker
        self.connect()

    # -------------------------------
    # Mosquitto (Broker local)
    # -------------------------------
    def start_broker(self, num_retries: int = 3, timeout: int = 2) -> None:
        """
        Starts Mosquitto broker if not already running.
        """
        if self.is_mosquitto_running():
            self.logger.println("Mosquitto broker já está rodando.", "INFO")
            return

        # Continue with current logic if not running
        attempt = 0
        while attempt < num_retries:
            try:
                self.logger.println(f"Iniciando Mosquitto broker... (tentativa {attempt + 1})", "INFO")
                proc = subprocess.Popen(["mosquitto", "-v"])
                self._mosquitto_pid = proc.pid
                self.logger.println(f"Processo Mosquitto iniciado com PID={self._mosquitto_pid}", "DEBUG")
                time.sleep(timeout)
                if self.is_mosquitto_running():
                    self.logger.println(f"Broker MQTT iniciado (PID={self._mosquitto_pid})", "INFO")
                    return
                else:
                    raise Exception("Mosquitto não está rodando após inicialização.")
            except Exception as e:
                self.logger.println(f"Erro ao iniciar broker: {e}", "ERROR")
                attempt += 1
                time.sleep(timeout)

        # Se todas as tentativas falharem, tenta reiniciar o serviço Mosquitto
        try:
            self.logger.println("Tentando reiniciar o serviço Mosquitto...", "INFO")
            
            if self.config_manager.get("conf").get("system") == "LINUX":
                subprocess.run(["sudo", "systemctl", "restart", "mosquitto"], check=True)
            elif self.config_manager.get("conf").get("system") == "WINDOWS":
                subprocess.run(["sc", "stop", "mosquitto"], check=True)
                subprocess.run(["sc", "start", "mosquitto"], check=True)

            self.logger.println("Serviço Mosquitto reiniciado com sucesso.", "INFO")
        except Exception as e2:
            self.logger.println(f"Erro ao reiniciar o serviço Mosquitto: {e2}", "ERROR")
            
    def is_mosquitto_running(self) -> bool:
        """
        Checks if Mosquitto broker is already running (Windows: searches for 'mosquitto.exe').
        Returns True if found, False otherwise.
        """
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == "mosquitto.exe":
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    # def is_broker_running(self) -> bool:
    #     """
    #     Verifica se o broker Mosquitto local está em execução.
        
    #     Args:
    #         None
            
    #     Returns:
    #         bool: True se o broker estiver em execução, False caso contrário.
    #     """
    #     if self._mosquitto_pid:
    #         try:
    #             os.kill(self._mosquitto_pid, 0)
    #             return True
    #         except OSError:
    #             return False
    #     return False

    def stop_broker(self) -> None:
        """
        Para o broker Mosquitto local.
        
        Args:
            None
            
        Returns:
            None
        """
        if self._mosquitto_pid:
            os.kill(self._mosquitto_pid, signal.SIGTERM)
            self.logger.println("Broker MQTT parado.", "INFO")
            self._mosquitto_pid = None

    # -------------------------------
    # Cliente MQTT
    # -------------------------------
    def connect(self) -> None:
        """
        Conecta ao broker MQTT.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            Exception: Se ocorrer um erro ao conectar ao broker.
        """
        try:
            self.logger.println(f"Conectando ao broker {self.broker_host}:{self.broker_port}...", "INFO")
            self.client.connect(self.broker_host, self.broker_port, self.keepalive)
            self.client.loop_start()
            self.logger.println("Would now start MQTT connection (commented out for diagnostic)", "INFO")

        except Exception as e:
            self.logger.println(f"Erro ao conectar ao broker: {e}", "ERROR")

    def disconnect(self) -> None:
        """
        Desconecta do broker MQTT.

        Args:
            None

        Returns:
            None
        """
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.println("Cliente MQTT desconectado.", "INFO")

    def subscribe_topics(self) -> None:
        """
        Inscreve-se nos tópicos configurados.
        
        Args:
            None
            
        Returns:
            None
        
        """
        for topic in self.topics.keys():
            self.client.subscribe(topic, qos=self.qos if isinstance(self.qos, int) else 1)
            self.logger.println(f"Inscrito no tópico: {topic} (QoS={self.qos})", "INFO")

    def publish(self, topic: str, payload: Any, qos: int = 0) -> None:
        """
        Publica uma mensagem em um tópico.

        Args:
            topic (str): O tópico no qual publicar a mensagem.
            payload (Any): A carga da mensagem a ser publicada.
            qos (int, opcional): O nível de QoS (Quality of Service) para a mensagem. Padrão é 0.

        Returns:
            None
        """        
        self.logger.println(f"Publicando no tópico '{topic}': {payload}", "DEBUG")
        self.client.publish(topic, str(payload), qos=qos)
        
    def save_into_database(self, msg, payload) -> None:
        """
        Salva a mensagem recebida no banco de dados.

        Args:
            msg: A mensagem recebida.
            payload: O payload da mensagem.

        Returns:
            None
            
        Raises:
            Exception: Se ocorrer um erro ao salvar no banco de dados.
        """
        
        topic = msg.topic
        topic_fields = self.topics.get(topic, [])
        if not topic_fields:
            self.logger.println(f"Tópico '{topic}' não está mapeado para nenhuma tabela no banco de dados.", "WARNING")
            return

        try:
            data = json.loads(payload)
        except Exception as e:
            self.logger.println(f"Erro ao decodificar JSON: {payload} - {e}", "ERROR")
            return
        
        # Cheque se o payload corresponde ao mapping esperado
        missing = [field for field in topic_fields if field not in data]
        if missing:
            self.logger.println(f"Payload incompleto, faltando campos {missing} para o tópico '{topic}': {data}", "WARNING")
            return

        # Obter o device_id utilizando mac_address
        device_id = self.database.get_device_id(data.get("mac_address"))
        if not device_id:
            self.logger.println(f"Dispositivo com MAC '{data.get('mac_address')}' não encontrado no banco de dados.", "WARNING")
            return

        # Adicionar o device_id e remover o mac_address
        data["device_id"] = device_id
        data.pop("mac_address", None)

        # Nome da tabela esperado == parte final do tópico  
        try:
            if topic == "spectrum_datapoints": # Samples
                self.sample_handler.handle_datapoint(data)
            else: # Logs, Telemetry                
                self.database.insert_dict_into_table(topic, data, query_key="insert_" + topic)
        except Exception as e:
            self.logger.println(f"Erro ao inserir em '{topic}': {e}", "ERROR")
        else:            
            self.logger.println(f"Registro inserido em '{topic}': {data}", "DEBUG")

    # -------------------------------
    # Callbacks
    # -------------------------------
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """
        Callback chamado quando o cliente se conecta ao broker.

        Args:
            client: O cliente MQTT.
            userdata: Dados do usuário (não utilizado).
            flags: Flags de conexão.
            rc: Código de resultado da conexão.
        Returns:
            None
        """        
        if rc == 0:
            self.logger.println("Conectado ao broker MQTT com sucesso.", "INFO")
            self.subscribe_topics()
        else:
            self.logger.println(f"Falha na conexão ao broker. Código: {rc}", "ERROR")

    def _on_message(self, client, userdata, msg) -> None:
        """
        Callback chamado quando uma mensagem é recebida em um tópico inscrito.

        Args:
            client: O cliente MQTT.
            userdata: Dados do usuário (não utilizado).
            msg: A mensagem recebida.

        Returns:
            None
        """        
        payload_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        payload = msg.payload.decode("utf-8")
        self.logger.println(f"Mensagem recebida no tópico '{msg.topic}': {payload} ({payload_timestamp})", "INFO")
        
        self.save_into_database(msg, payload)

    def _on_disconnect(self, client, userdata, rc) -> None:
        """
        Callback chamado quando o cliente se desconecta do broker.
        
        Args:
            client: O cliente MQTT.
            userdata: Dados do usuário (não utilizado).
            rc: Código de resultado da desconexão.
            
        Returns:
            None
        """
        self.logger.println("Desconectado do broker MQTT.", "WARNING")


# # -------------------------------
# # Exemplo de uso
# # -------------------------------
# if __name__ == "__main__":
#     config = ConfigManager("../config")
#     db = Database(config)
#     broker = Broker(config, db)

#     broker.start_broker()    # inicia o mosquitto local
#     broker.connect()         # conecta o cliente MQTT
#     time.sleep(2)
#     broker.publish("test/topic", "Hello from Raspberry Pi!", qos=1)

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         broker.disconnect()
#         broker.stop_broker()
#         db.close()
