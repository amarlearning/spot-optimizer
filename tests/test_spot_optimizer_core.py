import pytest
from unittest.mock import Mock
import pandas as pd
from spot_optimizer.spot_optimizer_core import SpotOptimizerCore
from spot_optimizer.exceptions import OptimizationError


@pytest.fixture
def mock_db():
    """Fixture for a mocked database."""
    db = Mock()
    db.query_data = Mock()
    return db


@pytest.fixture
def optimizer_core(mock_db):
    """Fixture for SpotOptimizerCore with a mocked database."""
    return SpotOptimizerCore(db=mock_db)


@pytest.fixture
def sample_query_result():
    """Sample DataFrame returned by a database query."""
    return pd.DataFrame(
        {
            "instance_type": ["m5.xlarge"],
            "cores": [4],
            "ram_gb": [16],
            "spot_score": [75],
            "interruption_rate": [1],
            "instances_needed": [2],
            "total_cores": [8],
            "total_memory": [32],
            "cpu_waste_pct": [0],
            "memory_waste_pct": [0],
        }
    )


def test_optimize_success(optimizer_core, mock_db, sample_query_result):
    """Test successful optimization."""
    mock_db.query_data.return_value = sample_query_result
    result = optimizer_core.optimize(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=False,
        arm_instances=True,
        instance_family=[],
        emr_version=None,
        mode="balanced",
    )
    assert result == {
        "instances": {"type": "m5.xlarge", "count": 2},
        "mode": "balanced",
        "total_cores": 8,
        "total_ram": 32,
        "reliability": {"spot_score": 75, "interruption_rate": 1},
    }
    # Verify query was called
    mock_db.query_data.assert_called_once()


def test_optimize_no_results(optimizer_core, mock_db):
    """Test optimization when no suitable instances are found."""
    mock_db.query_data.return_value = pd.DataFrame()
    with pytest.raises(OptimizationError, match="No suitable instances found"):
        optimizer_core.optimize(
            cores=8,
            memory=32,
            region="us-west-2",
            ssd_only=False,
            arm_instances=True,
            instance_family=[],
            emr_version=None,
            mode="balanced",
        )


def test_optimize_with_instance_family(optimizer_core, mock_db, sample_query_result):
    """Test optimization with an instance family filter."""
    mock_db.query_data.return_value = sample_query_result
    optimizer_core.optimize(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=False,
        arm_instances=True,
        instance_family=["m5", "c5"],
        emr_version=None,
        mode="balanced",
    )
    query_call = mock_db.query_data.call_args[0][0]
    assert "instance_family IN (?,?)" in query_call


def test_optimize_with_ssd_only(optimizer_core, mock_db, sample_query_result):
    """Test optimization with SSD-only filter."""
    mock_db.query_data.return_value = sample_query_result
    optimizer_core.optimize(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=True,
        arm_instances=True,
        instance_family=[],
        emr_version=None,
        mode="balanced",
    )
    query_call = mock_db.query_data.call_args[0][0]
    assert "i.storage_type = 'ssd'" in query_call


def test_optimize_without_arm_instances(optimizer_core, mock_db, sample_query_result):
    """Test optimization with ARM instances disabled."""
    mock_db.query_data.return_value = sample_query_result
    optimizer_core.optimize(
        cores=8,
        memory=32,
        region="us-west-2",
        ssd_only=False,
        arm_instances=False,
        instance_family=[],
        emr_version=None,
        mode="balanced",
    )
    query_call = mock_db.query_data.call_args[0][0]
    assert "i.architecture != 'arm64'" in query_call


def test_optimize_database_error(optimizer_core, mock_db):
    """Test handling of database errors during optimization."""
    mock_db.query_data.side_effect = Exception("DB error")
    with pytest.raises(OptimizationError, match="Unexpected error during optimization"):
        optimizer_core.optimize(
            cores=8,
            memory=32,
            region="us-west-2",
            ssd_only=False,
            arm_instances=True,
            instance_family=[],
            emr_version=None,
            mode="balanced",
        )
