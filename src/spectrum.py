import time
import board
from adafruit_as7341 import AS7341
from typing import List, Tuple, Optional

from src.config_manager import ConfigManager
from src.logger import Logger

class SpectrumSensor:
    """Wrapper class for the AS7341 Spectrometer sensor.

    This class provides a flexible API to interact with the AS7341 sensor. It allows reading individual channels,
    enabling flicker detection, and fetching all channels in a batch.

    Attributes:
        sensor (AS7341): Instance of the AS7341 sensor.
    """

    def __init__(self,  conf: ConfigManager, i2c_bus=None) -> None:
        """Initializes the AS7341 sensor.

        Args:
            i2c_bus (I2C, optional): The I2C bus to use. Defaults to board.I2C().
            address (int, optional): The I2C address of the sensor. Default is 0x39.
        
        Returns:
            None
        """
        self.conf = conf
        self.logger = Logger()
        
        if i2c_bus is None:
            i2c_bus = board.I2C()
            
        self.i2c_address = self.conf.get("addresses").get("AS7341", 0x39)  # Default I2C address for AS7341
        
        self.sensor = AS7341(i2c_bus, self.i2c_address)
        self.initialize_sensor()

    def initialize_sensor(self) -> None:
        """Initializes the sensor with default settings.

        This function configures the sensor with the default settings like enabling LED, setting integration time, etc.

        Returns:
            None
        """
        self.sensor.initialize()
        self.logger.println("AS7341 sensor initialized.", "INFO")
    
    def read_channel(self, channel: str) -> int:
        """Reads the value of a specific channel.

        Args:
            channel (str): The channel to read, e.g., '415nm', '445nm', etc.

        Returns:
            int: The current reading for the specified channel.
        
        Raises:
            ValueError: If the channel name is invalid.
        """
        valid_channels = {
            "415nm": self.sensor.channel_415nm,
            "445nm": self.sensor.channel_445nm,
            "480nm": self.sensor.channel_480nm,
            "515nm": self.sensor.channel_515nm,
            "555nm": self.sensor.channel_555nm,
            "590nm": self.sensor.channel_590nm,
            "630nm": self.sensor.channel_630nm,
            "680nm": self.sensor.channel_680nm,
            "clear": self.sensor.channel_clear,
            "nir": self.sensor.channel_nir,
        }
        
        try:
            if channel not in valid_channels:
                raise ValueError(f"Invalid channel name: {channel}")
        except ValueError as e:
            self.logger.println(str(e), "ERROR")
        
        return valid_channels[channel]

    def read_all_channels(self) -> dict:
        """Reads the values from all channels.

        Returns:
            dict: A dictionary containing the readings for each channel with keys in the format:
                {"channel_415nm": value, "channel_445nm": value, ..., "channel_nir": value}
        """
        return {
            "channel_415nm": self.sensor.channel_415nm,
            "channel_445nm": self.sensor.channel_445nm,
            "channel_480nm": self.sensor.channel_480nm,
            "channel_515nm": self.sensor.channel_515nm,
            "channel_555nm": self.sensor.channel_555nm,
            "channel_590nm": self.sensor.channel_590nm,
            "channel_630nm": self.sensor.channel_630nm,
            "channel_680nm": self.sensor.channel_680nm,
            "channel_clear": self.sensor.channel_clear,
            "channel_nir": self.sensor.channel_nir,
        }

    def enable_flicker_detection(self, enabled: bool = True) -> None:
        """Enables or disables flicker detection.

        Args:
            enabled (bool): Set to True to enable flicker detection, False to disable it.
        
        Returns:
            None
        """
        self.sensor.flicker_detection_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.println(f"Flicker detection {status}.", "INFO")
    
    def get_flicker_detection_status(self) -> Optional[int]:
        """Returns the current flicker detection frequency, if enabled.

        Returns:
            int or None: The flicker frequency detected, or None if flicker detection is disabled.
        """
        if self.sensor.flicker_detection_enabled:
            if self.sensor.flicker_detected:
                self.logger.println(f"Flicker detected: {self.sensor.flicker_frequency} Hz", "INFO")
            else:
                self.logger.println("No flicker detected.", "INFO")
            return self.sensor.flicker_detected
        else:
            self.logger.println("Flicker detection is disabled. Cannot get status", "WARNING")
            return None

    def set_led_current(self, current: int) -> None:
        """Sets the current for the LED.

        Args:
            current (int): The current value to set for the LED.
        
        Returns:
            None
        """
        self.sensor.led_current = current
        self.logger.println(f"LED current set to {current}.", "INFO")
    
    def toggle_led(self, state: bool) -> None:
        """Toggles the LED on or off.

        Args:
            state (bool): Set to True to turn on the LED, False to turn it off.
        
        Returns:
            None
        """
        self.sensor.led = state
        status = "on" if state else "off"
        self.logger.println(f"LED is turned {status}.", "INFO")

    def display_channel_readings(self, channels: List[str]) -> None:
        """Displays the readings for the specified channels.

        Args:
            channels (List[str]): List of channel names to display, e.g., ['415nm', '555nm'].
        
        Returns:
            None
        """
        for channel in channels:
            try:
                reading = self.read_channel(channel)
                self.logger.println(f"{channel}: {reading}", "DEBUG")
            except ValueError as e:
                self.logger.println(str(e), "ERROR")

    def display_all_channel_readings(self) -> None:
        """Displays the readings for all channels.

        Returns:
            None
        """
        channel_names = [
            "415nm", "445nm", "480nm", "515nm", "555nm", 
            "590nm", "630nm", "680nm", "clear", "nir"
        ]
        readings = self.read_all_channels()
        
        for name, reading in zip(channel_names, readings):
            self.logger.println(f"{name}: {reading}", "DEBUG")

# # Example Usage:
# if __name__ == "__main__":
#     spectrum = SpectrumSensor(i2c_bus=board.I2C())
    
#     # Display readings for specific channels
#     spectrum.display_channel_readings(["415nm", "555nm"])
    
#     # Display all channel readings
#     spectrum.display_all_channel_readings()
    
#     # Enable flicker detection
#     spectrum.enable_flicker_detection(True)
    
#     # Toggle LED
#     spectrum.toggle_led(True)
    
#     # Set LED current
#     spectrum.set_led_current(50)
    
#     # Display flicker detection status
#     flicker_status = spectrum.get_flicker_detection_status()
#     if flicker_status:
#         print(f"Detected a {flicker_status} Hz flicker")
#     else:
#         print("No flicker detected.")
