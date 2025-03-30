import os
import time
import subprocess
from typing import Optional
from datetime import datetime
from ds3231 import DS3231
import ntplib
from config_manager import ConfigManager

class RTC:
    """Class to interface with the DS3231 RTC module and handle time synchronization.

    This class updates the Raspberry Pi system time from an NTP server, sets the RTC time,
    and retrieves the time and temperature from the DS3231 RTC module.

    Attributes:
        rtc (DS3231): The DS3231 object to interface with the RTC.
        ntp_server (str): NTP server to synchronize the system time with.
        timezone (str): Timezone to set for the system.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initializes the RTC interface.

        Args:
            config_manager (ConfigManager): The ConfigManager instance to load configuration values.
        
        Returns:
            None
        """
        # Load NTP server and timezone settings from the configuration file
        config = config_manager.get("conf")
        self.ntp_server = config.get("ntp_server", "pool.ntp.org")  # Default NTP server
        self.timezone = config.get("timezone", "UTC")  # Default timezone
        
        # Initialize the DS3231 RTC object
        self.rtc = DS3231()

    def synchronize_system_time(self) -> bool:
        """Synchronizes the Raspberry Pi system time with an NTP server.

        If successful, updates the RTC time as well.

        Returns:
            bool: True if the system time was successfully synchronized with NTP, False otherwise.
            
        Raises:
            ntplib.NTPException: If there is an error communicating with the NTP server.
            subprocess.CalledProcessError: If there is an error executing the date command.
        """
        try:
            client = ntplib.NTPClient()
            response = client.request(self.ntp_server)
            ntp_time = datetime.utcfromtimestamp(response.tx_time)
            formatted_time = ntp_time.strftime('%Y-%m-%d %H:%M:%S')

            # Update the system time using 'date' command
            subprocess.call(['sudo', 'date', '-s', formatted_time])
            print(f"System time synchronized with NTP server: {self.ntp_server}")

            # Update the RTC with the system time
            self.update_rtc()
            return True
        except (ntplib.NTPException, subprocess.CalledProcessError) as e:
            print(f"Failed to synchronize system time with NTP: {e}")
            return False

    def update_rtc(self) -> None:
        """Updates the DS3231 RTC with the current system time.

        Returns:
            None
        """
        system_time = time.localtime()
        self.rtc.datetime = system_time
        print(f"RTC updated with system time: {time.strftime('%Y-%m-%d %H:%M:%S', system_time)}")

    def retrieve_rtc_time(self) -> datetime:
        """Retrieves the time from the DS3231 RTC and sets the system time.

        Returns:
            datetime: The current time read from the DS3231 RTC.
        """
        rtc_time = self.rtc.datetime
        print(f"System time set from RTC: {rtc_time}")
        return rtc_time

    def get_rtc_temperature(self) -> float:
        """Retrieves the temperature from the DS3231 temperature sensor.

        Returns:
            float: The current temperature in Celsius.
        """
        temperature = self.rtc.temperature
        print(f"RTC Temperature: {temperature}°C")
        return temperature

    def sync_time(self) -> None:
        """Synchronizes the system time with NTP or RTC depending on network availability.

        If the network is available, it attempts to sync with the NTP server. If not, it retrieves the time from the RTC.

        Returns:
            None
        """
        # Check if network is available by pinging a known address
        network_available = self.check_network()
        
        if network_available:
            # Synchronize system time with NTP and update RTC
            if not self.synchronize_system_time():
                print("Using RTC as fallback, system time synchronization failed.")
                self.retrieve_rtc_time()
        else:
            # Network not available, retrieve time from RTC and set system time
            print("Network not available. Using RTC time.")
            rtc_time = self.retrieve_rtc_time()
            # Update system time from RTC (this is specific to Raspberry Pi, as it has to be set manually)
            subprocess.call(['sudo', 'date', '-s', rtc_time.strftime('%Y-%m-%d %H:%M:%S')])

    def check_network(self) -> bool:
        """Checks if the network is available by pinging a known host.

        Returns:
            bool: True if the network is available, False otherwise.
            
        Raises:
            subprocess.CalledProcessError: If the ping command fails.
        """
        try:
            # Ping Google DNS to check if the network is available
            subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False


# # Example Usage
# if __name__ == "__main__":
#     # Initialize the ConfigManager to read pins from config/pins.yaml
#     from config_manager import ConfigManager
#     config_manager = ConfigManager()

#     # Initialize the Database
#     from database import Database  # Import the Database module
#     db = Database(config_manager)

#     # Initialize RTC module
#     rtc_module = RTC(config_manager)

#     # Synchronize system time with RTC or NTP
#     rtc_module.sync_time()

#     # Get RTC temperature
#     temperature = rtc_module.get_rtc_temperature()
#     print(f"RTC temperature: {temperature}°C")
