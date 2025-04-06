import time
import json
import os
from hx711 import HX711
from typing import Tuple, Optional
from datetime import datetime


from src.config_manager import ConfigManager
from src.logger import Logger
from src.database import Database

class LoadCell:
    """Wrapper class to interface with the HX711 module and load cell.

    This class provides methods to read weight, tare the scale, calibrate with two known weights,
    and handle raw sensor data.

    Attributes:
        hx711 (HX711): The HX711 object to interface with the load cell.
        calibration_factor (float): Calibration factor for converting raw data to weight.
        tare_offset (float): The tare (zero) offset for the scale.
        db (Database): The Database instance for storing calibration and tare logs.
    """
    
    def __init__(self, config_manager: ConfigManager, db: Database) -> None:
        """Initializes the load cell interface.

        Args:
            config_manager (ConfigManager): The ConfigManager instance to load pin configurations.
            db (Database): The Database instance to log tare and calibration events.
        
        Returns:
            None
        """
        # Read pin configurations from config/pins.yaml using ConfigManager
        pins = config_manager.get("pins")
        dt_pin = pins.get("LOADCELL_DT")  # Data pin for HX711
        sck_pin = pins.get("LOADCELL_SCK")  # Clock pin for HX711
        
        # Initialize HX711 object
        self.hx711 = HX711(dout=dt_pin, pd_sck=sck_pin)
        
        # Initialize attributes
        self.db = db
        self.calibration_factor = 1.0
        self.tare_offset = 0.0
        
        # Load calibration data from the database
        self.load_calibration_from_db()
        
        # Initialize the logger
        self.logger = Logger()
        self.logger.println("LoadCell initialized successfully.", "INFO")

    def tare(self) -> None:
        """Tares the load cell (sets the current reading to zero).

        Args:
            None
        
        Returns:
            None
        """
        self.hx711.tare()
        self.tare_offset = self.hx711.get_value(5)
        
        # Log tare action in the database with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        calibration_data = {
            "timestamp": timestamp,
            "calibration_factor": self.calibration_factor,
            "tare_offset": self.tare_offset
        }
        self.db.insert_data("insert_data_calibration_log", "calibration_data", calibration_data)
        self.logger.println(f"Scale tared. Current tare offset: {self.tare_offset} at {timestamp}", "INFO")
    
    def calibrate_two_point(self, weight1: float, reading1: float, weight2: float, reading2: float) -> None:
        """Calibrate the load cell using two known weights and their corresponding readings.

        Args:
            weight1 (float): The first known weight (in units of choice, e.g., grams).
            reading1 (float): The raw reading from the load cell for the first weight.
            weight2 (float): The second known weight.
            reading2 (float): The raw reading from the load cell for the second weight.
        
        Returns:
            None
        """
        # Calculate calibration factor
        scale1 = weight1 / reading1
        scale2 = weight2 / reading2
        
        # Average the scale factors from both points
        self.calibration_factor = (scale1 + scale2) / 2.0
        
        # Log calibration event in the database with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        calibration_data = {
            "timestamp": timestamp,
            "calibration_factor": self.calibration_factor,
            "tare_offset": self.tare_offset
        }
        self.db.insert_data("insert_data_calibration_log", "calibration_data", calibration_data)
        
        # Update calibration data in the database
        self.update_calibration_in_db(timestamp, self.calibration_factor, self.tare_offset)
        self.logger.println(f"Calibration successful. Calibration factor: {self.calibration_factor} at {timestamp}", "INFO")
    
    def read_weight(self) -> float:
        """Reads the current weight from the load cell, applying the calibration factor.

        Returns:
            float: The current weight in calibrated units (e.g., grams).
        """
        raw_data = self.hx711.get_value(5)
        weight = raw_data * self.calibration_factor
        weight -= self.tare_offset  # Apply tare offset
        
        self.logger.println(f"Raw data: {raw_data}, Weight: {weight} grams", "DEBUG")
        
        return weight
    
    def get_raw_data(self) -> int:
        """Returns the raw sensor data from the load cell.

        This is useful for debugging or advanced processing.

        Returns:
            int: The raw reading from the load cell.
        """
        return self.hx711.get_value(5)

    def update_calibration_in_db(self, timestamp: str, calibration_factor: float, tare_offset: float) -> None:
        """Updates the calibration data in the database.

        Args:
            timestamp (str): The timestamp of the calibration.
            calibration_factor (float): The new calibration factor.
            tare_offset (float): The new tare offset.

        Returns:
            None
        """
        calibration_data = {
            "timestamp": timestamp,
            "calibration_factor": calibration_factor,
            "tare_offset": tare_offset
        }
        self.db.update_data("update_calibration_data", "calibration_data", calibration_data, f"timestamp = '{timestamp}'")
        self.logger.println(f"Calibration data updated at {timestamp}", "INFO")
        self.logger.println(f"Calibration factor: {calibration_factor}, Tare offset: {tare_offset}", "DEBUG")
    
    def load_calibration_from_db(self) -> None:
        """Loads the most recent calibration data from the database.

        This method reads the calibration factor and tare offset from the `calibration_data` table.

        Returns:
            None
        """
        result = self.db.fetch_one("fetch_latest_load_cell_calibration_data", "SELECT * FROM calibration_data ORDER BY timestamp DESC LIMIT 1")
        
        if result:
            self.calibration_factor = result[2]  # Assuming calibration_factor is the 3rd column
            self.tare_offset = result[3]  # Assuming tare_offset is the 4th column
            self.logger.println("Calibration data loaded successfully from the database.", "INFO")
        else:
            self.logger.println("No calibration data found in the database. Using default calibration.", "WARNING")

# # Example Usage
# if __name__ == "__main__":
#     # Initialize the ConfigManager to read pins from config/pins.yaml
#     from config_manager import ConfigManager
#     config_manager = ConfigManager()

#     # Initialize the Database
#     from database import Database  # Import the Database module
#     db = Database(config_manager)
    
#     # Initialize the LoadCell with the Database instance
#     load_cell = LoadCell(config_manager, db)

#     # Tare the scale
#     load_cell.tare()

#     # Perform a two-point calibration with known weights
#     load_cell.calibrate_two_point(weight1=100, reading1=150000, weight2=200, reading2=300000)

#     # Read the current weight
#     weight = load_cell.read_weight()
#     print(f"Current weight: {weight} grams")

#     # Get raw data
#     raw_data = load_cell.get_raw_data()
#     print(f"Raw data: {raw_data}")
