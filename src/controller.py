import time
import threading
import schedule
from datetime import datetime

from typing import Dict, Any, List, Tuple, Optional

from src.config_manager import ConfigManager
from src.logger import Logger
from src.database import Database
from src.rtc import RTC
from src.led import RGBLED, IRLED
from src.spectrum import SpectrumSensor
from src.monitoring import SystemMonitoring
from src.load_cell import LoadCell

class Controller:
    def __init__(self):
        
        # Initializing config and logger
        self.config = ConfigManager()
        self.logger = Logger()
        
        self.logger.println("Initializing Controller...", "INFO")
        
        # Initializing database
        self.db = Database(self.config)
        
        # Initializing system monitoring
        self.monitor = SystemMonitoring(self.db)
        
        # Initializing RTC
        self.rtc = RTC(self.config)
        self.rtc.sync_time()
        
        # Initializing LEDs and spectrum sensor
        self.rgb_led = RGBLED(self.config)
        self.rgb_led.turn_off()
        self.ir_led = IRLED(self.config)
        self.ir_led.turn_off()
        self.spectrum_sensor = SpectrumSensor(self.config)
        
        # Initializing load cell sensor
        self.load_cell_sensor = LoadCell(self.config, self.db)
        
        self.collect_interval = self.config.get("conf")["collect_interval"]
        self.brightness = self.config.get("conf")["brightness"]
        self.led_white_current = self.config.get("conf")["led_white_current"]
        self.oversampling = self.config.get("conf")["oversampling"]

        self.is_paused = False
        
        # Inicializar API Flask para consulta remota
        # self.api = DatabaseAPI(self.db)
        # self.logger.println("Starting Flask API server for database. Access at: http://0.0.0.0:5000/data/demo_table", "INFO")
        # self.api.run(host="0.0.0.0", port=5000)

        self.logger.println("Controller initialized successfully.", "INFO")
        
        self.device_id = None
        self.urine_bag_id = None
        
    def collect_spectrum_data(self, sample_id: int, batch_number: int):

        #################################################################
        # LED RGB Collection
        ##################################################################

        for color in ["R", "G", "B"]:
            self.logger.println(f"Turning on RGB LED: {color}", "DEBUG")
            self.rgb_led.set_color(color)
            time.sleep(1.0)

            readings = self.spectrum_sensor.read_all_channels()
            timestamp = datetime.now().isoformat()
            self.rgb_led.turn_off()
            self.logger.println(f"Color {color} readings at {timestamp}: {readings}", "DEBUG")
            
            # Insert data into the database
            spectrum_data_db_entry = {
                "sample_id": sample_id,
                "timestamp": timestamp,
                "batch": batch_number,
                "led_color": color,
                "led_intensity": self.brightness,
                "channel_415nm": readings.get("channel_415nm"),
                "channel_445nm": readings.get("channel_445nm"),
                "channel_480nm": readings.get("channel_480nm"),
                "channel_515nm": readings.get("channel_515nm"),
                "channel_555nm": readings.get("channel_555nm"),
                "channel_590nm": readings.get("channel_590nm"),
                "channel_630nm": readings.get("channel_630nm"),
                "channel_680nm": readings.get("channel_680nm"),
                "channel_clear": readings.get("channel_clear"),
                "channel_nir": readings.get("channel_nir")
            }
            
            self.db.insert_data("insert_spectrum_data", "spectrum_data", spectrum_data_db_entry)
            
            self.logger.println(f"RGB LED {color} readings collected and inserted into the database.", "DEBUG")
            
            self.logger.println(f"RGB LED {color} turned off", "DEBUG")
            
        ####################################################################
        # Internal White LED Collection
        ####################################################################

        self.logger.println("Turning on internal white LED of AS7341", "DEBUG")
        self.spectrum_sensor.set_led_current(self.led_white_current)
        self.spectrum_sensor.toggle_led(True)
        time.sleep(1.0)

        readings_white = self.spectrum_sensor.read_all_channels()
        timestamp_white = datetime.now().isoformat()
        self.spectrum_sensor.toggle_led(False)
        self.logger.println("Internal white LED turned off", "DEBUG")
        self.logger.println(f"White LED readings at {timestamp_white}: {readings_white}", "DEBUG")

        # Insert data into the database
        spectrum_data_db_entry = {
            "sample_id": sample_id,
            "timestamp": timestamp_white,
            "batch": batch_number,
            "led_color": "W",
            "led_intensity": self.led_white_current,
            "channel_415nm": readings_white.get("channel_415nm"),
            "channel_445nm": readings_white.get("channel_445nm"),
            "channel_480nm": readings_white.get("channel_480nm"),
            "channel_515nm": readings_white.get("channel_515nm"),
            "channel_555nm": readings_white.get("channel_555nm"),
            "channel_590nm": readings_white.get("channel_590nm"),
            "channel_630nm": readings_white.get("channel_630nm"),
            "channel_680nm": readings_white.get("channel_680nm"),
            "channel_clear": readings_white.get("channel_clear"),
            "channel_nir": readings_white.get("channel_nir")
        }
        
        self.db.insert_data("insert_spectrum_data", "spectrum_data", spectrum_data_db_entry)
        self.logger.println("Internal white LED readings collected and inserted into the database.", "DEBUG")
        
        ################################################################
        # IR LED Collection
        ################################################################
        
        self.logger.println("Turning on IR LED", "DEBUG")
        self.ir_led.turn_on()
        self.ir_led.set_brightness(self.brightness)
        time.sleep(1.0)
        
        readings_ir = self.spectrum_sensor.read_all_channels()
        timestamp_ir = datetime.now().isoformat()
        self.ir_led.turn_off()
        self.logger.println("IR LED turned off", "DEBUG")
        self.logger.println(f"IR LED readings at {timestamp_ir}: {readings_ir}", "DEBUG")
        
        # Insert data into the database
        spectrum_data_db_entry = {
            "sample_id": sample_id,
            "timestamp": timestamp_ir,
            "batch": batch_number,
            "led_color": "IR",
            "led_intensity": self.brightness,
            "channel_415nm": readings_ir.get("channel_415nm"),
            "channel_445nm": readings_ir.get("channel_445nm"),
            "channel_480nm": readings_ir.get("channel_480nm"),
            "channel_515nm": readings_ir.get("channel_515nm"),
            "channel_555nm": readings_ir.get("channel_555nm"),
            "channel_590nm": readings_ir.get("channel_590nm"),
            "channel_630nm": readings_ir.get("channel_630nm"),
            "channel_680nm": readings_ir.get("channel_680nm"),
            "channel_clear": readings_ir.get("channel_clear"),
            "channel_nir": readings_ir.get("channel_nir")
        }
        
        self.db.insert_data("insert_spectrum_data", "spectrum_data", spectrum_data_db_entry)
        self.logger.println("IR LED readings collected and inserted into the database.", "DEBUG")
        
        self.logger.println("Spectrum data collection completed.", "DEBUG")
        
    def collect_load_cell_data(self, sample_id: int, batch_number: int):
        """Collects data from the load cell sensor and inserts it into the database.
        
        Args:
            sample_id (int): The ID of the sample.
            batch_number (int): The batch number.
        """
        self.logger.println("Collecting data from load cell...", "DEBUG")
        
        weight = self.load_cell_sensor.read_weight()
        
        timestamp = datetime.now().isoformat()
        self.logger.println(f"Load cell readings at {timestamp}: {weight} grams", "DEBUG")
        
        # Insert data into the database
        load_cell_data_db_entry = {
            "sample_id": sample_id,
            "timestamp": timestamp,
            "batch": batch_number,
            "weight": weight,
            "tare_offset": self.load_cell_sensor.tare_offset,
            "calibration_factor": self.load_cell_sensor.calibration_factor
        }
        
        self.db.insert_data("insert_load_cell_data", "load_cell_data", load_cell_data_db_entry)
        self.logger.println("Load cell data collected and inserted into the database.", "DEBUG")

    def collect_batch(self, sample_id: int, batch_number: int):
        """"Collects data for a single batch.
        
        Args:
            sample_id (int): The ID of the sample.
            batch_number (int): The batch number.
        """
        self.collect_spectrum_data(sample_id, batch_number)
        # self.collect_load_cell_data(sample_id, batch_number)

    def collect_routine(self):
        """
        Executes the complete collection routine for urine samples, including multiple batches.
        This method performs the following steps:
        1. Logs the start of the collection routine.
        2. Inserts a new entry into the 'samples' table and retrieves the sample ID.
        3. Iterates through the specified number of batches (`self.oversampling`) and collects data for each batch.
        4. Logs the completion of the collection routine and its duration.
        5. Updates the 'samples' table entry with the end timestamp.
        6. Logs the completion of the data collection process.
        """
        
        self.logger.println(f"Starting complete collection routine ({self.oversampling} batches)", "INFO")
        
        start_collection_time = datetime.now()
        
        # Insert entry on 'samples' table and get sample ID
        self.db.insert_data("insert_sample", "samples", {
            "urine_bag_id": self.urine_bag_id,
            "start_timestamp": datetime.now().isoformat(),
            "end_timestamp": None,
        })
        sample_id = self.db.get_last_inserted_id("samples")

        for batch_number in range(self.oversampling):
            self.logger.print_separator("DEBUG", sep_type=".")
            self.logger.println(f"Starting batch {batch_number + 1}/{self.oversampling}", "INFO")
            
            self.collect_batch(sample_id, batch_number + 1)

        end_collection_time = datetime.now()
        duration = (end_collection_time - start_collection_time).total_seconds()
        self.logger.println(f"Collection completed in {duration:.2f} seconds", "INFO")

        # Update the sample entry with end timestamp
        self.db.update_data("update_sample", "samples", {"end_timestamp": end_collection_time.isoformat()}, condition=f"id = {sample_id}")
        self.logger.println(f"Sample entry updated with end timestamp: {end_collection_time.isoformat()}", "INFO")

        self.logger.println("Collection data completed", "INFO")
        self.logger.print_separator("DEBUG")

    def schedule_collection(self):
        self.logger.println(f"Scheduling data collection every {self.collect_interval} seconds.", "INFO")
        schedule.every(self.collect_interval).seconds.do(self.collect_routine)

        def run_scheduler():
            while True:
                if not self.is_paused:
                    schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=run_scheduler, daemon=True).start()
        self.logger.println("Scheduler thread started successfully.", "INFO")

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        state = "paused" if self.is_paused else "resumed"
        self.logger.println(f"Data collection has been {state}.", "INFO")
        
    def sync_urine_bag_info(self, force_update: bool = True) -> bool:
        """Synchronizes the urine bag information with the database.
        
        This method retrieves the device ID and urine bag ID from the database.
        If the device ID is not found, it prompts the user to register the device first.
        If the urine bag ID is not found, it prompts the user to register the urine bag first.
        
        Returns:
            bool: True if synchronization is successful, False otherwise.
        """
    
        self.logger.println("Identifying and registering the device...", "INFO")
        
        # Get device ID from the database
        self.device_id = self.db.get_device_id()
        if not self.device_id:
            self.logger.println("No device ID found. Please register the device first.", "ERROR")
            return False
        
        # Get related urine bag ID from the database
        self.urine_bag_id = self.db.get_urine_bag_id(self.device_id, force_update)
        if not self.urine_bag_id:
            self.logger.println("No urine bag ID found. Please register the urine bag first.", "ERROR")
            return False
        
        return True

    def start(self):
        self.sync_urine_bag_info()
        
        # If the urine bag ID is not found, exit the program
        if not self.urine_bag_id:
            self.logger.println("Urine bag ID not found. Exiting...", "ERROR")
            return
        
        self.schedule_collection()
        self.monitor.start_monitoring()  # Monitoring in background
        self.logger.println("Press ENTER to pause/resume data collection", "INFO")
        
        while True:
            input()
            self.toggle_pause()
