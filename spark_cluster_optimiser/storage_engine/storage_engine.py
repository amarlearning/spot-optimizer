from abc import ABC, abstractmethod

import pandas as pd


class StorageEngine(ABC):
    @abstractmethod
    def store_data(self, data: dict) -> None:
        """
        Stores the fetched data in DuckDB.
        :param data: Data to be stored.
        """
        pass

    @abstractmethod
    def query_data(self, query: str) -> pd.DataFrame:
        """
        Queries the data stored in DuckDB.
        :param query: SQL query string.
        :return: Query result as a pandas DataFrame.
        """
        pass

    @abstractmethod
    def clear_data(self) -> None:
        """
        Clears all data stored in DuckDB.
        """
        pass
