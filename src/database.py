import sqlite3
import subprocess
import yaml
import os
import shutil
from datetime import datetime
from flask import Flask, jsonify
from typing import Any, Dict, Optional

from src.config_manager import ConfigManager
from src.logger import Logger

class Database:
    """Class for managing the SQLite database with dynamic queries loaded from a YAML file.

    This class loads DDL and DML queries from the configuration file 'db_queries.yaml' and executes them to manage the
    database schema and data. It provides CRUD operations to store and retrieve variables.

    Attributes:
        db_filepath (str): Path to the SQLite database file.
        queries (Dict[str, str]): Dictionary of queries loaded from the YAML configuration file.
        connection (sqlite3.Connection): Database connection object.
        cursor (sqlite3.Cursor): Cursor object for executing SQL queries.
    """

    def __init__(self, config_manager: ConfigManager, 
                 db_filepath: str = "../database/sensor_data.db", 
                 db_queries_filepath = "../config/db_queries.yaml") -> None:
        """Initializes the database connection and loads queries.

        Args:
            config_manager (ConfigManager): The ConfigManager instance to load queries.
            db_filepath (str, optional): Path to the SQLite database file. Default is "../database/sensor_data.db".
            db_queries_filepath (str, optional): Path to the YAML file containing queries. Default is "../config/db_queries.yaml".

        Raises:
            FileNotFoundError: If the queries file doesn't exist.
        """
        self.config_manager = config_manager
        self.logger = Logger()
        
        self.db_filepath = self.config_manager.get("conf").get("db_filepath")
        if not self.db_filepath:
            self.db_filepath = db_filepath
            
        self.db_queries_filepath = self.config_manager.get("conf").get("db_queries_filepath")
        if not self.db_queries_filepath:
            self.db_queries_filepath = db_queries_filepath
        
        self.queries = self.load_queries()
        self.connection = sqlite3.connect(self.db_filepath, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.initialize_db()
        
        # Debug: Load mock data if specified in the configuration
        if self.config_manager.get("conf").get("load_mock_data"):
            self.logger.println("Inserting mock data...", "DEBUG")
            self.mock_data()

        # Open SQLiteWeb interface for debugging using sqlite-web
        self.start_sqlite_web()
        
        self.logger.println("Database initialized successfully.", "INFO")
        
        self.device_id = None
        self.urine_bag_id = None

    def load_queries(self) -> Dict[str, str]:
        """Load DDL and DML queries from the 'db_queries.yaml' configuration file.

        Returns:
            Dict[str, str]: Dictionary of queries.
            
        Raises:
            FileNotFoundError: If the queries file doesn't exist.
        """
        
        if not os.path.exists(self.db_queries_filepath):
            raise FileNotFoundError(f"Queries file '{self.db_queries_filepath}' not found.")
        
        with open(self.db_queries_filepath, "r") as file:
            return yaml.safe_load(file)

    def initialize_db(self) -> None:
        """Initializes the database schema by executing DDL queries from the loaded configuration.

        Returns:
            None
        """
        ddl_queries = self.queries.get("ddl", {})
        for query_key, query in ddl_queries.items():
            self.execute_query(query_key, query)
            
    def start_sqlite_web(self) -> None:
        """Starts the SQLiteWeb server to view and interact with the database in a browser.

        This will run the `sqlite_web` tool in the background to serve the database via a web interface.
        The server will be accessible via a browser at the specified address.
        
        Returns:
            None
        """
        try:
            # Run sqlite-web to open the database in a browser
            # Use subprocess to run the command as a background process
            subprocess.Popen(['sqlite_web', self.db_filepath])            
            
            # Get the networks IP address of the device
            hostname = subprocess.check_output(['hostname', '-I']).decode().strip().split()[0]
            self.logger.println(f"SQLiteWeb is running at http://{hostname}:8080", "INFO")
            
        except Exception as e:
            self.logger.println(f"Error starting SQLiteWeb: {e}", "ERROR")
        

    def execute_query(self, query_key: str, query: str, params: tuple = ()) -> None:
        """Execute a query (INSERT, SELECT, etc.) on the database. 

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            None
        """
        self.logger.println(f"Executing query: {query_key}", "DEBUG")
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_one(self, query_key: str, query: Optional[str] = "", params: tuple = ()) -> Any:
        """Fetch a single result from a query.

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            Any: The fetched result.
            
        Raises:
            ValueError: If the query key is not found.
        """
        query = self.queries.get("fetch", {}).get(query_key) if not query else query
        
        if not query:
            raise ValueError(f"Fetch query with key '{query_key}' not found.")
        
        self.logger.println(f"Fetching one result for query: {query_key}", "DEBUG")
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query_key: str, query: Optional[str] = "", params: tuple = ()) -> Any:
        """Fetch all results from a query.

        Args:
            query_key (str): The key identifying the query.
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the SQL query (default is an empty tuple).
        
        Returns:
            Any: The fetched results.
            
        Raises:
            ValueError: If the query key is not found.
        """
        query = self.queries.get("fetch", {}).get(query_key) if not query else query
        
        if not query:
            raise ValueError(f"Fetch query with key '{query_key}' not found.")
        
        self.logger.println(f"Fetching all results for query: {query_key}", "DEBUG")
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
            
        Raises:
            ValueError: If the query key is not found.
        """
        query = self.queries.get("dml", {}).get(query_key)
        if not query:
            raise ValueError(f"Insert query with key '{query_key}' not found.")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = query.format(table=table, columns=columns, placeholders=placeholders)
        self.execute_query(query_key, query, tuple(data.values()))

    def update_data(self, query_key: str, table: str, data: Dict[str, Any], condition: Optional[str] = "1=1") -> None:
        """Update data in the specified table based on a condition.

        Args:
            query_key (str): The key identifying the update query.
            table (str): Table name.
            data (Dict[str, Any]): Data to update, as a dictionary.
            condition (str): Condition for the update (e.g., 'id = 1').

        Returns:
            None
            
        Raises:
            ValueError: If the query key is not found.
        """
        query = self.queries.get("update", {}).get(query_key)
        if not query:
            raise ValueError(f"Update query with key '{query_key}' not found.")
        
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = query.format(table=table, set_clause=set_clause, condition=condition)        
        self.execute_query(query_key, query, tuple(data.values()))
        
    def mock_data(self) -> None:
        """Load mock data into the database for testing purposes.

        Returns:
            None
        """
        mock_data_queries = self.queries.get("mock", {})
        for query_key, query in mock_data_queries.items():
            self.execute_query(query_key, query)
            
    def show_table(self, table: str) -> None:
        """Display the contents of the specified table.

        Args:
            table (str): Table name.
        
        Returns:
            None
        """
        query = f"SELECT * FROM {table}"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        for row in rows:
            print(row)
            
    def show_table_structure(self, table: str) -> None:
        """Display the structure of the specified table.

        Args:
            table (str): Table name.
        
        Returns:
            None
        """
        query = f"PRAGMA table_info({table})"
        self.cursor.execute(query)
        columns = self.cursor.fetchall()
        
        for column in columns:
            print(column)

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
        shutil.copy(self.db_filepath, backup_file)
        self.logger.println(f"Backup created at: {backup_file}", "INFO")

    def close(self) -> None:
        """Close the database connection.

        Returns:
            None
        """
        self.connection.close()
        
        self.logger.println("Database connection closed.", "INFO")
        
    def describe_database(self) -> Dict[str, Any]:
        """
        Describes the structure of the SQLite database, returning tables, columns, types, 
        primary keys and foreign keys.

        Returns:
            Dict[str, Any]: A dictionary describing the entire database schema.
        """
        self.logger.println("Describing database schema...", "INFO")

        schema = {}
        
        # Get all tables from the SQLite master
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in self.cursor.fetchall()]

        for table in tables:
            self.logger.println(f"Analyzing table: {table}", "DEBUG")
            
            schema[table] = {
                "columns": [],
                "foreign_keys": []
            }

            # Get columns information
            self.cursor.execute(f"PRAGMA table_info({table});")
            columns_info = self.cursor.fetchall()
            
            for column in columns_info:
                col_info = {
                    "id": column[0],
                    "name": column[1],
                    "type": column[2],
                    "notnull": bool(column[3]),
                    "default": column[4],
                    "primary_key": bool(column[5])
                }
                schema[table]["columns"].append(col_info)

            # Get foreign keys information
            self.cursor.execute(f"PRAGMA foreign_key_list({table});")
            foreign_keys_info = self.cursor.fetchall()
            
            for fk in foreign_keys_info:
                fk_info = {
                    "id": fk[0],
                    "seq": fk[1],
                    "table": fk[2],
                    "from": fk[3],
                    "to": fk[4],
                    "on_update": fk[5],
                    "on_delete": fk[6],
                    "match": fk[7]
                }
                schema[table]["foreign_keys"].append(fk_info)

        self.logger.println("Database schema description completed.", "INFO")

        return schema
    
    def get_new_id(self, table: str) -> int:
        """Get the next available ID for a new entry in the specified table.

        Args:
            table (str): The name of the table.
        
        Returns:
            int: The next available ID.
            
        Raises:
            ValueError: If the table does not exist or if the ID cannot be retrieved.
        """
        
        query = f"SELECT MAX(id) FROM {table}"
        max_id = self.fetch_one("get_new_id", query)
        
        if max_id is None:
            return 1
        else:
            return max_id[0] + 1
        
    def get_last_inserted_id(self, table: str) -> int:
        """Get the last inserted ID from the specified table.

        Args:
            table (str): The name of the table.
        
        Returns:
            int: The last inserted ID.
            
        Raises:
            ValueError: If the table does not exist or if the ID cannot be retrieved.
        """
        
        query = f"SELECT last_insert_rowid() FROM {table}"
        last_id = self.fetch_one("get_last_inserted_id", query)
        
        if last_id is None:
            return 0
        else:
            return last_id[0]
    
    def get_device_id(self) -> Optional[str]:
        """Get the device ID from the system according to the mac_address
        
        Args:
            None
        
        Returns:
            str: The device ID.
        
        Raises:
            ValueError: If the device ID is not found or if the device ID is not set.
        """
        
        if self.device_id:
            return self.device_id
        
        try:
            # Get the MAC address of the device
            mac_address = subprocess.check_output(['cat', '/sys/class/net/eth0/address']).decode().strip()
            
            # Get the device ID from the device table where mac_address matches
            query = "SELECT device_id FROM devices WHERE mac_address = ?"
            
            self.device_id = self.fetch_one("get_device_id", query, (mac_address,))
            
            return self.device_id
        except Exception as e:
            self.logger.println(f"Error getting device ID: {e}", "ERROR")
            return None
        
    def get_urine_bag_id(self, force_update: bool = False) -> Optional[str]:
        """Get the urine bag ID from the urine_bag table according to the device ID and where 'status' is 'active'
        
        Args:
            force_update (bool): If True, forces an update of the urine bag ID.
            
        Returns:
            str: The urine bag ID.
            
        Raises:
            ValueError: If the urine bag ID is not found or if the device ID is not set.
        """
        
        if self.urine_bag_id and not force_update:
            return self.urine_bag_id
        
        try:
            # Get the urine bag ID from the urine_bag table where device_id matches and status is active
            query = "SELECT urine_bag_id FROM urine_bag WHERE device_id = ? AND status = 'active'"
            
            self.urine_bag_id = self.fetch_one("get_urine_bag_id", query, (self.device_id,))
            
            return self.urine_bag_id
        except Exception as e:
            self.logger.println(f"Error getting urine bag ID: {e}", "ERROR")
            return None
        