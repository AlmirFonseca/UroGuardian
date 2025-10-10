import time
import board
import Adafruit_ADS1x15
from src.config_manager import ConfigManager
from src.logger import Logger

class ADC:
    """Class to interface with the ADS1115 Analog-to-Digital Converter (ADC).

    This class uses the Adafruit CircuitPython ADS1x15 library to read analog values from the ADS1115.
    It allows configuring the ADC's gain, selecting channels dynamically, and reading the raw values or voltages.

    Attributes:
        adc (Adafruit_ADS1x15.ADS1115): The instance of the ADS1115 ADC object.
        logger (Logger): The Logger instance for logging ADC actions.
        gain (int): The gain setting for the ADC.
        i2c_address (int): The I2C address of the ADC.
    """

    def __init__(self, config_manager: ConfigManager):
        """Initializes the ADC with configuration settings and prepares it for reading.

        Args:
            config_manager (ConfigManager): The ConfigManager instance to load configuration values.

        Raises:
            ValueError: If the pin configuration for the ADC is missing or incorrect.
        """
        # Load ADC configuration settings from the config
        self.config_manager = config_manager
        self.logger = Logger()

        # Load ADS1115 settings
        self.i2c_address = self.config_manager.get("pins").get("ADS1115_I2C_ADDRESS", 0x48)
        self.gain = self.config_manager.get("conf").get("adc_gain", 1)  # Default gain is 1

        # Set up the ADS1115
        self.adc = Adafruit_ADS1x15.ADS1115(address=self.i2c_address)

        # Initialize the logger
        self.logger.println(f"Initialized ADS1115 on I2C address {hex(self.i2c_address)} with gain {self.gain}", "INFO")

    def set_gain(self, gain: int):
        """Sets the gain for the ADC, which impacts the input voltage range.

        Args:
            gain (int): Gain value, which determines the input voltage range.

        Raises:
            ValueError: If an invalid gain value is provided.
        """
        valid_gains = {
            1: 6.144,   # ±6.144V
            2: 4.096,   # ±4.096V
            4: 2.048,   # ±2.048V
            8: 1.024,   # ±1.024V
            16: 0.512   # ±0.512V
        }

        if gain not in valid_gains:
            raise ValueError("Invalid gain. Valid gains are: 1, 2, 4, 8, 16.")
        
        self.gain = gain
        self.logger.println(f"Gain set to {gain}", "INFO")

    def read_channel(self, channel: int) -> int:
        """Reads the raw value from a specific channel.

        Args:
            channel (int): The channel to read, e.g., 0, 1, 2, 3 for AIN0, AIN1, AIN2, AIN3.

        Returns:
            int: The raw ADC reading.
        """
        if channel < 0 or channel > 3:
            raise ValueError("Channel must be an integer between 0 and 3.")

        raw_value = self.adc.read_adc(channel, gain=self.gain, data_rate=860)
        self.logger.println(f"Raw value read from channel {channel}: {raw_value}", "DEBUG")
        return raw_value

    def read_voltage(self, channel: int) -> float:
        """Reads the voltage value corresponding to the specific channel.

        Args:
            channel (int): The channel to read, e.g., 0, 1, 2, 3 for AIN0, AIN1, AIN2, AIN3.

        Returns:
            float: The voltage corresponding to the raw ADC value.
        """
        raw_value = self.read_channel(channel)
        voltage = self.adc.voltage(raw_value, gain=self.gain)
        self.logger.println(f"Voltage on channel {channel}: {voltage:.4f}V", "DEBUG")
        return voltage

    def read_all_channels(self) -> dict:
        """Reads all channels (AIN0, AIN1, AIN2, AIN3) and returns their raw values.

        Returns:
            dict: A dictionary with channel numbers as keys and their raw values as values.
        """
        channels = [0, 1, 2, 3]
        channel_data = {}

        for i in channels:
            raw_value = self.adc.read_adc(i, gain=self.gain, data_rate=860)
            channel_data[f"AIN{i}"] = raw_value
            self.logger.println(f"Raw value for AIN{i}: {raw_value}", "DEBUG")

        return channel_data

    def get_voltage_all_channels(self) -> dict:
        """Reads the voltage values for all channels and returns them in a dictionary.

        Returns:
            dict: A dictionary with channel names as keys and voltage values as values.
        """
        raw_data = self.read_all_channels()
        voltage_data = {channel: self.adc.voltage(value, gain=self.gain) for channel, value in raw_data.items()}

        for channel, voltage in voltage_data.items():
            self.logger.println(f"Voltage on {channel}: {voltage:.4f}V", "DEBUG")

        return voltage_data

    def cleanup(self):
        """Cleans up the GPIO settings."""
        GPIO.cleanup()
        self.logger.println("GPIO cleanup done for ADC.", "INFO")
