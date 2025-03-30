from src.monitoring import SystemMonitoring
from src.database import Database
from src.config_manager import ConfigManager

config_manager = ConfigManager()
db = Database(config_manager)

# Initialize monitoring and start data collection
monitoring = SystemMonitoring(db)
monitoring.collect_and_store_data()

# Fetch the data and print
data = db.fetch_all("fetch_data", "SELECT * FROM system_monitoring")
print(data)
