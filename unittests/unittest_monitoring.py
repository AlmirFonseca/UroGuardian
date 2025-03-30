import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.monitoring import SystemMonitoring
from src.database import Database

class TestSystemMonitoring(unittest.TestCase):

    def setUp(self):
        # Mock ConfigManager and Database initialization
        self.db = MagicMock(Database)
        self.monitoring = SystemMonitoring(self.db, time_interval=1)  # Interval of 1 second for quick tests

    def test_get_cpu_usage(self):
        # Mock psutil.cpu_percent
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 25.5
            cpu_usage = self.monitoring.get_cpu_usage()
            self.assertEqual(cpu_usage, 25.5)

    def test_get_ram_usage(self):
        # Mock psutil.virtual_memory
        with patch('psutil.virtual_memory') as mock_virtual_memory:
            mock_virtual_memory.return_value.percent = 45.0
            ram_usage = self.monitoring.get_ram_usage()
            self.assertEqual(ram_usage, 45.0)

    def test_get_disk_usage(self):
        # Mock psutil.disk_usage
        with patch('psutil.disk_usage') as mock_disk_usage:
            mock_disk_usage.return_value.percent = 60.0
            disk_usage = self.monitoring.get_disk_usage()
            self.assertEqual(disk_usage, 60.0)

    def test_get_network_usage(self):
        # Mock psutil.net_io_counters
        with patch('psutil.net_io_counters') as mock_net_io_counters:
            mock_net_io_counters.return_value.bytes_sent = 1000000
            mock_net_io_counters.return_value.bytes_recv = 2000000
            network_usage = self.monitoring.get_network_usage()
            self.assertEqual(network_usage, 3.0)  # MB

    def test_get_wifi_ssid_and_db(self):
        # Mock subprocess.check_output for SSID and signal strength
        with patch('subprocess.check_output') as mock_check_output:
            mock_check_output.return_value = b'"MyWiFi"'
            signal_strength_mock = "Signal level=-70 dBm"
            with patch.object(self.monitoring, 'extract_signal_strength', return_value=-70):
                wifi_info = self.monitoring.get_wifi_ssid_and_db()
                self.assertEqual(wifi_info, ("MyWiFi", -70))

    def test_collect_and_store_data(self):
        # Mock the actual insert_data method of Database to prevent database interaction
        with patch.object(self.db, 'insert_data') as mock_insert_data:
            data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_usage": 25.5,
                "ram_usage": 45.0,
                "power_usage": None,
                "disk_usage": 60.0,
                "network_usage": 3.0,
                "wifi_ssid": "MyWiFi",
                "wifi_signal_strength": -70
            }
            self.monitoring.collect_and_store_data()
            mock_insert_data.assert_called_once_with("insert_data_system_monitoring", "system_monitoring", data)

    @patch('psutil.cpu_percent', return_value=25.5)
    @patch('psutil.virtual_memory', return_value=MagicMock(percent=45.0))
    @patch('psutil.disk_usage', return_value=MagicMock(percent=60.0))
    @patch('psutil.net_io_counters', return_value=MagicMock(bytes_sent=1000000, bytes_recv=2000000))
    @patch('subprocess.check_output', return_value=b'"MyWiFi"')
    def test_start_monitoring(self, mock_ssid, mock_net_io, mock_disk, mock_ram, mock_cpu):
        # Test that start_monitoring calls the method to collect and store data
        with patch.object(self.monitoring, 'collect_and_store_data') as mock_collect:
            self.monitoring.start_monitoring()
            time.sleep(2)  # Allow the monitoring to run for a while (with 1-second interval)
            mock_collect.assert_called()

if __name__ == "__main__":
    unittest.main()
