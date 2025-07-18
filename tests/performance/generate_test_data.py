import itertools
import json
from typing import List, Dict, Any
from pathlib import Path


def get_test_parameters() -> Dict[str, List[Any]]:
    """
    Define all parameter combinations for testing.
    """
    return {
        "cores": [8, 16, 32, 64, 128] + list(range(200, 2000, 100)),
        "memory": [16, 32, 64, 128, 256, 512] + list(range(1000, 20000, 750)),
        "region": [
            "ap-northeast-3",
            "ca-central-1",
            "eu-west-2",
            "mx-central-1",
            "af-south-1",
            "il-central-1",
            "ap-northeast-2",
            "eu-west-1",
            "ap-southeast-1",
            "me-central-1",
            "me-south-1",
            "ap-south-2",
            "eu-south-1",
            "us-west-1",
            "eu-north-1",
            "ca-west-1",
            "eu-south-2",
            "eu-west-3",
            "ap-south-1",
            "ap-southeast-3",
            "us-east-2",
            "eu-central-1",
            "ap-southeast-5",
            "us-east-1",
            "ap-northeast-1",
            "ap-southeast-2",
            "ap-southeast-4",
            "ap-southeast-7",
            "eu-central-2",
            "ap-east-1",
            "sa-east-1",
            "us-west-2",
        ],
        "ssd_only": [True, False],
        "arm_instances": [True, False],
        "mode": ["latency", "balanced", "fault_tolerance"],
    }


def get_resource_path(filename: str) -> Path:
    """
    Get the absolute path to the resource file.

    Args:
        filename: Name of the resource file

    Returns:
        Path: Absolute path to the resource file
    """
    # Get the absolute path to the tests directory
    tests_dir = Path(__file__).parent.parent
    resource_dir = tests_dir / "resources"

    # Create resources directory if it doesn't exist
    resource_dir.mkdir(exist_ok=True)

    return resource_dir / filename


def generate_test_combinations(
    params: Dict[str, List[Any]], limit: int = None
) -> List[Dict[str, Any]]:
    """
    Generate test combinations from parameters.

    Args:
        params: Dictionary of parameters and their possible values
        limit: Optional limit on number of combinations to generate

    Returns:
        List of dictionaries containing parameter combinations
    """
    # Get all possible combinations
    keys = params.keys()
    values = params.values()

    default_keys = ["cores", "memory"]
    default_values = [params[key] for key in default_keys if key in params]

    combinations = itertools.product(*values)
    default_combinations = itertools.product(*default_values)

    # Convert combinations to list of dictionaries
    test_cases_extended = [dict(zip(keys, combo)) for combo in combinations]

    # Apply reasonable filters
    filtered_cases_extended = [
        case for case in test_cases_extended if is_valid_combination(case)
    ]

    test_cases_default = [
        dict(zip(default_keys, combo)) for combo in default_combinations
    ]

    filtered_cases_default = [
        case for case in test_cases_default if is_valid_combination(case)
    ]

    filtered_cases = filtered_cases_default + filtered_cases_extended
    if limit:
        filtered_cases = filtered_cases[:limit]

    return filtered_cases


def is_valid_combination(case: Dict[str, Any]) -> bool:
    """
    Check if a parameter combination is valid/reasonable.

    Args:
        case: Dictionary containing a parameter combination

    Returns:
        bool: True if combination is valid
    """
    # Memory should be proportional to cores (within reason)
    min_mem_per_core = 2  # GB
    max_mem_per_core = 8  # GB
    mem_per_core = case["memory"] / case["cores"]

    if not (min_mem_per_core <= mem_per_core <= max_mem_per_core):
        return False

    return True


def save_test_data(
    combinations: List[Dict[str, Any]], filename: str = "test_combinations.json"
):
    """
    Save test combinations to a JSON file.

    Args:
        combinations: List of parameter combinations
        filename: Output filename
    """
    output_path = get_resource_path(filename)
    with open(output_path, "w") as f:
        json.dump(
            {"total_combinations": len(combinations), "combinations": combinations},
            f,
            indent=2,
        )

    print(f"Test data saved to: {output_path}")


def main():
    """Generate and save test combinations."""
    params = get_test_parameters()

    # Generate combinations
    combinations = generate_test_combinations(params)

    # Print statistics
    print(f"Generated {len(combinations)} valid test combinations")

    # Save to file
    save_test_data(combinations)


if __name__ == "__main__":
    main()
