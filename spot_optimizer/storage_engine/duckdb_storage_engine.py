import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

from spot_optimizer.storage_engine.storage_engine import StorageEngine


class DuckDBStorage(StorageEngine):
    """DuckDB implementation of the storage engine."""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize DuckDB storage.
        :param db_path: Path to the DuckDB database file (default: in-memory).
        """
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        
        metadata_path = os.path.join(Path(__file__).parent.parent, "resources", "instance_metadata.json")

        with open(metadata_path) as f:
            self.instance_metadata = json.load(f)

    def connect(self) -> None:
        """Establish connection to DuckDB."""
        self.conn = duckdb.connect(database=self.db_path)
        self._create_tables()

    def disconnect(self) -> None:
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        if not self.conn:
            raise RuntimeError("No database connection")

        tables = {
            "cache_timestamp": "CREATE TABLE IF NOT EXISTS cache_timestamp (timestamp TIMESTAMP)",
            "global_rate": "CREATE TABLE IF NOT EXISTS global_rate (global_rate VARCHAR)",
            "instance_types": """
                CREATE TABLE IF NOT EXISTS instance_types (
                    instance_type VARCHAR,
                    instance_family VARCHAR,
                    cores INTEGER,
                    ram_gb FLOAT,
                    storage_type VARCHAR,
                    architecture VARCHAR,
                    emr_compatible BOOLEAN DEFAULT FALSE,
                    emr_min_version VARCHAR
                )
            """,
            "ranges": """
                CREATE TABLE IF NOT EXISTS ranges (
                    index INTEGER,
                    label VARCHAR,
                    dots INTEGER,
                    max INTEGER
                )
            """,
            "spot_advisor": """
                CREATE TABLE IF NOT EXISTS spot_advisor (
                    region VARCHAR,
                    os VARCHAR,
                    instance_types VARCHAR,
                    s INTEGER,
                    r INTEGER
                )
            """
        }

        for table_name, create_sql in tables.items():
            try:
                self.conn.execute(create_sql)
            except Exception as e:
                raise RuntimeError(f"Failed to create table {table_name}: {str(e)}")

    def store_data(self, data: Dict[str, Any]) -> None:
        """
        Store data in DuckDB.
        :param data: Dictionary containing data to be stored.
        :raises RuntimeError: If no database connection exists.
        """
        if not self.conn:
            raise RuntimeError("No database connection")

        try:
            # Store timestamp
            self.conn.execute(
                "INSERT INTO cache_timestamp (timestamp) VALUES (?)",
                [datetime.now()]
            )

            # Store global rate
            self.conn.execute(
                "INSERT INTO global_rate (global_rate) VALUES (?)",
                [data["global_rate"]]
            )
            
            # Store instance data with metadata
            instance_data = []
            for key, value in data["instance_types"].items():
                # Get storage and arch from metadata, fallback to defaults if not found
                metadata = self.instance_metadata.get(key, {})
                instance_data.append((
                    key,
                    key.split(".")[0],
                    value["cores"],
                    value["ram_gb"],
                    metadata.get("storage", "ebs"),
                    metadata.get("arch", "x86_64"),
                    value.get("emr", False),
                    value.get("emr_min_version", None)
                ))

            self.conn.executemany(
                """
                INSERT INTO instance_types (
                    instance_type, instance_family, cores, ram_gb,
                    storage_type, architecture,
                    emr_compatible, emr_min_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                instance_data
            )

            # Store ranges data
            ranges_data = [
                (item["index"], item["label"], item["dots"], item["max"])
                for item in data["ranges"]
            ]
            self.conn.executemany(
                "INSERT INTO ranges (index, label, dots, max) VALUES (?, ?, ?, ?)",
                ranges_data
            )

            # Fix: Store spot advisor data with correct structure
            spot_advisor_data = []
            for region, os_data in data["spot_advisor"].items():
                for os_name, instance_data in os_data.items():
                    for instance_type, scores in instance_data.items():
                        spot_advisor_data.append((
                            region,          # e.g., "ap-southeast-4"
                            os_name,         # e.g., "Linux"
                            instance_type,   # e.g., "r6i.24xlarge"
                            scores["s"],     # spot score
                            scores["r"]      # rate
                        ))

            self.conn.executemany(
                "INSERT INTO spot_advisor (region, os, instance_types, s, r) VALUES (?, ?, ?, ?, ?)",
                spot_advisor_data
            )

        except Exception as e:
            raise RuntimeError(f"Failed to store data: {str(e)}")

    def query_data(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """
        Query data from DuckDB.
        :param query: SQL query string.
        :param params: Optional query parameters.
        :return: Query result as pandas DataFrame.
        :raises RuntimeError: If no database connection exists.
        """
        if not self.conn:
            raise RuntimeError("No database connection")

        try:
            if params:
                return self.conn.execute(query, params).fetchdf()
            return self.conn.execute(query).fetchdf()
        except Exception as e:
            raise RuntimeError(f"Query failed: {str(e)}")

    def clear_data(self) -> None:
        """
        Clear all data from DuckDB tables.
        :raises RuntimeError: If no database connection exists.
        """
        if not self.conn:
            raise RuntimeError("No database connection")

        tables = ["cache_timestamp", "global_rate", "instance_types", "ranges", "spot_advisor"]
        for table in tables:
            try:
                self.conn.execute(f"DELETE FROM {table}")
            except Exception as e:
                raise RuntimeError(f"Failed to clear table {table}: {str(e)}")
