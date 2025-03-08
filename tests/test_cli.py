import pytest
from unittest.mock import patch

from spot_optimizer.cli import main, parse_args


@pytest.fixture
def mock_spot_optimiser():
    """Mock the spot_optimiser function."""
    with patch('spot_optimizer.cli.spot_optimiser') as mock:
        mock.return_value = {
            "instances": {
                "type": "m5.xlarge",
                "count": 2
            },
            "mode": "balanced",
            "total_cores": 8,
            "total_ram": 32
        }
        yield mock


def test_cli_required_args(mock_spot_optimiser, capsys):
    """Test CLI with only required arguments."""
    with patch('sys.argv', ['spot-optimiser', '--cores', '8', '--memory', '32']):
        main()
        
    mock_spot_optimiser.assert_called_once_with(
        cores=8,
        memory=32,
        region='us-west-2',  # default value
        ssd_only=False,      # default value
        arm_instances=False, # default value
        instance_family=None,  # default value
        emr_version=None,    # default value
        mode='balanced'      # default value
    )
    
    captured = capsys.readouterr()
    assert "Spot instance optimization result" in captured.out


def test_cli_all_args(mock_spot_optimiser, capsys):
    """Test CLI with all arguments specified."""
    with patch('sys.argv', [
        'spot-optimiser',
        '--cores', '16',
        '--memory', '64',
        '--region', 'us-east-1',
        '--ssd-only',
        '--arm-instances',
        '--instance-family', 'm6g', 'c6g',
        '--emr-version', '6.10.0',
        '--mode', 'latency'
    ]):
        main()
        
    mock_spot_optimiser.assert_called_once_with(
        cores=16,
        memory=64,
        region='us-east-1',
        ssd_only=True,
        arm_instances=True,
        instance_family=['m6g', 'c6g'],
        emr_version='6.10.0',
        mode='latency'
    )


def test_cli_invalid_mode(capsys):
    """Test CLI with invalid mode argument."""
    with patch('sys.argv', [
        'spot-optimiser',
        '--cores', '8',
        '--memory', '32',
        '--mode', 'invalid_mode'
    ]):
        with pytest.raises(SystemExit):
            main()
        
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err.lower()


def test_cli_missing_required_args(capsys):
    """Test CLI without required arguments."""
    with patch('sys.argv', ['spot-optimiser']):
        with pytest.raises(SystemExit):
            main()
        
    captured = capsys.readouterr()
    assert "the following arguments are required" in captured.err.lower()


def test_cli_invalid_cores(capsys):
    """Test CLI with invalid cores value."""
    with patch('sys.argv', ['spot-optimiser', '--cores', '-1', '--memory', '32']):
        with pytest.raises(SystemExit):
            main()
        
    captured = capsys.readouterr()
    assert "argument --cores" in captured.err.lower()


def test_cli_invalid_memory(capsys):
    """Test CLI with invalid memory value."""
    with patch('sys.argv', ['spot-optimiser', '--cores', '8', '--memory', '0']):
        with pytest.raises(SystemExit):
            main()
        
    captured = capsys.readouterr()
    assert "argument --memory" in captured.err.lower()


@pytest.mark.parametrize("cores,memory,expected_error", [
    (0, 32, "argument --cores: cores must be greater than 0, got 0"),
    (8, 0, "argument --memory: memory must be greater than 0, got 0"),
])
def test_cli_validation(cores, memory, expected_error):
    """Test CLI input validation."""
    args = [
        '--cores', str(cores),
        '--memory', str(memory)
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        parse_args(args)
    
    assert exc_info.value.code == 2

def test_cli_error_handling(mock_spot_optimiser):
    """Test CLI error handling when optimizer raises an exception."""
    mock_spot_optimiser.side_effect = Exception("Optimization failed")
    
    with patch('sys.argv', ['spot-optimiser', '--cores', '8', '--memory', '32']):
        with pytest.raises(Exception, match="Optimization failed"):
            main()
