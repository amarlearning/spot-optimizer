#!/usr/bin/env python3
"""
Test script to verify custom exception implementation in spot-optimizer.
"""
import sys
import os

# Add the current directory to the path so we can import spot_optimizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_validator_exceptions():
    """Test custom exceptions in validators module."""
    print("Testing validator exceptions...")

    from spot_optimizer.validators import validate_cores, validate_memory, validate_mode
    from spot_optimizer.exceptions import ValidationError

    # Test cores validation
    try:
        validate_cores(-1)
        print(
            "❌ FAILED: validate_cores should raise ValidationError for negative cores"
        )
    except ValidationError as e:
        print(f"✅ PASSED: validate_cores raises ValidationError: {e.error_code}")
        print(f"   Message: {e}")
        print(f"   Suggestions: {e.suggestions}")
    except Exception as e:
        print(
            f"❌ FAILED: validate_cores raised unexpected exception: {type(e).__name__}: {e}"
        )

    # Test memory validation
    try:
        validate_memory(0)
        print("❌ FAILED: validate_memory should raise ValidationError for zero memory")
    except ValidationError as e:
        print(f"✅ PASSED: validate_memory raises ValidationError: {e.error_code}")
        print(f"   Message: {e}")
    except Exception as e:
        print(
            f"❌ FAILED: validate_memory raised unexpected exception: {type(e).__name__}: {e}"
        )

    # Test mode validation
    try:
        validate_mode("invalid_mode")
        print("❌ FAILED: validate_mode should raise ValidationError for invalid mode")
    except ValidationError as e:
        print(f"✅ PASSED: validate_mode raises ValidationError: {e.error_code}")
        print(f"   Message: {e}")
    except Exception as e:
        print(
            f"❌ FAILED: validate_mode raised unexpected exception: {type(e).__name__}: {e}"
        )

    print()


def test_aws_cache_exceptions():
    """Test custom exceptions in AWS cache module."""
    print("Testing AWS cache exceptions...")

    from spot_optimizer.spot_advisor_data.aws_spot_advisor_cache import (
        AwsSpotAdvisorData,
    )
    from spot_optimizer.exceptions import ValidationError

    # Test URL validation
    try:
        AwsSpotAdvisorData("invalid_url")
        print(
            "❌ FAILED: AwsSpotAdvisorData should raise ValidationError for invalid URL"
        )
    except ValidationError as e:
        print(f"✅ PASSED: AwsSpotAdvisorData raises ValidationError: {e.error_code}")
        print(f"   Message: {e}")
    except Exception as e:
        print(
            f"❌ FAILED: AwsSpotAdvisorData raised unexpected exception: {type(e).__name__}: {e}"
        )

    print()


def test_exception_hierarchy():
    """Test exception hierarchy and inheritance."""
    print("Testing exception hierarchy...")

    from spot_optimizer.exceptions import (
        SpotOptimizerError,
        ValidationError,
        StorageError,
        NetworkError,
        DataError,
        OptimizationError,
        ConfigurationError,
        ErrorCode,
    )

    # Test inheritance
    test_cases = [
        (ValidationError, "Test validation error"),
        (StorageError, "Test storage error"),
        (NetworkError, "Test network error"),
        (DataError, "Test data error"),
        (OptimizationError, "Test optimization error"),
        (ConfigurationError, "Test configuration error"),
    ]

    for exception_class, message in test_cases:
        try:
            exc = exception_class(message, error_code=ErrorCode.UNKNOWN)
            assert isinstance(
                exc, SpotOptimizerError
            ), f"{exception_class.__name__} should inherit from SpotOptimizerError"
            assert (
                exc.error_code == ErrorCode.UNKNOWN
            ), f"{exception_class.__name__} should have error_code attribute"
            assert (
                str(exc) == message
            ), f"{exception_class.__name__} should have correct message"
            print(
                f"✅ PASSED: {exception_class.__name__} properly inherits from SpotOptimizerError"
            )
        except Exception as e:
            print(
                f"❌ FAILED: {exception_class.__name__} test failed: {type(e).__name__}: {e}"
            )

    print()


def test_convenience_functions():
    """Test convenience functions for raising exceptions."""
    print("Testing convenience functions...")

    from spot_optimizer.exceptions import (
        raise_validation_error,
        raise_storage_error,
        raise_network_error,
        raise_data_error,
        raise_optimization_error,
        raise_configuration_error,
        ValidationError,
        StorageError,
        NetworkError,
        DataError,
        OptimizationError,
        ConfigurationError,
        ErrorCode,
    )

    test_cases = [
        (raise_validation_error, ValidationError),
        (raise_storage_error, StorageError),
        (raise_network_error, NetworkError),
        (raise_data_error, DataError),
        (raise_optimization_error, OptimizationError),
        (raise_configuration_error, ConfigurationError),
    ]

    for func, expected_exception in test_cases:
        try:
            func("Test message", error_code=ErrorCode.UNKNOWN)
            print(
                f"❌ FAILED: {func.__name__} should raise {expected_exception.__name__}"
            )
        except expected_exception as e:
            print(
                f"✅ PASSED: {func.__name__} raises {expected_exception.__name__}: {e.error_code}"
            )
        except Exception as e:
            print(
                f"❌ FAILED: {func.__name__} raised unexpected exception: {type(e).__name__}: {e}"
            )

    print()


def main():
    """Run all tests."""
    print("🧪 Testing Custom Exception Implementation\n")
    print("=" * 50)

    test_exception_hierarchy()
    test_convenience_functions()
    test_validator_exceptions()
    test_aws_cache_exceptions()

    print("=" * 50)
    print("✅ Custom exception testing completed!")
    print(
        "Note: Network tests require actual network connectivity and may fail in isolated environments."
    )


if __name__ == "__main__":
    main()
