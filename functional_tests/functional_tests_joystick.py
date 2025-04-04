import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import time
import unittest
from unittest.mock import patch, MagicMock


from src.joystick import Joystick
from src.config_manager import ConfigManager
from src.logger import Logger


class TestJoystickFunctional(unittest.TestCase):
    """Test the joystick functionality, simulating button presses and logging."""

    @patch('RPi.GPIO.add_event_detect')  # Mock GPIO to avoid actual pin configuration
    @patch('RPi.GPIO.setup')  # Mock GPIO setup
    @patch('RPi.GPIO.cleanup')  # Mock GPIO cleanup
    def setUp(self, mock_cleanup, mock_setup, mock_add_event_detect):
        """Set up the test environment, mocking GPIO methods."""
        self.config_manager = MagicMock(ConfigManager)
        # Simulating the pin mappings as they would be in the 'pins.yaml'
        self.config_manager.get.return_value = {
            "JOYSTICK_UP": 17,
            "JOYSTICK_DOWN": 27,
            "JOYSTICK_LEFT": 22,
            "JOYSTICK_RIGHT": 23,
            "JOYSTICK_PRESS": 24
        }
        
        # Create the Joystick object
        self.joystick = Joystick(self.config_manager)

    @patch.object(Logger, 'println')  # Mocking the Logger to test logs
    def test_button_press(self, mock_println):
        """Test joystick button press actions."""
        
        # Simulating button press events
        with patch.object(self.joystick, '_handle_button_action') as mock_handle_action:
            self.joystick._button_pressed(17)  # Simulate UP button press
            mock_handle_action.assert_called_with("UP")
            mock_println.assert_called_with("UP button pressed", "INFO")
            
            self.joystick._button_pressed(27)  # Simulate DOWN button press
            mock_handle_action.assert_called_with("DOWN")
            mock_println.assert_called_with("DOWN button pressed", "INFO")

            self.joystick._button_pressed(22)  # Simulate LEFT button press
            mock_handle_action.assert_called_with("LEFT")
            mock_println.assert_called_with("LEFT button pressed", "INFO")

            self.joystick._button_pressed(5)  # Simulate RIGHT button press
            mock_handle_action.assert_called_with("RIGHT")
            mock_println.assert_called_with("RIGHT button pressed", "INFO")

            self.joystick._button_pressed(6)  # Simulate PRESS button press
            mock_handle_action.assert_called_with("PRESS")
            mock_println.assert_called_with("PRESS button pressed", "INFO")

    @patch.object(Logger, 'println')  # Mocking the Logger to test logs
    def test_button_actions(self, mock_println):
        """Test joystick actions triggered by button presses."""
        
        with patch.object(self.joystick, '_move_up') as mock_move_up:
            self.joystick._handle_button_action("UP")
            mock_move_up.assert_called_once()
            mock_println.assert_called_with("Joystick moved UP", "DEBUG")
        
        with patch.object(self.joystick, '_move_down') as mock_move_down:
            self.joystick._handle_button_action("DOWN")
            mock_move_down.assert_called_once()
            mock_println.assert_called_with("Joystick moved DOWN", "DEBUG")
        
        with patch.object(self.joystick, '_move_left') as mock_move_left:
            self.joystick._handle_button_action("LEFT")
            mock_move_left.assert_called_once()
            mock_println.assert_called_with("Joystick moved LEFT", "DEBUG")
        
        with patch.object(self.joystick, '_move_right') as mock_move_right:
            self.joystick._handle_button_action("RIGHT")
            mock_move_right.assert_called_once()
            mock_println.assert_called_with("Joystick moved RIGHT", "DEBUG")
        
        with patch.object(self.joystick, '_press_button') as mock_press_button:
            self.joystick._handle_button_action("PRESS")
            mock_press_button.assert_called_once()
            mock_println.assert_called_with("Joystick PRESS button pressed", "DEBUG")
            
    def tearDown(self):
        """Clean up after each test."""
        self.joystick.cleanup()


if __name__ == "__main__":
    unittest.main()
