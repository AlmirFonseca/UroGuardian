from src.config_manager import ConfigManager

config_manager = ConfigManager()

# Get and print NTP server and timezone from the configuration
conf = config_manager.get("conf")
print(f"NTP Server: {conf['ntp_server']}")
print(f"Timezone: {conf['timezone']}")
