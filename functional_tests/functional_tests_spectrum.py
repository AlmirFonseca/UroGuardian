import sys
import os

# Add the parent folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_manager import ConfigManager
from src.spectrum import SpectrumSensor
import board
import time

def spectrum_demo():
    # Create an instance of the SpectrumSensor
    config_manager = ConfigManager()
    spectrum = SpectrumSensor(conf=config_manager, i2c_bus=board.I2C())
    
    # Display readings for specific channels
    print("Reading 415nm and 555nm channels...")
    spectrum.display_channel_readings(["415nm", "555nm"])

    # Display all channel readings
    print("Reading all channels...")
    spectrum.display_all_channel_readings()

    # Enable flicker detection
    print("Enabling flicker detection...")
    spectrum.enable_flicker_detection(True)
    
    # Get flicker detection status
    flicker_status = spectrum.get_flicker_detection_status()
    if flicker_status:
        print(f"Detected a {flicker_status} Hz flicker")
    else:
        print("No flicker detected.")
    
    # Toggle LED
    print("Turning on LED...")
    spectrum.toggle_led(True)

    # Set LED current
    print("Setting LED current to 10...")
    spectrum.set_led_current(10)
    
    # Wait 3 seconds
    print("Waiting for 3 seconds...")
    time.sleep(3)
    
    # Turn off LED
    print("Turning off LED...")
    spectrum.toggle_led(False)

if __name__ == "__main__":
    spectrum_demo()
