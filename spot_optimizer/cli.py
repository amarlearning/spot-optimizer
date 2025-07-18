import json
import argparse
import sys
from typing import List, Optional

from spot_optimizer import optimize
from spot_optimizer.exceptions import SpotOptimizerError
from spot_optimizer.logging_config import get_logger

logger = get_logger(__name__)


def _handle_error(e: SpotOptimizerError) -> None:
    """Log and print error message, then exit."""
    print(f"{e.__class__.__name__}: {e}", file=sys.stderr)

    if e.suggestions:
        print("Suggestions:", file=sys.stderr)
        suggestions = (
            e.suggestions if isinstance(e.suggestions, list) else [e.suggestions]
        )
        for suggestion in suggestions:
            print(f"  - {suggestion}", file=sys.stderr)

    sys.exit(1)


def validate_positive_int(value: str, param_name: str) -> int:
    """Validate that the value is a positive integer.
    :param value: The string value to validate
    :param param_name: Name of the parameter for error messages
    :return: The validated positive integer
    :raises: ArgumentTypeError: If value is not a positive integer
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
    """Parse command line arguments.
    :param args: List of arguments to parse. Defaults to sys.argv[1:] if None.
    :return: Parsed command line arguments
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
        _handle_error(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
