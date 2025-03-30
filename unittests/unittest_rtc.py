import unittest
from src.rtc import RTC
from src.config_manager import ConfigManager

class TestRTC(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()
        self.rtc = RTC(self.config_manager)

    def test_sync_time(self):
        self.rtc.sync_time()  # This will sync the time from NTP or RTC
        # Verify system time update (You can check logs or system time manually)

    def test_get_rtc_temperature(self):
        temperature = self.rtc.get_rtc_temperature()
        self.assertIsInstance(temperature, float)

if __name__ == "__main__":
    unittest.main()
