import json
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from spot_optimizer import SpotOptimizer
from spot_optimizer.spot_advisor_engine import ensure_fresh_data

def analyze_failure_patterns(results: List[Dict[str, Any]]):
    """Analyze patterns in failed queries."""
    failed_queries = [r for r in results if not r["success"]]
    total_failures = len(failed_queries)
    
    print("\nFailure Pattern Analysis:")
    print(f"Total Failed Queries: {total_failures}")
    
    # Analyze by resource requirements
    core_ranges = [(0, 16), (17, 64), (65, 256), (257, float('inf'))]
    memory_ranges = [(0, 32), (33, 128), (129, 512), (513, float('inf'))]
    
    print("\n1. Resource Requirement Patterns:")
    for core_range in core_ranges:
        for mem_range in memory_ranges:
            matching_failures = [
                q for q in failed_queries 
                if core_range[0] <= q["params"]["cores"] <= core_range[1]
                and mem_range[0] <= q["params"]["memory"] <= mem_range[1]
            ]
            if matching_failures:
                percentage = (len(matching_failures) / total_failures) * 100
                print(f"Cores {core_range}, Memory {mem_range}: {len(matching_failures)} failures ({percentage:.1f}%)")
    
    # Analyze by mode
    print("\n2. Failure Distribution by Mode:")
    mode_failures = {}
    for query in failed_queries:
        mode = query["params"]["mode"]
        mode_failures[mode] = mode_failures.get(mode, 0) + 1
    
    for mode, count in mode_failures.items():
        percentage = (count / total_failures) * 100
        print(f"{mode}: {count} failures ({percentage:.1f}%)")
    
    # Analyze by region
    print("\n3. Regional Failure Distribution:")
    region_failures = {}
    for query in failed_queries:
        region = query["params"]["region"]
        region_failures[region] = region_failures.get(region, 0) + 1
    
    for region, count in sorted(region_failures.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_failures) * 100
        print(f"{region}: {count} failures ({percentage:.1f}%)")
    
    # Analyze specific constraints
    print("\n4. Constraint Analysis:")
    ssd_failures = len([q for q in failed_queries if q["params"]["ssd_only"]])
    non_arm_failures = len([q for q in failed_queries if not q["params"]["arm_instances"]])
    
    print(f"SSD-only requirement: {ssd_failures} failures ({(ssd_failures/total_failures)*100:.1f}%)")
    print(f"Non-ARM requirement: {non_arm_failures} failures ({(non_arm_failures/total_failures)*100:.1f}%)")
    
    # Memory to Core ratio analysis
    print("\n5. Memory/Core Ratio Analysis:")
    ratio_ranges = [(0, 2), (2, 4), (4, 8), (8, float('inf'))]
    
    for r_range in ratio_ranges:
        matching_ratios = [
            q for q in failed_queries 
            if r_range[0] <= (q["params"]["memory"] / q["params"]["cores"]) < r_range[1]
        ]
        if matching_ratios:
            percentage = (len(matching_ratios) / total_failures) * 100
            print(f"Memory/Core ratio {r_range}: {len(matching_ratios)} failures ({percentage:.1f}%)")

    # Find extreme failure cases
    print("\n6. Example Extreme Cases:")
    max_core_failure = max(failed_queries, key=lambda x: x["params"]["cores"])
    max_mem_failure = max(failed_queries, key=lambda x: x["params"]["memory"])
    
    print("Highest core request that failed:")
    print(json.dumps(max_core_failure["params"], indent=2))
    
    print("\nHighest memory request that failed:")
    print(json.dumps(max_mem_failure["params"], indent=2))

class PerformanceTester:
    def __init__(self):
        self.results_dir = Path(__file__).parent.parent / "resources"
        self.combinations = self.load_test_combinations()
        self.optimizer = None

    def load_test_combinations(self) -> List[Dict[str, Any]]:
        """Load test combinations from resources."""
        combo_file = self.results_dir / "test_combinations.json"
        if not combo_file.exists():
            raise FileNotFoundError(
                f"Test combinations file not found at {combo_file}. "
                "Please run generate_test_data.py first."
            )
        
        with open(combo_file) as f:
            data = json.load(f)
        return data["combinations"]

    def prepare_environment(self):
        """Initialize optimizer and ensure fresh cache."""
        print("\nPreparing test environment...")
        print(f"Total test combinations: {len(self.combinations)}")
        
        self.optimizer = SpotOptimizer()
        
        print("Ensuring fresh cache data...")
        start_time = time.time()
        ensure_fresh_data(self.optimizer.spot_advisor, self.optimizer.db)
        prep_time = time.time() - start_time
        print(f"Cache preparation completed in {prep_time:.2f} seconds")

    def run_benchmarks(self):
        """Execute performance tests."""
        if not self.optimizer:
            raise RuntimeError("Environment not prepared. Call prepare_environment() first.")

        results = []
        total = len(self.combinations)
        start_time = datetime.now()
        
        print(f"\nRunning performance tests for {total} combinations...")
        
        for idx, params in enumerate(self.combinations, 1):
            try:
                query_start = time.perf_counter()
                self.optimizer.optimize(**params)
                query_time = time.perf_counter() - query_start
                
                results.append({
                    "params": params,
                    "time": query_time,
                    "success": True
                })
                
            except Exception as e:
                results.append({
                    "params": params,
                    "time": None,
                    "success": False,
                    "error": str(e)
                })
            
            # Progress update
            if idx % 1000 == 0 or idx == total:
                print(f"Progress: {idx}/{total} ({(idx/total)*100:.1f}%)")
        
        total_time = datetime.now() - start_time
        return results, total_time

    def analyze_results(self, results: List[Dict[str, Any]], total_time: timedelta):
        """Generate performance metrics."""
        # Extract successful query times
        query_times = [r["time"] for r in results if r["success"]]
        failed_queries = [r for r in results if not r["success"]]
        
        metrics = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_combinations": len(results),
                "total_time_seconds": total_time.total_seconds()
            },
            "summary": {
                "successful_queries": len(query_times),
                "failed_queries": len(failed_queries),
                "success_rate": f"{(len(query_times)/len(results))*100:.2f}%"
            },
            "timing_stats": {
                "min_seconds": min(query_times) if query_times else None,
                "max_seconds": max(query_times) if query_times else None,
                "mean_seconds": statistics.mean(query_times) if query_times else None,
                "median_seconds": statistics.median(query_times) if query_times else None,
                "stddev_seconds": statistics.stdev(query_times) if len(query_times) > 1 else None,
                "p95_seconds": statistics.quantiles(query_times, n=20)[18] if len(query_times) >= 20 else None
            }
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"performance_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "metrics": metrics,
                "detailed_results": results
            }, f, indent=2)
        
        # Print summary
        print("\nPerformance Test Results:")
        print(f"Total Combinations: {metrics['test_info']['total_combinations']}")
        print(f"Total Time: {metrics['test_info']['total_time_seconds']:.2f} seconds")
        print(f"Success Rate: {metrics['summary']['success_rate']}")
        print("\nQuery Time Statistics (seconds):")
        for key, value in metrics['timing_stats'].items():
            if value is not None:
                print(f"{key}: {value:.4f}")
        
        print(f"\nDetailed results saved to: {results_file}")

def main():
    try:
        tester = PerformanceTester()
        tester.prepare_environment()
        results, total_time = tester.run_benchmarks()
        tester.analyze_results(results, total_time)
        
        analyze_failure_patterns(results)
    except Exception as e:
        print(f"Error during performance testing: {e}")
        raise

if __name__ == "__main__":
    main() 