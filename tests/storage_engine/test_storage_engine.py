import pytest
from spot_optimizer.storage_engine.storage_engine import StorageEngine


def test_storage_engine_is_abstract():
    """Test that StorageEngine cannot be instantiated directly and requires implementation of abstract methods."""

    # Try to create a concrete class missing all required methods
    with pytest.raises(TypeError) as exc_info:

        class InvalidStorage(StorageEngine):
            pass

        InvalidStorage()
    assert "Can't instantiate abstract class" in str(exc_info.value)

    # Try to create a concrete class missing some required methods
    with pytest.raises(TypeError) as exc_info:

        class PartialStorage(StorageEngine):
            def connect(self):
                pass

            def disconnect(self):
                pass

            # Missing store_data, query_data, and clear_data

        PartialStorage()
    assert "Can't instantiate abstract class" in str(exc_info.value)

    # Verify that a complete implementation can be instantiated
    class ValidStorage(StorageEngine):
        def connect(self):
            pass

        def disconnect(self):
            pass

        def store_data(self, data):
            pass

        def query_data(self, query, params=None):
            pass

        def clear_data(self):
            pass

    # This should not raise any exceptions
    ValidStorage()
