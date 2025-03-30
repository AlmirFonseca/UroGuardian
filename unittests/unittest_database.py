import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
from src.database import Database
from src.config_manager import ConfigManager

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()
        self.db = Database(self.config_manager)

    def test_insert_data(self):
        data = {"timestamp": "2025-03-29 10:00:00", "cpu_usage": 20.5}
        self.db.insert_data("insert_data_system_monitoring", "system_monitoring", data)
        result = self.db.fetch_all("fetch_data", "SELECT * FROM system_monitoring")
        self.assertGreater(len(result), 0)

if __name__ == "__main__":
    unittest.main()
