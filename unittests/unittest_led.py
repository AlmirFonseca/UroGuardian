import unittest
from src.led import RGBLed

class TestLED(unittest.TestCase):

    def setUp(self):
        self.led = RGBLed(dt_pin=5, sck_pin=6)  # Sample pins

    def test_set_color(self):
        self.led.set_color(255, 0, 0)  # Red
        self.assertEqual(self.led.get_color(), (255, 0, 0))

    def test_brightness(self):
        self.led.set_brightness(50)
        self.assertEqual(self.led.get_brightness(), 50)

if __name__ == "__main__":
    unittest.main()
