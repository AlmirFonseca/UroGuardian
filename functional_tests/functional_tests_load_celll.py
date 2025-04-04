import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from src.load_cell import LoadCell
from src.database import Database
from src.config_manager import ConfigManager
from datetime import datetime

class TestLoadCellFunctional(unittest.TestCase):
    
    def setUp(self):
        """Configuração dos testes, criando objetos mock para as dependências."""
        # Mocking the ConfigManager and Database classes
        self.config_manager = MagicMock()
        self.db = MagicMock()
        
        # Configuração do ConfigManager mock
        self.config_manager.get.return_value = {
            "pins": {"LOADCELL_DT": 5, "LOADCELL_SCK": 6},
            "conf": {"adc_gain": 1}
        }
        
        # Instanciando a LoadCell com mocks
        self.load_cell = LoadCell(self.config_manager, self.db)
        
    def test_full_workflow(self):
        """Testa o fluxo completo de tare, calibração, leitura de peso e persistência de dados"""
        # Simular o comportamento de leitura e tare
        self.load_cell.hx711.get_value = MagicMock(return_value=10000)
        
        # Realiza o tare
        self.load_cell.tare()
        
        # Calibra com dois pontos
        self.load_cell.calibrate_two_point(weight1=500, reading1=10000, weight2=1000, reading2=20000)
        
        # Realiza a leitura do peso
        weight = self.load_cell.read_weight()
        
        # Verifica se o peso lido é o esperado
        self.assertEqual(weight, 10000 * 0.05 - 12345)
        
        # Verificar as inserções no banco de dados
        self.db.insert_data.assert_called_with(
            "insert_data_tare_log", 
            "tare_log", 
            {"timestamp": self.load_cell.logger.get_timestamp(), "tare_offset": 12345}
        )
        
        self.db.insert_data.assert_called_with(
            "insert_data_calibration_log", 
            "calibration_data", 
            {"timestamp": self.load_cell.logger.get_timestamp(), "calibration_factor": 0.05, "tare_offset": 12345}
        )
        
        # Verificar se a atualização da calibração foi chamada
        self.db.update_data.assert_called_with(
            "update_calibration_data", 
            "calibration_data", 
            {"timestamp": self.load_cell.logger.get_timestamp(), "calibration_factor": 0.05, "tare_offset": 12345}, 
            f"timestamp = '{self.load_cell.logger.get_timestamp()}'"
        )

if __name__ == "__main__":
    unittest.main()
