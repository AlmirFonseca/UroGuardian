import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database, DatabaseAPI
from src.config_manager import ConfigManager

def database_demo():
    config_manager = ConfigManager()
    db = Database(config_manager)

    # Demonstração: Criar uma tabela personalizada
    create_query = "CREATE TABLE IF NOT EXISTS demo_table (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);"
    db.execute_query("create_demo_table", create_query)

    # Inserir dados na tabela personalizada
    data_to_insert = {"id": 1, "name": "Alice", "age": 30}
    insert_query = "INSERT INTO demo_table (id, name, age) VALUES (?, ?, ?);"
    db.execute_query("insert_demo_data", insert_query, tuple(data_to_insert.values()))

    # Ler os dados inseridos (fetch_one)
    fetch_query = "SELECT * FROM demo_table WHERE id = ?;"
    result = db.fetch_one("fetch_one_demo_data", fetch_query, (1,))
    print(f"Fetched single record: {result}")

    # Inserir mais dados para fetch_all
    data_to_insert_2 = {"id": 2, "name": "Bob", "age": 25}
    db.execute_query("insert_demo_data_2", insert_query, tuple(data_to_insert_2.values()))

    # Ler todos os dados (fetch_all)
    fetch_all_query = "SELECT * FROM demo_table;"
    all_results = db.fetch_all("fetch_all_demo_data", fetch_all_query)
    print(f"All records: {all_results}")

    # Atualizar um registro
    update_query = "UPDATE demo_table SET age = ? WHERE id = ?;"
    db.execute_query("update_demo_data", update_query, (31, 1))
    updated_result = db.fetch_one("fetch_updated_demo_data", fetch_query, (1,))
    print(f"Updated record: {updated_result}")

    # Realizar backup
    db.backup_database(backup_dir="../backups_demo")

    # Inicializar API Flask para consulta remota
    api = DatabaseAPI(db)
    print("Starting Flask API server for database. Access at: http://0.0.0.0:5000/data/demo_table")
    api.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    database_demo()
