import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import patch, MagicMock


from src.joystick import Joystick
from src.config_manager import ConfigManager
from src.logger import Logger


class TestJoystickUnit(unittest.TestCase):
    """Unit test for the Joystick class, testing individual methods."""

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

    def test_get_button_name(self):
        """Test the method to get the button name from a GPIO channel."""
        self.assertEqual(self.joystick._get_button_name(17), "UP")
        self.assertEqual(self.joystick._get_button_name(27), "DOWN")
        self.assertEqual(self.joystick._get_button_name(22), "LEFT")
        self.assertEqual(self.joystick._get_button_name(5), "RIGHT")
        self.assertEqual(self.joystick._get_button_name(6), "PRESS")
        self.assertIsNone(self.joystick._get_button_name(100))  # Invalid channel

    def test_handle_button_action(self):
        """Test that correct actions are called for each button press."""
        with patch.object(self.joystick, '_move_up') as mock_move_up:
            self.joystick._handle_button_action("UP")
            mock_move_up.assert_called_once()

        with patch.object(self.joystick, '_move_down') as mock_move_down:
            self.joystick._handle_button_action("DOWN")
            mock_move_down.assert_called_once()

        with patch.object(self.joystick, '_move_left') as mock_move_left:
            self.joystick._handle_button_action("LEFT")
            mock_move_left.assert_called_once()

        with patch.object(self.joystick, '_move_right') as mock_move_right:
            self.joystick._handle_button_action("RIGHT")
            mock_move_right.assert_called_once()

        with patch.object(self.joystick, '_press_button') as mock_press_button:
            self.joystick._handle_button_action("PRESS")
            mock_press_button.assert_called_once()

    def tearDown(self):
        """Clean up after each test."""
        self.joystick.cleanup()


if __name__ == "__main__":
    unittest.main()
