import sqlite3
import yaml
import os
import shutil
from datetime import datetime
from flask import Flask, jsonify
from typing import Any, Dict

from src.config_manager import ConfigManager

class Database:
    """Class for managing the SQLite database with dynamic queries loaded from a YAML file.

    This class loads DDL and DML queries from the configuration file 'db_queries.yaml' and executes them to manage the
    database schema and data. It provides CRUD operations to store and retrieve variables.

    Attributes:
        db_file (str): Path to the SQLite database file.
        queries (Dict[str, str]): Dictionary of queries loaded from the YAML configuration file.
        connection (sqlite3.Connection): Database connection object.
        cursor (sqlite3.Cursor): Cursor object for executing SQL queries.
    """

    def __init__(self, config_manager: ConfigManager, db_file: str = "../sensor_data.db") -> None:
        """Initializes the database connection and loads queries.

        Args:
            config_manager (ConfigManager): The ConfigManager instance to load queries.
            db_file (str, optional): Path to the SQLite database file. Default is "sensor_data.db".

        Raises:
            FileNotFoundError: If the queries file doesn't exist.
        """
        self.db_file = db_file
        self.config_manager = config_manager
        self.queries = self.load_queries()
        self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.initialize_db()

    def load_queries(self) -> Dict[str, str]:
        """Load DDL and DML queries from the 'db_queries.yaml' configuration file.

        Returns:
            Dict[str, str]: Dictionary of queries.
        """
        queries_file = "../config/db_queries.yaml"
        if not os.path.exists(queries_file):
            raise FileNotFoundError(f"Queries file '{queries_file}' not found.")
        
        with open(queries_file, "r") as file:
            return yaml.safe_load(file)

    def initialize_db(self) -> None:
        """Initializes the database schema by executing DDL queries from the loaded configuration.

        Returns:
            None
        """
        ddl_queries = self.queries.get("ddl", {})
        for query_key, query in ddl_queries.items():
            self.execute_query(query_key, query)

    def execute_query(self, query_key: str, query: str, params: tuple = ()) -> None:
        """Execute a query (INSERT, SELECT, etc.) on the database. 

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            None
        """
        print(f"Executing query: {query_key}")
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_one(self, query_key: str, query: str, params: tuple = ()) -> Any:
        """Fetch a single result from a query.

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            Any: The fetched result.
        """
        print(f"Fetching one result for query: {query_key}")
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query_key: str, query: str, params: tuple = ()) -> Any:
        """Fetch all results from a query.

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            Any: The fetched results.
        """
        print(f"Fetching all results for query: {query_key}")
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def insert_data(self, query_key: str, table: str, data: Dict[str, Any]) -> None:
        """Insert data into the specified table.

        Args:
            query_key (str): The key identifying the insert query.
            table (str): Table name.
            data (Dict[str, Any]): Data to insert, as a dictionary.
        
        Returns:
            None
        """
        query = self.queries.get("dml", {}).get(query_key)
        if not query:
            raise ValueError(f"Insert query with key '{query_key}' not found.")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = query.format(table=table, columns=columns, placeholders=placeholders)
        self.execute_query(query_key, query, tuple(data.values()))

    def update_data(self, query_key: str, table: str, data: Dict[str, Any], condition: str) -> None:
        """Update data in the specified table based on a condition.

        Args:
            query_key (str): The key identifying the update query.
            table (str): Table name.
            data (Dict[str, Any]): Data to update, as a dictionary.
            condition (str): Condition for the update (e.g., 'id = 1').

        Returns:
            None
        """
        query = self.queries.get("dml", {}).get(query_key)
        if not query:
            raise ValueError(f"Update query with key '{query_key}' not found.")
        
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = query.format(table=table, set_clause=set_clause, condition=condition)
        self.execute_query(query_key, query, tuple(data.values()))

    def backup_database(self, backup_dir: str = "backups") -> None:
        """Create a backup of the current database with a timestamp in the filename.

        Args:
            backup_dir (str, optional): Directory where the backup will be stored. Default is 'backups'..
        
        Returns:
            None
        """
        # Ensure the backup directory exists
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Get the current date and time for the backup filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")

        # Copy the database to the backup file
        shutil.copy(self.db_file, backup_file)
        print(f"Backup created at: {backup_file}")

    def close(self) -> None:
        """Close the database connection.

        Returns:
            None
        """
        self.connection.close()


class DatabaseAPI:
    """Flask API for remotely accessing the local database data.

    This class exposes an API to remotely access data stored in the SQLite database.

    Attributes:
        app (Flask): Flask application instance.
        db (Database): Database instance to interact with the database.
    """

    def __init__(self, db: Database) -> None:
        """Initializes the Flask API.

        Args:
            db (Database): The database instance to interact with.

        Returns:
            None
        """
        self.db = db
        self.app = Flask(__name__)

        @self.app.route('/data/<table>', methods=['GET'])
        def get_data(table: str):
            """Fetch all data from the specified table.

            Args:
                table (str): Table name.
            
            Returns:
                JSON: The data in JSON format.
            """
            data = self.db.fetch_all("fetch_data", f"SELECT * FROM {table}")
            return jsonify(data)

    def run(self, host: str = "0.0.0.0", port: int = 5000) -> None:
        """Run the Flask API server.

        Args:
            host (str, optional): Host to bind the server to (default is '0.0.0.0').
            port (int, optional): Port to bind the server to (default is 5000).
        
        Returns:
            None
        """
        self.app.run(host=host, port=port)


# Example Usage:
# if __name__ == "__main__":
#     config_manager = ConfigManager()
#     db = Database(config_manager)
#     api = DatabaseAPI(db)
#     api.run(host="0.0.0.0", port=5000)
