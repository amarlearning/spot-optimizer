from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


class StorageEngine(ABC):
    """Abstract base class for storage engine implementations."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the storage."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the storage."""
        pass

    @abstractmethod
    def store_data(self, data: Dict[str, Any]) -> None:
        """
        Store data in the storage engine.
        :param data: Dictionary containing data to be stored.
        """
        pass

    @abstractmethod
    def query_data(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """
        Query data from the storage engine.
        :param query: Query string appropriate for the storage engine.
        :param params: Optional parameters for the query.
        :return: Query result as a pandas DataFrame.
        """
        pass

    @abstractmethod
    def clear_data(self) -> None:
        """Clear all data from the storage."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
