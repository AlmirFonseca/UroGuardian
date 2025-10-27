import time
import threading
import schedule
from datetime import datetime

from typing import Dict, Any, List, Tuple, Optional

# # import os
# # import sys
# # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# # print(sys.path)

from src.config_manager import ConfigManager
from src.logger import Logger
from src.database import Database
from src.sample_handler import SampleHandler
from src.broker import Broker
from src.webpage import WebPage
from src.nfc_reader import NFCReader

class Controller:
    def __init__(self):
        self.logger = Logger()
        self.logger.println("Initializing Controller...", "INFO")
        
        # Initializing config and logger
        self.logger.println("Loading configuration...", "INFO")
        self.config = ConfigManager()
        
        # Define system state locked dict
        self.state = {"stage": "standby"}
        self.state_lock = threading.Lock()
        
        self.nfc_timeout = self.config.get("conf").get("nfc").get("nfc_timeout", 20)
        # self.nfc_lock = threading.Lock()
        # self.nfc_result = None
        
        
        # Initializing database and remote access
        self.logger.println("Initializing database...", "INFO")
        self.db = Database(self.config, web_interface=self.config.get("conf").get("sqlite_web_interface"))
        
        # Initializing web page
        self.logger.println("Initializing web page...", "INFO")
        self.webpage = WebPage(self.config, self.logger, self.db)
        
        # Initializing sample handler
        self.logger.println("Initializing sample handler...", "INFO")
        self.sample_handler = SampleHandler(self.db, self)
        
        # Initializing MQTT broker
        self.logger.println("Initializing MQTT broker...", "INFO")
        self.broker = Broker(self.config, self.db, self.sample_handler)
        
        # Initializing NFC Reader
        self.logger.println("Initializing NFC reader...", "INFO")
        self.nfc_reader = NFCReader(self.config, self.db)
        
        self.logger.println("Controller initialized successfully.", "INFO")

    def set_stage(self, stage: dict, extra: dict = None) -> None:
        """
        Atualiza a etapa global de forma thread-safe, e emite update via webpage.
        """
        self.logger.println(f"CONTROLLER Atualizando etapa para: {stage} com extras: {extra}", "INFO")
        with self.state_lock:
            self.logger.println(f"CONTROLLER LOCK Atualizando etapa para: {stage} com extras: {extra}", "INFO")
            self.state['stage'] = stage
            if extra:
                self.state.update(extra)
            # Dispara atualização de tela para todos os navegadores conectados
            self.webpage.update_stage(stage, extra)
            
        # Se a etapa for 'results', inicia leitura NFC contínua
        if stage.get("stage") == "results":    
            # Start continuous NFC reading in background
            self.logger.println("Iniciando leitura NFC contínua...", "INFO")
            self.nfc_reader.read_tag_continuous(
                timeout=self.nfc_timeout,
                poll_interval=1.0,
                callback=self._on_nfc_detected
            )

    def _on_nfc_detected(self, tag_info):
        
        self.logger.println(f"NFC tag detected: {tag_info}", "INFO")
        self.nfc_reader.stop_continuous()
        
        # Associe hash tag a um user_id (if not found, create a new user)
        user_id = self.db.get_user_id(tag_info['uid'])
        
        # Associate sample to the user_id
        self.sample_handler.associate_sample_to_user(user_id)
        
        # Update webpage to history stage with user_id
        self.set_stage({'stage': 'history'}, {'user_id': user_id})

    # def toggle_pause(self):
    #     self.is_paused = not self.is_paused
    #     state = "paused" if self.is_paused else "resumed"
    #     self.logger.println(f"Data collection has been {state}.", "INFO")

    # def start(self):
        
    #     # If the urine bag ID is not found, exit the program
    #     if not self.urine_bag_id:
    #         self.logger.println("Urine bag ID not found. Exiting...", "ERROR")
    #         return
        
    #     self.schedule_collection()
    #     self.monitor.start_monitoring()  # Monitoring in background
    #     self.logger.println("Press ENTER to pause/resume data collection", "INFO")
        
    #     while True:
    #         input()
    #         self.toggle_pause()
