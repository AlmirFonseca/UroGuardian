import time
import subprocess
from typing import Optional
from datetime import datetime
import ntplib
import adafruit_ds3231
import board
import busio

from src.config_manager import ConfigManager

class RTC:
    """Class to interface with the DS3231 RTC module and handle time synchronization."""

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initializes the RTC interface with optional fallback for non-RPi environments."""

        # Load NTP server and timezone settings from the configuration file
        config = config_manager.get("conf")
        self.ntp_server = config.get("ntp_server", "pool.ntp.org")  # Default NTP server
        self.timezone = config.get("timezone", "UTC-3")  # Default timezone
        
        # Initialize I2C connection conditionally
        try:
            # Try using board.SCL and board.SDA (for Raspberry Pi)
            i2c = board.I2C()
            self.rtc = adafruit_ds3231.DS3231(i2c)
        except AttributeError:
            # If running in a non-RPi environment, create a mock or use default settings
            print("Board not detected, using default values for testing.")
            self.rtc = None  # Or initialize with a mock RTC class in testing

    def synchronize_system_time(self) -> bool:
        """Synchronizes the Raspberry Pi system time with an NTP server."""
        try:
            client = ntplib.NTPClient()
            response = client.request(self.ntp_server)
            ntp_time = datetime.utcfromtimestamp(response.tx_time)
            formatted_time = ntp_time.strftime('%Y-%m-%d %H:%M:%S')

            # Update the system time using 'date' command
            subprocess.call(['sudo', 'date', '-s', formatted_time])
            print(f"System time synchronized with NTP server: {self.ntp_server}")

            # Update the RTC with the system time if rtc object exists
            if self.rtc:
                self.update_rtc()
            return True
        except (ntplib.NTPException, subprocess.CalledProcessError) as e:
            print(f"Failed to synchronize system time with NTP: {e}")
            return False

    def update_rtc(self) -> None:
        """Updates the DS3231 RTC with the current system time."""
        if self.rtc:
            system_time = time.localtime()
            self.rtc.datetime = system_time
            print(f"RTC updated with system time: {time.strftime('%Y-%m-%d %H:%M:%S', system_time)}")

    def retrieve_rtc_time(self) -> datetime:
        """Retrieves the time from the DS3231 RTC and sets the system time."""
        if self.rtc:
            rtc_time = self.rtc.datetime
            print(f"System time set from RTC: {rtc_time}")
            return rtc_time
        else:
            print("RTC not initialized.")
            return datetime.now()

    def get_rtc_temperature(self) -> float:
        """Retrieves the temperature from the DS3231 temperature sensor."""
        if self.rtc:
            temperature = self.rtc.temperature
            print(f"RTC Temperature: {temperature}oC")
            return temperature
        else:
            print("RTC not initialized.")
            return 0.0

    def sync_time(self) -> None:
        """Synchronizes the system time with NTP or RTC depending on network availability."""
        network_available = self.check_network()
        
        if network_available:
            if not self.synchronize_system_time():
                print("Using RTC as fallback, system time synchronization failed.")
                self.retrieve_rtc_time()
        else:
            print("Network not available. Using RTC time.")
            rtc_time = self.retrieve_rtc_time()
            subprocess.call(['sudo', 'date', '-s', rtc_time.strftime('%Y-%m-%d %H:%M:%S')])

    def check_network(self) -> bool:
        """Checks if the network is available by pinging a known host."""
        try:
            subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
