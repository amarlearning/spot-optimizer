import os
import threading
from typing import Dict, List, Optional
from appdirs import user_data_dir

from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import AwsSpotAdvisorData
from spot_optimizer.storage_engine.duckdb_storage_engine import DuckDBStorage
from spot_optimizer.spot_advisor_engine import SpotAdvisorEngine
from spot_optimizer.spot_optimizer_core import SpotOptimizerCore
from spot_optimizer.validators import validate_optimization_params
from spot_optimizer.logging_config import get_logger


logger = get_logger(__name__)


class SpotOptimizerFacade:
    """Facade for spot instance optimization, providing a simplified interface."""

    _instance: Optional["SpotOptimizerFacade"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        spot_advisor: AwsSpotAdvisorData,
        db: DuckDBStorage,
        engine: SpotAdvisorEngine,
        core: SpotOptimizerCore,
    ):
        """
        Initialize the facade with its dependencies.
        Args:
            spot_advisor: Data source for spot instance information.
            db: Database storage engine.
            engine: Engine for managing data freshness.
            core: Core optimization logic.
        """
        self.spot_advisor = spot_advisor
        self.db = db
        self.engine = engine
        self.core = core
        self._initialized = False

    def __enter__(self) -> "SpotOptimizerFacade":
        """Context manager entry."""
        if not self._initialized:
            self.db.connect()
            self._initialized = True
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit with proper cleanup."""
        self.cleanup()

    def cleanup(self) -> None:
        """Cleanup database connection and resources."""
        if self._initialized and hasattr(self, "db") and self.db is not None:
            try:
                self.db.disconnect()
            except Exception as e:
                logger.warning(f"Error during database cleanup: {e}")
            finally:
                self._initialized = False

    @classmethod
    def get_instance(cls) -> "SpotOptimizerFacade":
        """
        Get or create the singleton instance using thread-safe double-checked locking.
        Returns:
            SpotOptimizerFacade: Singleton instance of the optimizer facade.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.create_default()
        return cls._instance

    @classmethod
    def create_default(cls) -> "SpotOptimizerFacade":
        """Create a default instance of the facade with dependencies."""
        db_path = cls.get_default_db_path()
        logger.debug(f"Using database path: {db_path}")

        spot_advisor = AwsSpotAdvisorData()
        db = DuckDBStorage(db_path=db_path)
        engine = SpotAdvisorEngine(spot_advisor, db)
        core = SpotOptimizerCore(db)

        return cls(spot_advisor, db, engine, core)

    @staticmethod
    def get_default_db_path() -> str:
        """
        Get the database path in user data directory.
        Returns:
            str: Path to the database file in the user's data directory.
        """
        app_name = "spot-optimizer"
        app_author = "aws-samples"  # Change this to your organization name
        data_dir = user_data_dir(app_name, app_author)
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "spot_advisor_data.db")

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance for testing purposes.
        This method should only be used in tests.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.cleanup()
                cls._instance = None

    def optimize(
        self,
        cores: int,
        memory: int,
        region: str = "us-west-2",
        ssd_only: bool = False,
        arm_instances: bool = True,
        instance_family: Optional[List[str]] = None,
        emr_version: Optional[str] = None,
        mode: str = "balanced",
    ) -> Dict:
        """
        Optimize spot instance configuration based on requirements.
        """
        validate_optimization_params(cores, memory)
        self.engine.ensure_fresh_data()
        return self.core.optimize(
            cores=cores,
            memory=memory,
            region=region,
            ssd_only=ssd_only,
            arm_instances=arm_instances,
            instance_family=instance_family,
            emr_version=emr_version,
            mode=mode,
        )
