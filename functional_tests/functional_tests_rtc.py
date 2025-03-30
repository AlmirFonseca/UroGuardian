from src.rtc import RTC
from src.config_manager import ConfigManager

rtc = RTC(ConfigManager())

# Synchronize time and print temperature
rtc.sync_time()
temperature = rtc.get_rtc_temperature()
print(f"RTC Temperature: {temperature}°C")
