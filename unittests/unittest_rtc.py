import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time
import subprocess
import ntpLIB

from src.rtc import RTC
from src.config_manager import ConfigManager

class TestRTC(unittest.TestCase):

    def setUp(self):
        # Mock ConfigManager to control configuration values
        self.config_manager = MagicMock(ConfigManager)
        self.config_manager.get.return_value = {
            "ntp_server": "pool.ntp.org",
            "timezone": "UTC"
        }

        # Create RTC instance
        self.rtc = RTC(self.config_manager)

    @patch('ntplib.NTPClient.request')
    @patch('subprocess.call')
    def test_synchronize_system_time(self, mock_subprocess, mock_ntp_request):
        # Mock NTP response
        mock_ntp_request.return_value.tx_time = 1617352976  # A fixed timestamp for testing
        mock_subprocess.return_value = None  # Mock successful subprocess call

        result = self.rtc.synchronize_system_time()
        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(['sudo', 'date', '-s', '2021-04-01 06:16:16'])
        self.assertEqual(self.rtc.rtc.datetime, time.localtime(1617352976))

    @patch('time.localtime')
    def test_update_rtc(self, mock_localtime):
        mock_localtime.return_value = time.struct_time((2021, 4, 1, 6, 16, 16, 3, 91, 0))  # Mock current system time
        self.rtc.update_rtc()
        self.assertEqual(self.rtc.rtc.datetime, mock_localtime.return_value)

    @patch('subprocess.check_output')
    def test_get_wifi_ssid_and_db(self, mock_check_output):
        # Mock successful Wi-Fi information retrieval
        mock_check_output.return_value = b'"MyWiFi"'
        mock_extract_signal_strength = MagicMock(return_value=-70)
        with patch.object(self.rtc, 'extract_signal_strength', mock_extract_signal_strength):
            wifi_info = self.rtc.get_wifi_ssid_and_db()
            self.assertEqual(wifi_info, ("MyWiFi", -70))

    @patch('subprocess.check_output', side_effect=Exception("Wi-Fi error"))
    def test_get_wifi_ssid_and_db_error(self, mock_check_output):
        wifi_info = self.rtc.get_wifi_ssid_and_db()
        self.assertIsNone(wifi_info)

    @patch('psutil.net_if_addrs')
    @patch('subprocess.check_call')
    def test_check_network(self, mock_check_call, mock_net_if_addrs):
        # Mock network available (successful ping)
        mock_check_call.return_value = None
        network_status = self.rtc.check_network()
        self.assertTrue(network_status)

        # Mock network unavailable (ping fails)
        mock_check_call.side_effect = subprocess.CalledProcessError(1, 'ping')
        network_status = self.rtc.check_network()
        self.assertFalse(network_status)

    @patch('subprocess.call')
    @patch('ntplib.NTPClient.request')
    def test_sync_time(self, mock_ntp_request, mock_subprocess):
        # Simulate network availability and successful NTP synchronization
        mock_ntp_request.return_value.tx_time = 1617352976
        mock_subprocess.return_value = None
        self.rtc.sync_time()

        # Check that the system time is synchronized
        mock_subprocess.assert_called_once_with(['sudo', 'date', '-s', '2021-04-01 06:16:16'])

    @patch('subprocess.call')
    @patch('ntplib.NTPClient.request')
    def test_sync_time_fallback(self, mock_ntp_request, mock_subprocess):
        # Simulate network failure, and fallback to RTC time
        mock_ntp_request.side_effect = ntplib.NTPException("NTP Error")
        mock_subprocess.return_value = None
        self.rtc.sync_time()

        # Check that the RTC time is used
        mock_subprocess.assert_called_once_with(['sudo', 'date', '-s', '2021-04-01 06:16:16'])

if __name__ == "__main__":
    unittest.main()
