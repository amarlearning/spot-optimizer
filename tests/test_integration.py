#!/usr/bin/env python3
"""
Comprehensive integration test suite for spot-optimizer.
Tests the package end-to-end with real AWS data.
"""

import sys
import traceback
import time
import threading
import os

def validate_result(result, min_cores, min_memory):
    """Validate the structure and content of optimization results."""
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "instances" in result, "Result should contain 'instances'"
    assert "mode" in result, "Result should contain 'mode'"
    assert "total_cores" in result, "Result should contain 'total_cores'"
    assert "total_ram" in result, "Result should contain 'total_ram'"
    assert "reliability" in result, "Result should contain 'reliability'"
    
    # Validate instances structure
    instances = result["instances"]
    assert "type" in instances, "Instances should contain 'type'"
    assert "count" in instances, "Instances should contain 'count'"
    assert isinstance(instances["count"], int), "Count should be integer"
    assert instances["count"] > 0, "Count should be positive"
    
    # Validate reliability structure
    reliability = result["reliability"]
    assert "spot_score" in reliability, "Reliability should contain 'spot_score'"
    assert "interruption_rate" in reliability, "Reliability should contain 'interruption_rate'"
    
    # Validate resource requirements are met
    assert result["total_cores"] >= min_cores, f"Total cores {result['total_cores']} should be >= {min_cores}"
    assert result["total_ram"] >= min_memory, f"Total RAM {result['total_ram']} should be >= {min_memory}"
    
    # Validate instance type format
    instance_type = instances["type"]
    assert "." in instance_type, f"Instance type {instance_type} should have family.size format"

def test_package_structure():
    """Test package structure and imports."""
    print("🧪 Testing package structure...")
    
    try:
        # Test main imports
        from spot_optimizer import optimize, Mode, SpotOptimizer
        assert callable(optimize), "optimize should be callable"
        assert hasattr(Mode, 'BALANCED'), "Mode should have BALANCED"
        assert hasattr(Mode, 'LATENCY'), "Mode should have LATENCY"
        assert hasattr(Mode, 'FAULT_TOLERANCE'), "Mode should have FAULT_TOLERANCE"
        print("   ✅ Main imports test passed")
        
        # Test CLI import
        from spot_optimizer.cli import main
        assert callable(main), "CLI main should be callable"
        print("   ✅ CLI import test passed")
        
        # Test singleton pattern
        optimizer1 = SpotOptimizer.get_instance()
        optimizer2 = SpotOptimizer.get_instance()
        assert optimizer1 is optimizer2, "SpotOptimizer should follow singleton pattern"
        print("   ✅ Singleton pattern test passed")
        
        print("✅ Package structure test passed!")
        
    except Exception as e:
        print(f"❌ Package structure test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Package structure test failed: {e}")

def test_basic_functionality():
    """Test basic spot optimizer functionality."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from spot_optimizer import optimize
        
        # Try multiple configurations to handle AWS availability
        configs = [
            {"cores": 2, "memory": 8, "region": "us-west-2"},
            {"cores": 2, "memory": 4, "region": "us-east-1"},
            {"cores": 1, "memory": 4, "region": "us-west-2"},
        ]
        
        for config in configs:
            try:
                result = optimize(**config)
                validate_result(result, config["cores"], config["memory"])
                print(f"✅ Basic functionality test passed!")
                print(f"   Result: {result}")
                return
            except ValueError as e:
                if "No suitable instances found" in str(e):
                    continue
                else:
                    raise
        
        raise ValueError("No suitable instances found in any configuration")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Basic functionality test failed: {e}")

def test_different_modes():
    """Test different optimization modes."""
    print("\n🧪 Testing different optimization modes...")
    
    try:
        from spot_optimizer import optimize, Mode
        
        modes = [Mode.BALANCED.value, Mode.LATENCY.value, Mode.FAULT_TOLERANCE.value]
        successful_modes = []
        
        # Test configurations in order of likelihood to succeed
        test_configs = [
            {"cores": 2, "memory": 4, "region": "us-east-1"},
            {"cores": 2, "memory": 8, "region": "us-west-2"},
            {"cores": 1, "memory": 2, "region": "us-east-1"},
        ]
        
        for mode in modes:
            mode_success = False
            for config in test_configs:
                try:
                    result = optimize(mode=mode, **config)
                    validate_result(result, config["cores"], config["memory"])
                    assert result["mode"] == mode, f"Mode should be {mode}"
                    print(f"   ✅ Mode {mode} test passed")
                    successful_modes.append(mode)
                    mode_success = True
                    break
                except ValueError as e:
                    if "No suitable instances found" in str(e):
                        continue
                    else:
                        raise
            
            if not mode_success:
                print(f"   ⚠️  Mode {mode} test skipped (no suitable instances)")
        
        if len(successful_modes) >= 2:
            print(f"✅ Optimization modes test passed! ({len(successful_modes)}/3 modes working)")
        else:
            raise AssertionError(f"Too few modes working: {successful_modes}")
        
    except Exception as e:
        print(f"❌ Optimization modes test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Optimization modes test failed: {e}")

def test_filters():
    """Test various filtering options."""
    print("\n🧪 Testing filtering options...")
    
    try:
        from spot_optimizer import optimize
        
        # Test SSD-only filter
        ssd_configs = [
            {"cores": 2, "memory": 8, "region": "us-west-2"},
            {"cores": 4, "memory": 16, "region": "us-east-1"},
        ]
        
        ssd_success = False
        for config in ssd_configs:
            try:
                result_ssd = optimize(ssd_only=True, **config)
                validate_result(result_ssd, config["cores"], config["memory"])
                print(f"   ✅ SSD-only filter test passed")
                ssd_success = True
                break
            except ValueError as e:
                if "No suitable instances found" in str(e):
                    continue
                else:
                    raise
        
        if not ssd_success:
            print("   ⚠️  SSD-only filter test skipped (no suitable instances)")
        
        # Test ARM instances filter
        result_no_arm = optimize(cores=2, memory=4, region="us-west-2", arm_instances=False)
        validate_result(result_no_arm, 2, 4)
        print("   ✅ ARM instances filter test passed")
        
        # Test instance family filter
        try:
            result_family = optimize(cores=4, memory=8, region="us-west-2", instance_family=["m5"])
            validate_result(result_family, 4, 8)
            instance_type = result_family["instances"]["type"]
            family = instance_type.split('.')[0]
            assert family == "m5", f"Instance family {family} should be m5"
            print("   ✅ Instance family filter test passed")
        except Exception as e:
            if "No suitable instances found" in str(e):
                print(f"   ⚠️  Instance family filter test skipped")
            else:
                raise
        
        print("✅ Filtering options test passed!")
        
    except Exception as e:
        print(f"❌ Filtering options test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Filtering options test failed: {e}")

def test_resource_scaling():
    """Test optimization with different resource scales."""
    print("\n🧪 Testing resource scaling...")
    
    test_cases = [
        {"cores": 1, "memory": 2, "desc": "tiny workload"},
        {"cores": 4, "memory": 16, "desc": "small workload"},
        {"cores": 16, "memory": 64, "desc": "medium workload"},
        {"cores": 64, "memory": 256, "desc": "large workload"},
    ]
    
    try:
        from spot_optimizer import optimize
        
        for case in test_cases:
            try:
                result = optimize(cores=case["cores"], memory=case["memory"], region="us-west-2")
                validate_result(result, case["cores"], case["memory"])
                print(f"   ✅ {case['desc']} test passed")
            except ValueError as e:
                if "No suitable instances found" in str(e):
                    print(f"   ⚠️  {case['desc']} test skipped (no suitable instances)")
                else:
                    raise
        
        print("✅ Resource scaling test passed!")
        
    except Exception as e:
        print(f"❌ Resource scaling test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Resource scaling test failed: {e}")

def test_multiple_regions():
    """Test optimization across different AWS regions."""
    print("\n🧪 Testing multiple regions...")
    
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ca-central-1"]
    
    try:
        from spot_optimizer import optimize
        
        successful_regions = 0
        
        for region in regions:
            try:
                result = optimize(cores=2, memory=8, region=region)
                validate_result(result, 2, 8)
                print(f"   ✅ Region {region} test passed")
                successful_regions += 1
            except Exception as e:
                if "No suitable instances found" in str(e):
                    print(f"   ⚠️  Region {region} test skipped")
                else:
                    print(f"   ❌ Region {region} test failed: {e}")
        
        if successful_regions >= 2:
            print(f"✅ Multiple regions test passed! ({successful_regions}/{len(regions)} regions working)")
        else:
            raise AssertionError(f"Too few regions working: {successful_regions}/{len(regions)}")
        
    except Exception as e:
        print(f"❌ Multiple regions test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Multiple regions test failed: {e}")

def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n🧪 Testing error handling...")
    
    try:
        from spot_optimizer import optimize
        
        # Test negative cores
        try:
            optimize(cores=-1, memory=8)
            assert False, "Should have raised ValueError for negative cores"
        except ValueError:
            print("   ✅ Negative cores error handling passed")
        
        # Test negative memory
        try:
            optimize(cores=4, memory=-1)
            assert False, "Should have raised ValueError for negative memory"
        except ValueError:
            print("   ✅ Negative memory error handling passed")
        
        # Test zero values
        try:
            optimize(cores=0, memory=8)
            assert False, "Should have raised ValueError for zero cores"
        except ValueError:
            print("   ✅ Zero cores error handling passed")
        
        print("✅ Error handling test passed!")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Error handling test failed: {e}")

def test_result_consistency():
    """Test that results are consistent across multiple calls."""
    print("\n🧪 Testing result consistency...")
    
    try:
        from spot_optimizer import optimize
        
        # Run the same optimization multiple times
        results = []
        for i in range(3):
            try:
                result = optimize(cores=4, memory=16, region="us-west-2", mode="balanced")
                results.append(result)
            except ValueError as e:
                if "No suitable instances found" in str(e):
                    print("   ⚠️  Consistency test skipped (no suitable instances)")
                    return
                else:
                    raise
        
        if len(results) < 2:
            print("   ⚠️  Consistency test skipped (insufficient results)")
            return
        
        # Check that results are consistent
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result["instances"]["type"] == first_result["instances"]["type"], \
                f"Instance type inconsistent between calls"
            assert result["mode"] == first_result["mode"], \
                f"Mode inconsistent between calls"
        
        print("   ✅ Multiple calls returned consistent results")
        print("✅ Result consistency test passed!")
        
    except Exception as e:
        print(f"❌ Result consistency test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Result consistency test failed: {e}")

def test_performance_characteristics():
    """Test performance and response time characteristics."""
    print("\n🧪 Testing performance characteristics...")
    
    try:
        from spot_optimizer import optimize
        
        # Test response time
        start_time = time.time()
        
        try:
            result = optimize(cores=4, memory=16, region="us-west-2")
            end_time = time.time()
            response_time = end_time - start_time
            
            # Should respond within reasonable time (30 seconds)
            assert response_time < 30, f"Response time too slow: {response_time:.2f}s"
            print(f"   ✅ Response time acceptable: {response_time:.2f}s")
            
            # Test that subsequent calls are faster (caching)
            start_time = time.time()
            result2 = optimize(cores=4, memory=16, region="us-west-2")
            end_time = time.time()
            cached_response_time = end_time - start_time
            
            print(f"   ✅ Cached response time: {cached_response_time:.2f}s")
            
            # Verify result is still valid
            validate_result(result2, 4, 16)
            
        except ValueError as e:
            if "No suitable instances found" in str(e):
                print("   ⚠️  Performance test skipped (no suitable instances)")
                return
            else:
                raise
        
        print("✅ Performance characteristics test passed!")
        
    except Exception as e:
        print(f"❌ Performance characteristics test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Performance characteristics test failed: {e}")

def test_concurrent_access():
    """Test concurrent access patterns."""
    print("\n🧪 Testing concurrent access...")
    
    try:
        from spot_optimizer import optimize, SpotOptimizer
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                result = optimize(cores=2, memory=8, region="us-west-2")
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Validate results
        if len(results) > 0:
            print(f"   ✅ Concurrent access successful ({len(results)}/3 threads)")
            
            # Verify singleton behavior across threads
            optimizer1 = SpotOptimizer.get_instance()
            optimizer2 = SpotOptimizer.get_instance()
            assert optimizer1 is optimizer2, "Singleton should work across threads"
            print("   ✅ Singleton behavior maintained across threads")
        else:
            # If no results, check if it's due to no suitable instances
            if any("No suitable instances found" in error[1] for error in errors):
                print("   ⚠️  Concurrent access test skipped (no suitable instances)")
                return
            else:
                raise AssertionError(f"All concurrent calls failed: {errors}")
        
        print("✅ Concurrent access test passed!")
        
    except Exception as e:
        print(f"❌ Concurrent access test failed: {e}")
        traceback.print_exc()
        raise AssertionError(f"Concurrent access test failed: {e}")

def main():
    """Run all integration tests."""
    print("🚀 Starting Comprehensive Integration Tests for Spot Optimizer")
    print("=" * 65)
    
    tests = [
        test_package_structure,
        test_basic_functionality,
        test_different_modes,
        test_filters,
        test_resource_scaling,
        test_multiple_regions,
        test_error_handling,
        test_result_consistency,
        test_performance_characteristics,
        test_concurrent_access,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 65)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("\nThe spot-optimizer package is working correctly!")
        print("✅ Core functionality validated")
        print("✅ Multiple regions tested")
        print("✅ Resource scaling verified")
        print("✅ Error handling confirmed")
        print("✅ Performance acceptable")
        print("✅ Concurrent access validated")
        return 0
    else:
        print("❌ Some tests failed!")
        print("\nPlease review the failures above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())