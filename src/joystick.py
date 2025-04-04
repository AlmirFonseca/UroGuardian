import RPi.GPIO as GPIO
import time

from src.config_manager import ConfigManager
from src.logger import Logger

class Joystick:
    """Class to interface with a 5-direction analog joystick with 5 push buttons.

    This class sets up the joystick as a physical UI input device with buttons for each direction
    and logs button presses with the Logger class. The pins for the joystick buttons are fetched
    from the `pins.yaml` file using ConfigManager.

    Attributes:
        gpio_pins (dict): A dictionary containing GPIO pin mappings for the joystick buttons.
        logger (Logger): The Logger instance used to log actions performed by the joystick.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Initializes the Joystick class by setting up GPIO pins for buttons and interrupts.

        Args:
            config_manager (ConfigManager): Instance of ConfigManager to load pin configurations from 'pins.yaml'.

        Raises:
            KeyError: If the pin configuration in 'pins.yaml' is missing or incorrect.
        """
        # Load the GPIO pins from the config
        self.config_manager = config_manager
        self.gpio_pins = self.config_manager.get("pins")
        self.logger = Logger()

        # Define the joystick buttons (Up, Down, Left, Right, Center/Press)
        try:
            self.pins = {
                "UP": self.gpio_pins["JOYSTICK_UP"],
                "DOWN": self.gpio_pins["JOYSTICK_DOWN"],
                "LEFT": self.gpio_pins["JOYSTICK_LEFT"],
                "RIGHT": self.gpio_pins["JOYSTICK_RIGHT"],
                "PRESS": self.gpio_pins["JOYSTICK_PRESS"]
            }
        except KeyError as e:
            self.logger.println(f"Missing pin in configuration: {e}", "ERROR")
            raise

        self._setup_gpio()

    def _setup_gpio(self):
        """Sets up the GPIO pins for the joystick buttons and configures them as interrupts.

        This method configures each button pin as an input and sets up a falling edge interrupt to detect button presses.
        Each button press will trigger a corresponding handler method.
        """
        GPIO.setmode(GPIO.BCM)
        for button, pin in self.pins.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull-up resistors
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self._button_pressed, bouncetime=300)  # Debounce time
            self.logger.println(f"Configured {button} button on pin {pin} as an interrupt", "INFO")
    
    def _button_pressed(self, channel):
        """Handles the button press event for any of the joystick buttons.

        Args:
            channel (int): The GPIO channel number corresponding to the button that was pressed.
        """
        button = self._get_button_name(channel)
        if button:
            self.logger.println(f"{button} button pressed", "INFO")
            self._handle_button_action(button)
        else:
            self.logger.println("Unknown button press detected", "ERROR")

    def _get_button_name(self, channel):
        """Maps the GPIO channel to the corresponding button name.

        Args:
            channel (int): The GPIO pin number.

        Returns:
            str: The name of the button (e.g., 'UP', 'DOWN', 'LEFT', 'RIGHT', 'PRESS') or None if unknown.
        """
        for button, pin in self.pins.items():
            if pin == channel:
                return button
        return None

    def _handle_button_action(self, button):
        """Handles the action triggered by a button press.

        Args:
            button (str): The name of the button that was pressed (e.g., 'UP', 'DOWN', etc.)
        """
        if button == "UP":
            self._move_up()
        elif button == "DOWN":
            self._move_down()
        elif button == "LEFT":
            self._move_left()
        elif button == "RIGHT":
            self._move_right()
        elif button == "PRESS":
            self._press_button()

    def _move_up(self):
        """Handles the action when the UP button is pressed."""
        self.logger.println("Joystick moved UP", "DEBUG")
        # Implement logic for UP direction (e.g., UI navigation, etc.)

    def _move_down(self):
        """Handles the action when the DOWN button is pressed."""
        self.logger.println("Joystick moved DOWN", "DEBUG")
        # Implement logic for DOWN direction

    def _move_left(self):
        """Handles the action when the LEFT button is pressed."""
        self.logger.println("Joystick moved LEFT", "DEBUG")
        # Implement logic for LEFT direction

    def _move_right(self):
        """Handles the action when the RIGHT button is pressed."""
        self.logger.println("Joystick moved RIGHT", "DEBUG")
        # Implement logic for RIGHT direction

    def _press_button(self):
        """Handles the action when the PRESS button is pressed."""
        self.logger.println("Joystick PRESS button pressed", "DEBUG")
        # Implement logic for PRESS button (e.g., select, submit, etc.)

    def cleanup(self):
        """Cleans up GPIO settings when done to release the pins."""
        GPIO.cleanup()
        self.logger.println("GPIO cleanup done.", "INFO")


# Example usage in main.py:

# if __name__ == "__main__":
#     from src.config_manager import ConfigManager

#     # Initialize ConfigManager and Joystick
#     config_manager = ConfigManager()
#     joystick = Joystick(config_manager)

#     try:
#         # Keep the program running to listen for joystick input
#         print("Joystick is ready. Press buttons to interact.")
#         while True:
#             time.sleep(1)  # Keep the script alive to listen for button presses
#     except KeyboardInterrupt:
#         # Clean up on exit
#         print("Exiting...")
#         joystick.cleanup()
