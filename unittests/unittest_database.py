import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import os
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.database import Database
from src.config_manager import ConfigManager

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.config_manager = ConfigManager()
        
        # Criar um banco de testes temporário
        self.db_file = "test_sensor_data.db"
        self.db = Database(self.config_manager, db_file=self.db_file)

        # Garantir que a tabela exista
        create_query = "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, data TEXT);"
        self.db.execute_query("create_test_table", create_query)

    def tearDown(self):
        # Fechar conexão e remover banco temporário após testes
        self.db.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

        # Limpeza dos backups de testes
        if os.path.exists("test_backups"):
            shutil.rmtree("test_backups")

    def test_insert_data(self):
        data = {"id": 1, "data": "Test Data"}
        insert_query = "INSERT INTO test_table (id, data) VALUES (?, ?);"
        self.db.execute_query("insert_test_data", insert_query, (data["id"], data["data"]))

        result = self.db.fetch_one("fetch_test_data", "SELECT * FROM test_table WHERE id = ?", (1,))
        self.assertEqual(result, (1, "Test Data"))

    def test_update_data(self):
        # Inserir dados iniciais
        insert_query = "INSERT INTO test_table (id, data) VALUES (?, ?);"
        self.db.execute_query("insert_test_data", insert_query, (1, "Old Data"))

        # Atualizar os dados
        update_query = "UPDATE test_table SET data = ? WHERE id = ?;"
        self.db.execute_query("update_test_data", update_query, ("New Data", 1))

        result = self.db.fetch_one("fetch_test_data", "SELECT * FROM test_table WHERE id = ?", (1,))
        self.assertEqual(result, (1, "New Data"))

    def test_fetch_all(self):
        # Inserir múltiplos dados
        insert_query = "INSERT INTO test_table (id, data) VALUES (?, ?);"
        for i in range(3):
            self.db.execute_query(f"insert_test_data_{i}", insert_query, (i, f"Data {i}"))

        results = self.db.fetch_all("fetch_all_test_data", "SELECT * FROM test_table;")
        self.assertEqual(len(results), 3)

    def test_backup_database(self):
        # Realiza backup e verifica criação
        self.db.backup_database(backup_dir="test_backups")

        backup_files = os.listdir("test_backups")
        self.assertEqual(len(backup_files), 1)
        self.assertTrue(backup_files[0].startswith("backup_"))
        self.assertTrue(backup_files[0].endswith(".db"))

if __name__ == "__main__":
    unittest.main()
