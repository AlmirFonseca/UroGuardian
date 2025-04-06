import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlite3
from datetime import datetime
from unittest.mock import MagicMock


from src.database import Database
from src.config_manager import ConfigManager
from src.logger import Logger

class TestDatabase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Mocking the ConfigManager and Logger classes
        cls.config_manager = ConfigManager()
        cls.logger = Logger()

        # # Configurações de banco de dados para o teste
        # cls.db_filepath = "unittest_database.db"
        # cls.db_queries_filepath = "test_db_queries.yaml"
    

        # Criação do Database para o teste
        cls.db = Database(cls.config_manager)
    
    @classmethod
    def setUp(self):
        # Limpar o banco de dados antes de cada teste
        self.db.connection.execute("DELETE FROM device")
        self.db.connection.execute("DELETE FROM patient")
        self.db.connection.commit()

    def test_insert_device(self):
        """Testa a inserção de dados na tabela device."""
        device_data = ("UroGuardian MVP", "0.0.1", "192.168.0.168", "active", "2025-03-30 08:00:00")
        self.db.insert_data("insert_device", "device", {
            "name": device_data[0],
            "version": device_data[1],
            "ip_address": device_data[2],
            "status": device_data[3],
            "last_update": device_data[4]
        })
        
        # Verifica se a inserção foi bem-sucedida
        result = self.db.fetch_one("fetch_device")
        self.assertEqual(result[1], "UroGuardian MVP")
        self.assertEqual(result[2], "0.0.1")
        self.assertEqual(result[3], "192.168.0.168")
        self.assertEqual(result[4], "active")

    def test_insert_patient(self):
        """Testa a inserção de dados na tabela patient."""
        patient_data = ('M', 55, 175, 72, 'Hipertensão', 'A1', 'Leito 1', 'Paciente em tratamento de pressão alta', 
                        '2025-03-30 08:00:00', '', '2025-03-30 08:00:00', '')
        self.db.insert_data("insert_patient", "patient", {
            "gender": patient_data[0],
            "age": patient_data[1],
            "height": patient_data[2],
            "weight": patient_data[3],
            "renal_conditions": patient_data[4],
            "room": patient_data[5],
            "bed": patient_data[6],
            "observations": patient_data[7],
            "urine_bag_usage_start_time": patient_data[8],
            "urine_bag_usage_end_time": patient_data[9],
            "device_usage_start_time": patient_data[10],
            "device_usage_end_time": patient_data[11]
        })
        
        # Verifica se a inserção foi bem-sucedida
        result = self.db.fetch_one("fetch_patient", "SELECT * FROM patient ORDER BY id DESC LIMIT 1")
        self.assertEqual(result[1], 'M')
        self.assertEqual(result[2], 55)
        self.assertEqual(result[3], 175)

    def test_update_device(self):
        """Testa a atualização de dados na tabela device."""
        device_data = ("UroGuardian MVP", "0.0.1", "192.168.0.168", "inactive", "2025-03-30 09:00:00")
        self.db.insert_data("insert_device", "device", {
            "name": device_data[0],
            "version": device_data[1],
            "ip_address": device_data[2],
            "status": device_data[3],
            "last_update": device_data[4]
        })
        
        # Atualiza o status do dispositivo
        self.db.update_data("update_data", "device", {
            "name": "UroGuardian MVP",
            "version": "0.0.1",
            "ip_address": "192.168.0.168",
            "status": "active",
            "last_update": "2025-03-30 10:00:00"
        })
        
        # Verifica se a atualização foi bem-sucedida
        result = self.db.fetch_one("fetch_device", "SELECT * FROM device ORDER BY id DESC LIMIT 1")
        self.assertEqual(result[4], "active")

    def test_fetch_all_devices(self):
        """Testa a recuperação de todos os dispositivos."""
        self.db.insert_data("insert_device", "device", {
            "name": "Device 1", "version": "1.0", "ip_address": "192.168.0.101", "status": "active", "last_update": "2025-03-30 08:00:00"
        })
        self.db.insert_data("insert_device", "device", {
            "name": "Device 2", "version": "1.2", "ip_address": "192.168.0.102", "status": "inactive", "last_update": "2025-03-30 08:10:00"
        })
        
        # Recupera todos os dispositivos
        result = self.db.fetch_all("fetch_devices", "SELECT * FROM device")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], "Device 1")
        self.assertEqual(result[1][1], "Device 2")

    def test_backup_database(self):
        """Testa o backup do banco de dados."""
        self.db.backup_database(backup_dir="database_backups")
        
        # Verifica se o arquivo de backup foi criado
        backup_files = os.listdir("database_backups")
        self.assertTrue(len(backup_files) > 0)
        self.assertTrue(backup_files[0].startswith("backup_"))

    def test_describe_database(self):
        """Testa a descrição do banco de dados."""
        schema = self.db.describe_database()
        
        self.assertIn("device", schema)
        self.assertIn("columns", schema["device"])
        self.assertIn("foreign_keys", schema["device"])

    # def test_close_connection(self):
    #     """Testa o fechamento da conexão com o banco de dados."""
    #     self.db.close()
        
    #     # Verifica se a conexão foi fechada
    #     with self.assertRaises(sqlite3.ProgrammingError):
    #         self.db.connection.execute("SELECT * FROM device")
            
    #     # Reabre a conexão para outros testes
    #     self.db.connection = sqlite3.connect(self.db.db_filepath)

if __name__ == '__main__':
    unittest.main()
