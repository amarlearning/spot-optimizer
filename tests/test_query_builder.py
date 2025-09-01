"""Tests for the query builder module."""

import pytest

from spot_optimizer.query_builder import OptimizationQueryBuilder


class TestOptimizationQueryBuilder:
    """Test cases for OptimizationQueryBuilder."""

    def test_build_optimization_query_basic(self):
        """Test basic query building without filters."""
        query = OptimizationQueryBuilder.build_optimization_query()
        
        assert "WITH ranked_instances AS" in query
        assert "SELECT" in query
        assert "FROM instance_types i" in query
        assert "JOIN spot_advisor s" in query
        assert "ORDER BY" in query
        assert "LIMIT 1" in query

    def test_build_optimization_query_with_ssd_filter(self):
        """Test query building with SSD filter."""
        query = OptimizationQueryBuilder.build_optimization_query(ssd_only=True)
        
        assert "AND i.storage_type = 'instance'" in query

    def test_build_optimization_query_without_arm(self):
        """Test query building without ARM instances."""
        query = OptimizationQueryBuilder.build_optimization_query(arm_instances=False)
        
        assert "AND i.architecture != 'arm64'" in query

    def test_build_optimization_query_with_instance_family(self):
        """Test query building with instance family filter."""
        query = OptimizationQueryBuilder.build_optimization_query(
            instance_family=["m5", "c5"]
        )
        
        assert "AND i.instance_family IN (?,?)" in query

    def test_build_optimization_query_all_filters(self):
        """Test query building with all filters enabled."""
        query = OptimizationQueryBuilder.build_optimization_query(
            ssd_only=True,
            arm_instances=False,
            instance_family=["m6i", "r6i", "c6i"]
        )
        
        assert "AND i.storage_type = 'instance'" in query
        assert "AND i.architecture != 'arm64'" in query
        assert "AND i.instance_family IN (?,?,?)" in query

    def test_build_query_parameters_basic(self):
        """Test basic parameter building."""
        params = OptimizationQueryBuilder.build_query_parameters(
            cores=8,
            memory=32,
            region="us-west-2",
            instance_family=None,
            min_instances=1,
            max_instances=10
        )
        
        expected_params = [
            8, 32, "us-west-2",  # Basic params
            8, 8,                # CPU waste calculation
            32, 32,              # Memory waste calculation
            8, 32,               # Minimum resource requirements
            1, 10                # Instance bounds
        ]
        
        assert params == expected_params

    def test_build_query_parameters_with_instance_family(self):
        """Test parameter building with instance family."""
        params = OptimizationQueryBuilder.build_query_parameters(
            cores=4,
            memory=16,
            region="us-east-1",
            instance_family=["m5", "c5"],
            min_instances=2,
            max_instances=8
        )
        
        expected_params = [
            4, 16, "us-east-1",  # Basic params
            "m5", "c5",          # Instance family params
            4, 4,                # CPU waste calculation
            16, 16,              # Memory waste calculation
            4, 16,               # Minimum resource requirements
            2, 8                 # Instance bounds
        ]
        
        assert params == expected_params

    def test_build_error_message_params_basic(self):
        """Test basic error message building."""
        error_msg = OptimizationQueryBuilder.build_error_message_params(
            cores=8,
            memory=32,
            region="us-west-2",
            mode="balanced"
        )
        
        expected = "No suitable instances found matching for cpu = 8 and memory = 32 and region = us-west-2 and mode = balanced"
        assert error_msg == expected

    def test_build_error_message_params_with_all_options(self):
        """Test error message building with all options."""
        error_msg = OptimizationQueryBuilder.build_error_message_params(
            cores=16,
            memory=64,
            region="eu-west-1",
            mode="latency",
            instance_family=["m6i", "r6i"],
            emr_version="6.10.0",
            ssd_only=True,
            arm_instances=False
        )
        
        expected_parts = [
            "cpu = 16",
            "memory = 64",
            "region = eu-west-1",
            "mode = latency",
            "instance_family = ['m6i', 'r6i']",
            "emr_version = 6.10.0",
            "ssd_only = True",
            "arm_instances = False"
        ]
        
        for part in expected_parts:
            assert part in error_msg

    def test_build_error_message_params_partial_options(self):
        """Test error message building with some options."""
        error_msg = OptimizationQueryBuilder.build_error_message_params(
            cores=4,
            memory=8,
            region="ap-southeast-1",
            mode="fault_tolerance",
            ssd_only=True
        )
        
        expected_parts = [
            "cpu = 4",
            "memory = 8",
            "region = ap-southeast-1",
            "mode = fault_tolerance",
            "ssd_only = True"
        ]
        
        for part in expected_parts:
            assert part in error_msg
        
        # These should not be in the message
        assert "instance_family" not in error_msg
        assert "emr_version" not in error_msg
        assert "arm_instances = False" not in error_msg