import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from src.monitoring import SystemMonitoring
from src.database import Database
from src.config_manager import ConfigManager

class TestMonitoring(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()
        self.db = Database(self.config_manager)
        self.monitoring = SystemMonitoring(self.db)

    def test_collect_and_store_data(self):
        self.monitoring.collect_and_store_data()
        data = self.db.fetch_all("fetch_data", "SELECT * FROM system_monitoring")
        self.assertGreater(len(data), 0)

if __name__ == "__main__":
    unittest.main()
