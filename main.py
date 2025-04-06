import argparse
import sys

from models import SpeedTestConfig
from speed_tester import SpeedTester
from utils import format_output, setup_logging, validate_config


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the speed test application.

    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Internet Speed Test Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--url",
        default="https://speed.cloudflare.com/__down",
        help="URL of the speed test server",
    )

    parser.add_argument(
        "--download-size", type=int, default=10, help="Size of download test in MB"
    )

    parser.add_argument(
        "--upload-size", type=int, default=5, help="Size of upload test in MB"
    )

    parser.add_argument(
        "--ping-count",
        type=int,
        default=10,
        help="Number of ping measurements for latency test",
    )

    parser.add_argument(
        "--jitter-samples",
        type=int,
        default=20,
        help="Number of samples for jitter measurement",
    )

    parser.add_argument(
        "--output",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for network operations in seconds",
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the speed test application.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    logger = setup_logging(verbose=args.verbose)

    try:
        # Create and validate configuration
        config = SpeedTestConfig(
            url=args.url,
            download_size_mb=args.download_size,
            upload_size_mb=args.upload_size,
            ping_count=args.ping_count,
            jitter_samples=args.jitter_samples,
            timeout_seconds=args.timeout,
        )

        # Validate configuration
        if not validate_config(config):
            logger.error("Invalid configuration provided")
            return 1

        # Create speed tester instance
        speed_tester = SpeedTester(config)

        # Run the tests
        logger.info("Starting speed tests...")
        result = speed_tester.run_all_tests()

        # Format and output results
        output = format_output(result, output_format=args.output)
        print(output)

        return 0

    except KeyboardInterrupt:
        logger.info("Speed test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        if args.verbose:
            logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
