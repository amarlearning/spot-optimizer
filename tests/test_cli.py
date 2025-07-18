import pytest
import json
from argparse import ArgumentTypeError
from unittest.mock import patch

from spot_optimizer.cli import validate_positive_int, parse_args, main


@pytest.mark.parametrize(
    "value,param_name,expected",
    [
        ("10", "cores", 10),
        ("100", "memory", 100),
        ("1", "cores", 1),
    ],
)
def test_validate_positive_int_valid(value, param_name, expected):
    """Test validation of valid positive integers."""
    assert validate_positive_int(value, param_name) == expected


@pytest.mark.parametrize(
    "value,param_name,error_msg",
    [
        ("0", "cores", "cores must be greater than 0, got 0"),
        ("-1", "memory", "memory must be greater than 0, got -1"),
        ("abc", "cores", "cores must be an integer, got abc"),
        ("1.5", "memory", "memory must be an integer, got 1.5"),
    ],
)
def test_validate_positive_int_invalid(value, param_name, error_msg):
    """Test validation of invalid positive integers."""
    with pytest.raises(ArgumentTypeError, match=error_msg):
        validate_positive_int(value, param_name)


def test_parse_args_required_only():
    """Test parsing with only required arguments."""
    args = parse_args(["--cores", "8", "--memory", "32"])
    assert args.cores == 8
    assert args.memory == 32
    assert args.region == "us-west-2"  # default
    assert not args.ssd_only  # default
    assert not args.arm_instances  # default
    assert args.instance_family is None  # default
    assert args.emr_version is None  # default
    assert args.mode == "balanced"  # default


def test_parse_args_all_options():
    """Test parsing with all arguments."""
    args = parse_args(
        [
            "--cores",
            "16",
            "--memory",
            "64",
            "--region",
            "us-east-1",
            "--ssd-only",
            "--arm-instances",
            "--instance-family",
            "m6g",
            "r6g",
            "--emr-version",
            "6.9.0",
            "--mode",
            "latency",
        ]
    )
    assert args.cores == 16
    assert args.memory == 64
    assert args.region == "us-east-1"
    assert args.ssd_only
    assert args.arm_instances
    assert args.instance_family == ["m6g", "r6g"]
    assert args.emr_version == "6.9.0"
    assert args.mode == "latency"


def test_parse_args_invalid_mode():
    """Test parsing with invalid mode."""
    with pytest.raises(SystemExit):
        parse_args(["--cores", "8", "--memory", "32", "--mode", "invalid"])


def test_parse_args_missing_required():
    """Test parsing without required arguments."""
    with pytest.raises(SystemExit):
        parse_args([])


@patch("spot_optimizer.cli.optimize")
def test_main_success(mock_optimize):
    """Test successful execution of main function."""
    expected_result = {
        "instances": {"type": "m5.xlarge", "count": 2},
        "mode": "balanced",
        "total_cores": 8,
        "total_ram": 32.0,
        "reliability": {"spot_score": 75, "interruption_rate": 1},
    }
    mock_optimize.return_value = expected_result

    with patch("sys.argv", ["spot-optimizer", "--cores", "8", "--memory", "32"]):
        with patch("builtins.print") as mock_print:
            main()

            # Verify optimize was called with correct arguments
            mock_optimize.assert_called_once_with(
                cores=8,
                memory=32,
                region="us-west-2",
                ssd_only=False,
                arm_instances=False,
                instance_family=None,
                emr_version=None,
                mode="balanced",
            )

            # Verify output was correct JSON
            mock_print.assert_called_once_with(json.dumps(expected_result, indent=2))


@patch("spot_optimizer.cli.optimize")
def test_main_error(mock_optimize):
    """Test main function with optimization error."""
    mock_optimize.side_effect = ValueError("No suitable instances found")

    with patch("sys.argv", ["spot-optimizer", "--cores", "8", "--memory", "32"]):
        with pytest.raises(ValueError, match="No suitable instances found"):
            main()


def test_validate_positive_int_directly():
    """Test the validate_positive_int function directly."""
    # Test valid cases
    assert validate_positive_int("10", "cores") == 10
    assert validate_positive_int("100", "memory") == 100

    # Test invalid cases
    with pytest.raises(ArgumentTypeError, match="cores must be greater than 0, got 0"):
        validate_positive_int("0", "cores")

    with pytest.raises(
        ArgumentTypeError, match="memory must be greater than 0, got -1"
    ):
        validate_positive_int("-1", "memory")

    with pytest.raises(ArgumentTypeError, match="cores must be an integer, got abc"):
        validate_positive_int("abc", "cores")


@pytest.mark.parametrize(
    "args,expected_error",
    [
        (
            ["--cores", "0", "--memory", "32"],
            "argument --cores: cores must be greater than 0, got 0",
        ),
        (
            ["--cores", "8", "--memory", "-1"],
            "argument --memory: memory must be greater than 0, got -1",
        ),
        (
            ["--cores", "abc", "--memory", "32"],
            "argument --cores: cores must be an integer, got abc",
        ),
    ],
)
def test_main_invalid_inputs(args, expected_error):
    """Test main function with invalid inputs."""
    with patch("sys.argv", ["spot-optimizer"] + args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
