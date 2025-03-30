import unittest
from src.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()

    def test_get_config(self):
        config = self.config_manager.get("conf")
        self.assertIn("ntp_server", config)
        self.assertEqual(config["ntp_server"], "pool.ntp.org")  # Adjust based on your config

    def test_reload_configs(self):
        self.config_manager.reload()
        config = self.config_manager.get("conf")
        self.assertIn("timezone", config)

if __name__ == "__main__":
    unittest.main()
