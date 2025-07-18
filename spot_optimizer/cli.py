import json
import argparse
import sys
from typing import List, Optional

from spot_optimizer import optimize
from spot_optimizer.exceptions import SpotOptimizerError
from spot_optimizer.logging_config import get_logger

logger = get_logger(__name__)


def _handle_error(e: SpotOptimizerError, exit_code: int) -> None:
    """Log and print error message, then exit."""
    logger.error("Error: %s", e, exc_info=True)
    print(f"Error: {e.message}", file=sys.stderr)
    if e.suggestions:
        print("Suggestions:", file=sys.stderr)
        for suggestion in e.suggestions:
            print(f"  - {suggestion}", file=sys.stderr)
    sys.exit(exit_code)


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


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
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


def main() -> None:
    """Main entry point for the CLI."""
    try:
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
    except SpotOptimizerError as e:
        _handle_error(e, 1)
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        print(f"Unexpected error: {e}", file=sys.stderr)
        print(
            "This is likely a bug. Please report it with the full error details.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
