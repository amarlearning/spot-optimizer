import argparse

from spot_optimizer.spot_instance_optimizer import cluster_optimiser


def main():
    parser = argparse.ArgumentParser(description="Run the spot instance optimizer.")
    parser.add_argument(
        "--cores",
        type=int,
        required=True,
        help="Total number of CPU cores required.",
    )
    parser.add_argument(
        "--memory",
        type=int,
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

    args = parser.parse_args()

    result = cluster_optimiser(
        cores=args.cores,
        memory=args.memory,
        region=args.region,
        ssd_only=args.ssd_only,
        arm_instances=args.arm_instances,
        instance_family=args.instance_family,
        emr_version=args.emr_version,
        mode=args.mode,
    )

    print(f"Spot instance optimization result: {result}")


if __name__ == "__main__":
    main()
