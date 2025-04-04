import time
import threading
import schedule
from datetime import datetime
from src.config_manager import ConfigManager
from src.logger import Logger
from src.database import Database, DatabaseAPI
from src.rtc import RTC
from src.led import RGBLED
from src.spectrum import SpectrumSensor
from src.monitoring import SystemMonitoring

class Controller:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.logger.println("Initializing Controller...", "INFO")

        self.db = Database(self.config)
        self.rtc = RTC(self.config)
        self.rtc.sync_time()

        self.rgb_led = RGBLED(self.config)
        self.sensor = SpectrumSensor(self.config)
        self.monitor = SystemMonitoring(self.db)
        
        self.collect_interval = self.config.get("conf")["collect_interval"]
        self.brightness = self.config.get("conf")["brightness"]
        self.led_white_current = self.config.get("conf")["led_white_current"]

        self.is_paused = False
        
        # Inicializar API Flask para consulta remota
        self.api = DatabaseAPI(self.db)
        self.logger.println("Starting Flask API server for database. Access at: http://0.0.0.0:5000/data/demo_table", "INFO")
        # self.api.run(host="0.0.0.0", port=5000)

        self.logger.println("Controller initialized successfully.", "INFO")

    def collect_batch(self):
        self.logger.print_separator("DEBUG")
        self.logger.println(f"Starting a new batch collection at {datetime.now()}", "INFO")
        collected_data = []

        colors = [("R", (self.brightness, 0, 0)),
                  ("G", (0, self.brightness, 0)),
                  ("B", (0, 0, self.brightness))]

        for color_name, (r, g, b) in colors:
            self.logger.println(f"Turning on RGB LED: {color_name}", "DEBUG")
            self.rgb_led.set_color(r, g, b)
            time.sleep(1.0)

            readings = self.sensor.read_all_channels()
            timestamp = datetime.now().isoformat()
            self.logger.println(f"{color_name} readings at {timestamp}: {readings}", "DEBUG")
            
            collected_data.append({
                "timestamp": timestamp,
                "led_color": color_name,
                "led_intensity": self.brightness,
                "readings": readings
            })
            self.rgb_led.turn_off()
            self.logger.println(f"RGB LED {color_name} turned off", "DEBUG")

        self.logger.println("Turning on internal white LED of AS7341", "DEBUG")
        self.sensor.set_led_current(self.led_white_current)
        self.sensor.toggle_led(True)
        time.sleep(1.0)

        readings_white = self.sensor.read_all_channels()
        timestamp_white = datetime.now().isoformat()
        self.logger.println(f"White LED readings at {timestamp_white}: {readings_white}", "DEBUG")

        collected_data.append({
            "timestamp": timestamp_white,
            "led_color": "W",
            "led_intensity": self.led_white_current,
            "readings": readings_white
        })

        self.sensor.toggle_led(False)
        self.logger.println("Internal white LED turned off", "DEBUG")

        return collected_data

    def collect_routine(self):
        self.logger.println("Starting complete collection routine (3 batches)", "INFO")
        start_time = datetime.now()
        all_batches_data = []

        for batch_number in range(3):
            self.logger.println(f"Starting batch {batch_number + 1}/3", "INFO")
            batch_data = self.collect_batch()
            all_batches_data.extend(batch_data)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        self.logger.println(f"Collection completed in {duration:.2f} seconds", "INFO")

        # Save data to database
        for data in all_batches_data:
            db_entry = {
                "timestamp": data["timestamp"],
                "led_color": data["led_color"],
                "led_intensity": data["led_intensity"],
                "channel_readings": ','.join(str(v) for v in data["readings"])
            }
            self.db.insert_data("insert_spectrum_readings", "spectrum_readings", db_entry)

        self.logger.println("All batch data successfully saved to database", "INFO")
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

    def start(self):
        self.schedule_collection()
        self.monitor.start_monitoring()  # Monitoring in background
        self.logger.println("Press ENTER to pause/resume data collection", "INFO")
        
        while True:
            input()
            self.toggle_pause()
