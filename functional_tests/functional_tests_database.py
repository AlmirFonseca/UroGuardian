import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.config_manager import ConfigManager

config_manager = ConfigManager()
db = Database(config_manager)

# Example data for insertion
data = {"timestamp": "2025-03-29 10:00:00", "cpu_usage": 20.5}

# Insert data into the 'system_monitoring' table
db.insert_data("insert_data_system_monitoring", "system_monitoring", data)

# Fetch and print all records
records = db.fetch_all("fetch_data", "SELECT * FROM system_monitoring")
print(records)
