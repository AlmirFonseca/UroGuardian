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

class Controller:
    def __init__(self):
        
        self.logger = Logger()
        self.logger.println("Initializing Controller...", "INFO")
        
        # Initializing config and logger
        self.logger.println("Loading configuration...", "INFO")
        self.config = ConfigManager()
        
        # Initializing database and remote access
        self.logger.println("Initializing database...", "INFO")
        self.db = Database(self.config)
        
        # Initializing sample handler
        self.logger.println("Initializing sample handler...", "INFO")
        self.sample_handler = SampleHandler(self.db)
        
        # Initializing MQTT broker
        self.logger.println("Initializing MQTT broker...", "INFO")
        self.broker = Broker(self.config, self.db, self.sample_handler)
        
        # Initializing system monitoring
        # self.monitor = SystemMonitoring(self.db)
        
        # Initializing RTC
        # self.rtc = RTC(self.config)
        # self.rtc.sync_time()
        
        self.lock = threading.Lock()
        
        self.logger.println("Controller initialized successfully.", "INFO")

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
