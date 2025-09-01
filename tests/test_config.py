"""Tests for the configuration module."""

import os
import tempfile
from unittest.mock import patch

import pytest

from spot_optimizer.config import SpotOptimizerConfig


class TestSpotOptimizerConfig:
    """Test cases for SpotOptimizerConfig."""

    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = SpotOptimizerConfig()
        
        assert config.cache_ttl == 3600
        assert config.request_timeout == 30
        assert config.max_retries == 3
        assert config.spot_advisor_url == "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"
        assert config.db_path.endswith("spot_advisor_data.db")

    def test_custom_initialization(self):
        """Test configuration with custom values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            
            config = SpotOptimizerConfig(
                db_path=db_path,
                cache_ttl=7200,
                request_timeout=60,
                max_retries=5,
                spot_advisor_url="https://example.com/data.json"
            )
            
            assert config.db_path == db_path
            assert config.cache_ttl == 7200
            assert config.request_timeout == 60
            assert config.max_retries == 5
            assert config.spot_advisor_url == "https://example.com/data.json"

    @patch.dict(os.environ, {
        'SPOT_OPTIMIZER_CACHE_TTL': '1800',
        'SPOT_OPTIMIZER_REQUEST_TIMEOUT': '45',
        'SPOT_OPTIMIZER_MAX_RETRIES': '2',
        'SPOT_OPTIMIZER_URL': 'https://custom.com/data.json'
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = SpotOptimizerConfig.from_env()
        
        assert config.cache_ttl == 1800
        assert config.request_timeout == 45
        assert config.max_retries == 2
        assert config.spot_advisor_url == "https://custom.com/data.json"

    @patch.dict(os.environ, {
        'SPOT_OPTIMIZER_DB_PATH': '/custom/path/db.sqlite'
    })
    def test_from_env_with_db_path(self):
        """Test configuration from environment with custom DB path."""
        config = SpotOptimizerConfig.from_env()
        
        assert config.db_path == '/custom/path/db.sqlite'

    def test_from_env_with_defaults(self):
        """Test configuration from environment with default values."""
        # Clear any existing environment variables
        env_vars = [
            'SPOT_OPTIMIZER_DB_PATH',
            'SPOT_OPTIMIZER_CACHE_TTL',
            'SPOT_OPTIMIZER_REQUEST_TIMEOUT',
            'SPOT_OPTIMIZER_MAX_RETRIES',
            'SPOT_OPTIMIZER_URL'
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            config = SpotOptimizerConfig.from_env()
            
            assert config.cache_ttl == 3600
            assert config.request_timeout == 30
            assert config.max_retries == 3
            assert config.spot_advisor_url == "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"

    def test_get_default_db_path(self):
        """Test default database path generation."""
        db_path = SpotOptimizerConfig._get_default_db_path()
        
        assert db_path.endswith("spot_advisor_data.db")
        assert "spot-optimizer" in db_path
        
        # Verify the directory exists
        assert os.path.exists(os.path.dirname(db_path))