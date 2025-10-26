# # nfc_reader.py

import time
import binascii
import threading
import random
from typing import Optional, Callable, Dict, Any

from src.logger import Logger
from src.database import Database
from src.config_manager import ConfigManager

CONFIG_SYSTEM = None

class MockPn532:
    PN532_MIFARE_ISO14443A_106KBPS = 0
    
    def __init__(self, i2c_bus):
        pass
    
    def begin(self):
        pass
    def getFirmwareVersion(self):
        # Return mocked version data
        return (0x32 << 24) | (0x01 << 16) | (0x05 << 8) | 0x00
    def SAMConfig(self):
        pass
    def readPassiveTargetID(self, mode):
        # Always return a fake UID for testing
        MOCK_UID =  '0123456789ABCDEF'
        uid_bytes = bytearray.fromhex(MOCK_UID)
        
        time.sleep(5)
        
        return True, uid_bytes

class MockPn532I2c:
    def __init__(self, bus):
        pass

try:
    # Get value for conditional import before class definition
    config_manager_test = ConfigManager("../config")
    CONFIG_SYSTEM = config_manager_test.get("conf").get("system")
except Exception:
    CONFIG_SYSTEM = None  # Allow import even if ConfigManager fails outside runtime

if CONFIG_SYSTEM == "WINDOWS":
    Pn532 = MockPn532
    Pn532I2c = MockPn532I2c
    pn532 = MockPn532("abc")  # For accessing the constant
else:
    from pn532pi import Pn532, pn532
    from pn532pi import Pn532I2c


class NFCReader:
    def __init__(self,
                 config_manager: ConfigManager,
                 database: Database,
                 i2c_bus: int = 1) -> None:
        self.config_manager = config_manager
        self.database = database
        self.logger = Logger()
        self._lock = threading.Lock()
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self.on_tag_detected: Optional[Callable[[Dict[str, Any]], None]] = None
        self._last_tag: Optional[Dict[str, Any]] = None
        self._found = threading.Event()

        # Inicialização via I2C
        self.i2c = Pn532I2c(i2c_bus)
        self.pn532 = Pn532(self.i2c)
        
        self.setup()

    def setup(self) -> None:
        self.pn532.begin()
        version_data = self.pn532.getFirmwareVersion()
        if not version_data:
            self.logger.println("PN531/PN532 não encontrado.", "ERROR")
            raise RuntimeError("Não foi possível inicializar o leitor NFC")
        chip_id = (version_data >> 24) & 0xFF
        ver_major = (version_data >> 16) & 0xFF
        ver_minor = (version_data >> 8) & 0xFF
        self.logger.println(
            f"Chip PN5 {chip_id:#x}, Firmware v{ver_major}.{ver_minor}", "DEBUG"
        )
        self.pn532.SAMConfig()
        self.logger.println("Leitor NFC pronto. Aguardando tags ISO14443A...", "INFO")

    # -------------------------------
    # Leitura customizada com timeout
    # -------------------------------
    def read_tag_continuous(self, timeout: float = 20.0, poll_interval: float = 1.0, callback: Optional[Callable]=None) -> Optional[Dict[str, Any]]:
        """
        Lê tags NFC em modo contínuo até timeout (segundos), retorna a primeira detectada ou None se nenhuma.
        Opcionalmente executa callback(tag) ao encontrar.
        """
        end_time = time.time() + timeout if timeout > 0 else None
        self.logger.println(f"Leitura NFC ativa por até {timeout} segundos...", "DEBUG")
        self._found.clear()
        self._last_tag = None
        while not self._found.is_set():
            tag = self.read_tag_once(timeout=poll_interval)
            if tag:
                self._last_tag = tag
                self._found.set()
                if callback:
                    callback(tag)
                elif self.on_tag_detected:
                    self.on_tag_detected(tag)
                return tag
            if end_time and time.time() >= end_time:
                break
        return None

    def start_continuous_threaded(self, callback: Optional[Callable]=None, poll_interval: float = 1.0):
        """
        Inicia leitura contínua EM THREAD, para uso no controller.
        Callback é chamado assim que qualquer tag for detectada.
        """
        if self.running:
            self.logger.println("Leitura contínua já em execução.", "WARNING")
            return
        self.logger.println(f"Iniciando leitura NFC em thread...", "DEBUG")
        self.running = True
        self._thread = threading.Thread(target=self._poll_tags_thread, args=(callback, poll_interval), daemon=True)
        self._thread.start()

    def _poll_tags_thread(self, callback, poll_interval):
        while self.running:
            tag = self.read_tag_once(timeout=1)
            if tag:
                if callback: callback(tag)
                elif self.on_tag_detected: self.on_tag_detected(tag)
                # Não pare a thread automaticamente: controller decide!
            time.sleep(poll_interval)

    def stop_continuous(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.logger.println("Leitura contínua NFC parada.", "INFO")

    # ------------- LEITURA ÚNICA JA EXISTENTE -------------
    def read_tag_once(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
        start = time.time()
        while time.time() - start < timeout:
            success, uid = self.pn532.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
            if success:
                uid_hex = binascii.hexlify(uid).decode("utf-8").upper()
                tag_info = {
                    "uid": uid_hex,
                    "length": len(uid),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.logger.println(f"Tag NFC detectada: {tag_info}", "INFO")
                return tag_info
        return None

























# import time
# import binascii
# import threading
# from typing import Optional, Callable, Dict, Any

# from pn532pi import Pn532, pn532
# from pn532pi import Pn532I2c

# from src.logger import Logger
# from src.database import Database
# from src.config_manager import ConfigManager


# class NFCReader:
#     """Classe para controle do módulo NFC PN531/PN532 no Raspberry Pi usando pn532pi.

#     Esta classe encapsula a comunicação com o PN531/PN532 via I2C, permitindo
#     inicializar o dispositivo, ler tags NFC (UID e tipo), operar em modo
#     de leitura única ou contínua e registrar eventos no banco SQLite.

#     Attributes:
#         config_manager (ConfigManager): Gerenciador de configuração.
#         database (Database): Instância de acesso ao banco SQLite.
#         logger (Logger): Instância do logger para registrar eventos.
#         pn532 (Pn532): Objeto de comunicação com o módulo NFC.
#         running (bool): Flag de controle para leitura contínua.
#         on_tag_detected (Optional[Callable]): Callback customizado para eventos de tag.
#     """

#     def __init__(self,
#                  config_manager: ConfigManager,
#                  database: Database,
#                  i2c_bus: int = 1) -> None:
#         """Inicializa o leitor NFC.

#         Args:
#             config_manager (ConfigManager): Gerenciador de parâmetros em YAML.
#             database (Database): Instância de acesso ao banco de dados SQLite.
#             i2c_bus (int, optional): Número do barramento I2C do Raspberry Pi. Default é 1.
#         """
#         self.config_manager = config_manager
#         self.database = database
#         self.logger = Logger()
#         self.running: bool = False
#         self._thread: Optional[threading.Thread] = None
#         self.on_tag_detected: Optional[Callable[[Dict[str, Any]], None]] = None

#         # Inicialização via I2C
#         self.i2c = Pn532I2c(i2c_bus)
#         self.pn532 = Pn532(self.i2c)
        
#         self.setup()

#     # ----------------------------------------------------------------
#     # Setup
#     # ----------------------------------------------------------------
#     def setup(self) -> None:
#         """Inicializa o PN531/PN532 e verifica firmware."""
#         self.pn532.begin()

#         version_data = self.pn532.getFirmwareVersion()
#         if not version_data:
#             self.logger.println("PN531/PN532 não encontrado.", "ERROR")
#             raise RuntimeError("Não foi possível inicializar o leitor NFC")

#         chip_id = (version_data >> 24) & 0xFF
#         ver_major = (version_data >> 16) & 0xFF
#         ver_minor = (version_data >> 8) & 0xFF
#         self.logger.println(
#             f"Chip PN5 {chip_id:#x}, Firmware v{ver_major}.{ver_minor}", "INFO"
#         )

#         # Configuração para leitura de tags ISO14443A
#         self.pn532.SAMConfig()
#         self.logger.println("Leitor NFC pronto. Aguardando tags ISO14443A...", "INFO")

#     # ----------------------------------------------------------------
#     # Leitura de tags
#     # ----------------------------------------------------------------
#     def read_tag_once(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
#         """Realiza uma leitura única de tag NFC.

#         Args:
#             timeout (int, optional): Tempo limite em segundos. Default = 2.

#         Returns:
#             Optional[Dict[str, Any]]: Informações da tag detectada ou None se nada encontrado.
#         """
#         start = time.time()
#         while time.time() - start < timeout:
#             success, uid = self.pn532.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
#             if success:
#                 uid_hex = binascii.hexlify(uid).decode("utf-8").upper()
#                 tag_info = {
#                     "uid": uid_hex,
#                     "length": len(uid),
#                     "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
#                 }

#                 self.logger.println(f"Tag NFC detectada: {tag_info}", "INFO")

#                 # Salvar log de evento no banco
#                 # self._save_event(tag_info)
                
#                 return tag_info

#         return None

#     def start_continuous_read(self, poll_interval: float = 1.0) -> None:
#         """Inicia leitura contínua em thread separada.

#         Args:
#             poll_interval (float, optional): Intervalo entre leituras em segundos.
#         """
#         if self.running:
#             self.logger.println("Leitura contínua já está em execução.", "WARNING")
#             return

#         self.running = True
#         self._thread = threading.Thread(target=self._poll_tags, args=(poll_interval,), daemon=True)
#         self._thread.start()
#         self.logger.println("Leitura contínua de tags NFC iniciada.", "INFO")

#     def stop_continuous_read(self) -> None:
#         """Interrompe a leitura contínua de tags NFC."""
#         self.running = False
#         if self._thread:
#             self._thread.join()
#         self.logger.println("Leitura contínua encerrada.", "INFO")

#     def _poll_tags(self, poll_interval: float) -> None:
#         """Loop interno para leitura contínua de tags."""
#         while self.running:
#             tag_info = self.read_tag_once(timeout=1)
#             if tag_info and self.on_tag_detected:
#                 self.on_tag_detected(tag_info)
#             time.sleep(poll_interval)

    # ----------------------------------------------------------------
    # Banco de dados
    # ----------------------------------------------------------------
    # def _save_event(self, tag_info: Dict[str, Any]) -> None:
    #     """Salva a leitura no banco de dados (logs).

    #     Args:
    #         tag_info (Dict[str, Any]): Informações da tag detectada.
    #     """
    #     try:
    #         data = {
    #             "device_id": self.database.get_device_id(),
    #             "timestamp": tag_info["timestamp"],
    #             "error_code": "NFC_TAG",
    #             "error_message": f"UID={tag_info['uid']} LEN={tag_info['length']}"
    #         }
    #         self.database.insert_data("insert_logs", "logs", data)
    #         self.logger.println("Leitura NFC registrada no banco.", "DEBUG")
    #     except Exception as e:
    #         self.logger.println(f"Erro ao salvar evento NFC: {e}", "ERROR")


# # ----------------------------------------------------------------
# # Exemplo de uso
# # ----------------------------------------------------------------
# if __name__ == "__main__":
#     config = ConfigManager("../config")
#     db = Database(config)
#     reader = NFCReader(config, db)

#     try:
#         reader.setup()

#         # Leitura única
#         tag = reader.read_tag_once()
#         print("Leitura única:", tag)

#         # Callback para leitura contínua
#         def handler(event):
#             print("Callback -> Tag detectada:", event)

#         reader.on_tag_detected = handler
#         reader.start_continuous_read()

#         while True:
#             time.sleep(1)

#     except KeyboardInterrupt:
#         reader.stop_continuous_read()
#         db.close()
