import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import time

from src.rtc import RTC
from src.config_manager import ConfigManager

def rtc_demo():
    # Initialize ConfigManager and RTC
    config_manager = ConfigManager()
    rtc = RTC(config_manager)

    # Demonstrate the current RTC time
    print("Retrieving current RTC time...")
    rtc_time = rtc.retrieve_rtc_time()
    print(f"Current RTC time: {rtc_time}")

    # Synchronize the system time with NTP or RTC depending on network availability
    print("Synchronizing system time...")
    rtc.sync_time()

    # Get RTC temperature
    temperature = rtc.get_rtc_temperature()
    print(f"RTC Temperature: {temperature}°C")

    # Check network availability
    print("Checking network availability...")
    network_available = rtc.check_network()
    if network_available:
        print("Network is available.")
    else:
        print("Network is not available.")

if __name__ == "__main__":
    rtc_demo()
