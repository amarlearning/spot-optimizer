from datetime import datetime

import duckdb
import pandas as pd

from spark_cluster_optimiser.storage_engine.storage_engine import StorageEngine


class DuckDBStorage(StorageEngine):
    def __init__(self, db_path: str = ":memory:"):
        """
        :param db_path: Path to the DuckDB database file (default: in-memory).
        """
        self.conn = duckdb.connect(database=db_path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS cache_timestamp (timestamp TIMESTAMP);"""
        )
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS global_rate (global_rate VARCHAR);"""
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS instance_types (instance_types VARCHAR,cores INTEGER,ram_gb FLOAT,emr BOOLEAN);"""
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ranges (index INTEGER,label VARCHAR,dots INTEGER,max INTEGER);"""
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spot_advisor (region VARCHAR,os VARCHAR,instance_types VARCHAR,s INTEGER,r INTEGER);"""
        )

    def store_data(self, data: dict) -> None:
        """
        Stores the fetched data in DuckDB.
        :param data: Data to be stored.
        """
        self.conn.execute(
            """INSERT INTO cache_timestamp (timestamp) VALUES (?);""",
            [datetime.now()],
        )
        self.conn.execute(
            """INSERT INTO global_rate (global_rate) VALUES (?)""",
            [data["global_rate"]],
        )

        instance_data = [
            (key, value["cores"], value["ram_gb"], value["emr"])
            for key, value in data["instance_types"].items()
        ]
        self.conn.executemany(
            """INSERT INTO instance_types (instance_types, cores, ram_gb, emr) VALUES (?, ?, ?, ?)""",
            instance_data,
        )

        ranges_data = [
            (item["index"], item["label"], item["dots"], item["max"])
            for item in data["ranges"]
        ]
        self.conn.executemany(
            """INSERT INTO ranges (index, label, dots, max) VALUES (?, ?, ?, ?)""",
            ranges_data,
        )

    def query_data(self, query: str) -> pd.DataFrame:
        """
        Queries the data stored in DuckDB.
        :param query: SQL query string.
        :return: Query result as a pandas DataFrame.
        """
        return self.conn.execute(query).fetchdf()

    def clear_data(self) -> None:
        """
        Clears all data stored in DuckDB.
        """
        self.conn.execute("""DELETE FROM cache_timestamp;""")
        self.conn.execute("""DELETE FROM global_rate;""")
        self.conn.execute("""DELETE FROM instance_types;""")
        self.conn.execute("""DELETE FROM ranges;""")
        self.conn.execute("""DELETE FROM spot_advisor;""")
