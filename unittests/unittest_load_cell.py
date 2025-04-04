import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock
from src.load_cell import LoadCell
from datetime import datetime

class TestLoadCell(unittest.TestCase):
    
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
        
    def test_tare(self):
        """Testa o método tare()"""
        # Mock the hx711 behavior
        self.load_cell.hx711.tare = MagicMock()
        self.load_cell.hx711.get_value = MagicMock(return_value=12345)
        
        self.load_cell.tare()  # Realiza o tare
        
        # Verificar se o tare foi realizado corretamente
        self.load_cell.hx711.tare.assert_called_once()
        self.assertEqual(self.load_cell.tare_offset, 12345)
        self.db.insert_data.assert_called_with(
            "insert_data_tare_log", 
            "tare_log", 
            {"timestamp": self.load_cell.logger.get_timestamp(), "tare_offset": 12345}
        )
    
    def test_calibrate_two_point(self):
        """Testa o método de calibração de dois pontos"""
        self.load_cell.hx711.get_value = MagicMock(return_value=10000)
        
        # Calibração com 2 pesos conhecidos
        self.load_cell.calibrate_two_point(weight1=500, reading1=10000, weight2=1000, reading2=20000)
        
        # Verificar se o fator de calibração foi calculado corretamente
        self.assertEqual(self.load_cell.calibration_factor, 0.05)
        self.db.insert_data.assert_called_with(
            "insert_data_calibration_log", 
            "calibration_data", 
            {"timestamp": self.load_cell.logger.get_timestamp(), "calibration_factor": 0.05, "tare_offset": 12345}
        )
    
    def test_read_weight(self):
        """Testa a leitura de peso com fator de calibração"""
        self.load_cell.calibration_factor = 0.05  # Fator de calibração configurado
        self.load_cell.hx711.get_value = MagicMock(return_value=10000)
        
        weight = self.load_cell.read_weight()
        
        # O peso deve ser o valor do valor bruto multiplicado pelo fator de calibração e subtraído do offset de tara
        self.assertEqual(weight, 10000 * 0.05 - 12345)  # Peso = leitura * calibração - tare_offset
    
    def test_get_raw_data(self):
        """Testa a leitura dos dados brutos"""
        self.load_cell.hx711.get_value = MagicMock(return_value=10000)
        
        raw_data = self.load_cell.get_raw_data()
        
        # Verificar se a leitura bruta está correta
        self.assertEqual(raw_data, 10000)

    def test_load_calibration_from_db(self):
        """Testa se os dados de calibração são carregados corretamente do banco de dados"""
        self.db.fetch_one.return_value = (1, "2025-03-30 12:00:00", 0.05, 100)
        
        self.load_cell.load_calibration_from_db()  # Carregar calibração
        
        self.assertEqual(self.load_cell.calibration_factor, 0.05)
        self.assertEqual(self.load_cell.tare_offset, 100)
        
    def test_update_calibration_in_db(self):
        """Testa se a calibração é atualizada no banco de dados"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.load_cell.update_calibration_in_db(timestamp, 0.05, 100)
        
        # Verificar se o método de atualização foi chamado corretamente
        self.db.update_data.assert_called_with(
            "update_calibration_data", 
            "calibration_data", 
            {"timestamp": timestamp, "calibration_factor": 0.05, "tare_offset": 100}, 
            f"timestamp = '{timestamp}'"
        )

if __name__ == "__main__":
    unittest.main()
