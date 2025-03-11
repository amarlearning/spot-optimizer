import json
import argparse

from spot_optimizer import optimize


def validate_positive_int(value: str, param_name: str) -> int:
    """
    Validate that the value is a positive integer.
    
    Args:
        value: The string value to validate
        param_name: Name of the parameter for error messages
    
    Returns:
        int: The validated positive integer
        
    Raises:
        ArgumentTypeError: If value is not a positive integer
    """
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(
                f"{param_name} must be greater than 0, got {ivalue}"
            )
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{param_name} must be an integer, got {value}"
        )


def parse_args(args=None):
    """
    Parse command line arguments.
    
    Args:
        args: List of arguments to parse. Defaults to sys.argv[1:] if None.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Run the spot instance optimizer.")
    parser.add_argument(
        "--cores",
        type=lambda x: validate_positive_int(x, "cores"),
        required=True,
        help="Total number of CPU cores required.",
    )
    parser.add_argument(
        "--memory",
        type=lambda x: validate_positive_int(x, "memory"),
        required=True,
        help="Total amount of RAM required (in GB).",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-west-2",
        help="AWS region to find instances in.",
    )
    parser.add_argument(
        "--ssd-only",
        action="store_true",
        help="Filter for SSD-backed instances.",
    )
    parser.add_argument(
        "--arm-instances",
        action="store_true",
        help="Include ARM-based instances if True.",
    )
    parser.add_argument(
        "--instance-family",
        type=str,
        nargs="+",
        help="Filter by instance family (e.g., 'm5', 'c6g', etc.).",
    )
    parser.add_argument(
        "--emr-version",
        type=str,
        help="Optional EMR version for EMR workloads (e.g., '6.10.0').",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="balanced",
        choices=["latency", "fault_tolerance", "balanced"],
        help='Optimization mode: "latency", "fault_tolerance", or "balanced".',
    )

    return parser.parse_args(args)


def main():
    """Main entry point for the CLI."""
    args = parse_args()

    result = optimize(
        cores=args.cores,
        memory=args.memory,
        region=args.region,
        ssd_only=args.ssd_only,
        arm_instances=args.arm_instances,
        instance_family=args.instance_family,
        emr_version=args.emr_version,
        mode=args.mode,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
