# Tests

This directory contains comprehensive tests for the spot-optimizer package with enhanced robustness and CI integration.

## Test Types

### Unit Tests
- `test_*.py` - Individual component tests
- Run with: `make test` or `make test-quick`
- Coverage threshold: 94%
- Fast execution, mocked dependencies
- Matrix tested on Python 3.11-3.14

### Integration Tests
- `test_integration.py` - Comprehensive end-to-end testing
- Run with: `make test-integration` or `make test-integration-verbose`
- Tests real AWS API integration with retry logic
- ~3-5 minutes execution time
- Enhanced error handling and fallback configurations

### Performance Tests
- Subset of integration tests focused on performance
- Run with: `make test-performance`
- Memory usage monitoring and timeout protection

## Enhanced Integration Test Coverage

The integration test suite includes 16 comprehensive test categories:

### Core Functionality
- ✅ **Package Structure** - Import validation, CLI availability, singleton pattern
- ✅ **Basic Functionality** - Core optimization with retry logic and fallback configs
- ✅ **Different Modes** - Balanced, Latency, Fault Tolerance modes with robust fallback

### Robustness & Reliability
- ✅ **Resource Scaling** - Tiny to large workloads (1-64 cores, 2-256GB RAM)
- ✅ **Multiple Regions** - 5 AWS regions with intelligent fallback
- ✅ **Edge Cases** - Minimum resources, odd requirements, filter combinations
- ✅ **Result Consistency** - Multiple calls return consistent results
- ✅ **Network Resilience** - Handles network issues and API rate limits

### Performance & Efficiency
- ✅ **Performance Characteristics** - Response time validation with timeout protection
- ✅ **Memory Efficiency** - Memory usage monitoring and leak detection
- ✅ **Concurrent Access** - Thread safety and singleton behavior validation
- ✅ **Timeout Handling** - Graceful handling of long-running operations

### Advanced Testing
- ✅ **Data Integrity** - Result validation and format verification
- ✅ **Environment Variables** - Debug mode and configuration testing
- ✅ **Error Handling** - Invalid inputs, boundary conditions, graceful failures
- ✅ **Filtering Options** - SSD-only, ARM/x86, instance families with fallback

## Test Execution Options

### Make Commands
```bash
# Quick unit tests only
make test-quick

# Unit tests only
make test-unit

# All tests (unit + integration)
make test

# Unit tests with coverage
make coverage

# Integration tests (standard)
make test-integration

# Integration tests (verbose CI mode)
make test-integration-verbose

# Performance-focused tests
make test-performance
```



## CI/CD Integration

### GitHub Actions Workflow
- **Unit Tests**: Matrix testing on Python 3.11-3.14
- **Integration Tests**: Multi-configuration testing with timeout protection
- **Coverage Reports**: Automated coverage reporting with 94% threshold
- **Scheduled Tests**: Daily integration tests to catch AWS API changes
- **Security Scanning**: Dependency and security vulnerability scanning
- **Build Verification**: Package build and installation verification

### Enhanced Features
- **Retry Logic**: Automatic retry with exponential backoff for flaky tests
- **Fallback Configurations**: Multiple test configurations to handle AWS availability
- **Timeout Protection**: Prevents hanging tests in CI environments
- **Detailed Reporting**: Enhanced test result summaries and failure analysis
- **Artifact Collection**: Test results, logs, and coverage reports preserved

## Expected Output (Enhanced)

```
🚀 Starting Comprehensive Integration Tests for Spot Optimizer
======================================================================

🧪 Testing package structure...
✅ Package structure test passed!

🧪 Testing basic functionality...
✅ Basic functionality test passed with config: {'cores': 2, 'memory': 8, 'region': 'us-west-2'}

🧪 Testing different optimization modes...
✅ Optimization modes test passed! (3/3 modes working)

🧪 Testing performance characteristics...
✅ Initial response time acceptable: 2.34s
✅ Cached response time: 0.12s
✅ Memory usage acceptable: 45.2MB

🧪 Testing timeout handling...
✅ Operation completed within timeout

🧪 Testing memory efficiency...
✅ Memory growth acceptable: 12.3MB

======================================================================
📊 Test Results Summary
   Total time: 45.67s
   Tests run: 16
   Passed: 16
   Failed: 0
   Success rate: 100.0%

🎉 All integration tests passed!
```

## Troubleshooting

### Common Issues
- **"No suitable instances found"**: Normal in some regions/configurations, tests have fallback logic
- **Network timeouts**: Tests include retry logic and timeout protection
- **Memory issues**: Performance tests monitor and validate memory usage
- **CI failures**: Detailed logging available with `CI=true` environment variable

### Debug Mode
```bash
# Enable debug output
export SPOT_OPTIMIZER_DEBUG=1
export CI=true
make test-integration-verbose
```

The enhanced integration test suite provides robust validation of the spot-optimizer package with intelligent error handling, comprehensive coverage, and CI/CD integration.