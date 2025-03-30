import psutil
import time
import schedule
from datetime import datetime
from typing import Optional
from typing import Tuple
import subprocess

from src.database import Database


class SystemMonitoring:
    """Class to monitor system resources (CPU, RAM, Power, Network, etc.) on Raspberry Pi Zero 2.

    The class gathers system data and stores it into the database at a specified time interval.

    Attributes:
        db (Database): Instance of the Database class to store the data.
        time_interval (int): The interval (in seconds) between data collection.
    """
    
    def __init__(self, db: Database, time_interval: int = 60) -> None:
        """Initializes the SystemMonitoring class.

        Args:
            db (Database): The Database instance to store the monitoring data.
            time_interval (int, optional): The interval in seconds between data collection (default is 60 seconds).
        """
        self.db = db
        self.time_interval = time_interval

    def get_cpu_usage(self) -> float:
        """Get the current CPU usage as a percentage.
        
        Returns:
            float: The current CPU usage in percentage.
        """
        return psutil.cpu_percent(interval=1)

    def get_ram_usage(self) -> float:
        """Get the current RAM usage as a percentage.
        
        Returns:
            float: The current RAM usage in percentage.
        """
        memory = psutil.virtual_memory()
        return memory.percent

    def get_power_usage(self) -> Optional[float]:
        """Get the current power consumption. This would depend on your setup.
        
        Placeholder method for power consumption. You could use external hardware to measure power.
        Returns `None` if not available.
        """
        # Placeholder for actual power measurement
        return None

    def get_disk_usage(self) -> float:
        """Get the current disk usage as a percentage.
        
        Returns:
            float: The current disk usage in percentage.
        """
        disk = psutil.disk_usage('/')
        return disk.percent

    def get_network_usage(self) -> float:
        """Get the current network usage as a percentage.
        
        Returns:
            float: The current network usage in MB/s.
        """        
        # Here we just measure the current sent/received bytes on the network interface
        network = psutil.net_io_counters()
        # Calculate the total amount of data transferred in the last second
        return (network.bytes_sent + network.bytes_recv) / 1024 / 1024  # MB

    def get_wifi_ssid_and_db(self) -> Optional[Tuple[str, float]]:
        """Get the SSID and signal strength (dB) if connected to Wi-Fi.

        Returns:
            tuple: A tuple containing SSID and the signal strength in dB (e.g., ('SSID', -70)).
        
        Raises:
            subprocess.CalledProcessError: If the command to get Wi-Fi details fails.
        """
        try:
            # Get the Wi-Fi interface (assuming wlan0 here)
            wifi_data = psutil.net_if_addrs().get('wlan0', None)
            if wifi_data:
                # Changed iwgetid to a simpler command without --pretty
                ssid = subprocess.check_output(["iwgetid", "wlan0", "-r"]).decode().strip()
                
                signal_strength = subprocess.check_output(["iwconfig", "wlan0"]).decode()
                signal_strength_db = self.extract_signal_strength(signal_strength)
                
                return ssid, signal_strength_db
            return None
        except Exception as e:
            print(f"Error fetching Wi-Fi details: {e}")
            return None

    def collect_and_store_data(self) -> None:
        """Collect system data and store it in the database.
        
        Raises:
            ValueError: If there is an error inserting data into the database.
        """
        
        # Collect current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Collect system usage data
        cpu_usage = self.get_cpu_usage()
        ram_usage = self.get_ram_usage()
        power_usage = self.get_power_usage()
        disk_usage = self.get_disk_usage()
        network_usage = self.get_network_usage()

        # Get Wi-Fi information (SSID and signal strength)
        wifi_info = self.get_wifi_ssid_and_db()
        ssid, signal_strength_db = wifi_info if wifi_info else ("N/A", None)
        
        # Prepare data dictionary to insert into the database
        data = {
            "timestamp": timestamp,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "power_usage": power_usage,
            "disk_usage": disk_usage,
            "network_usage": network_usage,
            "wifi_ssid": ssid,
            "wifi_signal_strength": signal_strength_db
        }
        
        # Insert data into the 'system_monitoring' table using query key
        try:
            self.db.insert_data("insert_data_system_monitoring", "system_monitoring", data)
            print(f"Data collected and stored at {timestamp}")
        except ValueError as e:
            print(f"Error inserting data: {e}")

    def start_monitoring(self) -> None:
        """Start the monitoring process with the given time interval, using a scheduling library."""
        # Schedule the task to run at specified intervals
        schedule.every(self.time_interval).seconds.do(self.collect_and_store_data)

        print(f"Monitoring started with {self.time_interval}-second interval.")
        
        # Run the scheduled tasks in a non-blocking way
        while True:
            schedule.run_pending()
            time.sleep(1)  # Avoid CPU overuse

# # Example Usage
# if __name__ == "__main__":
#     # Initialize the Database
#     from database import Database  # Import the Database module
#     config_manager = ConfigManager()
#     db = Database(config_manager)
    
#     # Initialize the SystemMonitoring with a 60-second interval
#     monitoring = SystemMonitoring(db, time_interval=60)
    
#     # Start monitoring the system
#     monitoring.start_monitoring()
