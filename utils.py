import csv
import io
import json
import logging

from models import SpeedTestConfig, SpeedTestResult


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        verbose (bool): Whether to enable verbose (DEBUG) logging

    Returns:
        logging.Logger: Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get logger for this module
    logger = logging.getLogger("speedtest")

    # Add handler to suppress library logging unless in verbose mode
    if not verbose:
        for logger_name in ["urllib3", "requests"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    return logger


def validate_config(config: SpeedTestConfig) -> bool:
    """
    Validate the speed test configuration.

    Args:
        config (SpeedTestConfig): Configuration to validate

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    # Additional validation beyond what Pydantic provides
    if config.download_size_mb > 100:
        logging.warning(
            f"Large download size ({config.download_size_mb} MB) may cause timeouts"
        )

    if config.upload_size_mb > 50:
        logging.warning(
            f"Large upload size ({config.upload_size_mb} MB) may cause timeouts"
        )

    if config.timeout_seconds < 5:
        logging.warning("Timeout is very short and may cause tests to fail prematurely")

    # All basic validation is handled by Pydantic, so we just return True
    return True


def format_text_output(result: SpeedTestResult) -> str:
    """
    Format test results as human-readable text.

    Args:
        result (SpeedTestResult): Speed test results to format

    Returns:
        str: Formatted output string
    """
    output = []
    output.append("=== INTERNET SPEED TEST RESULTS ===")
    output.append(f"Timestamp: {result.formatted_timestamp}")
    output.append("")

    if result.ping:
        output.append("PING (LATENCY)")
        output.append(f"  Min: {result.ping.min_ms:.2f} ms")
        output.append(f"  Avg: {result.ping.avg_ms:.2f} ms")
        output.append(f"  Max: {result.ping.max_ms:.2f} ms")
        output.append(
            f"  Samples: {result.ping.samples}/{result.ping.samples + result.ping.failed}"
        )
        output.append(f"  Success Rate: {result.ping.success_rate_percent:.1f}%")
        output.append("")

    if result.jitter:
        output.append("JITTER (STABILITY)")
        output.append(f"  Avg Jitter: {result.jitter.avg_jitter_ms:.2f} ms")
        output.append(f"  Min Jitter: {result.jitter.min_jitter_ms:.2f} ms")
        output.append(f"  Max Jitter: {result.jitter.max_jitter_ms:.2f} ms")
        output.append(f"  Std Dev: {result.jitter.std_dev_ms:.2f} ms")
        output.append(
            f"  Samples: {result.jitter.samples}/{result.jitter.samples + result.jitter.failed}"
        )
        output.append(f"  Success Rate: {result.jitter.success_rate_percent:.1f}%")
        output.append("")

    if result.download:
        output.append("DOWNLOAD")
        output.append(f"  Speed: {result.download.speed_mbps:.2f} Mbps")
        output.append(
            f"  Transferred: {result.download.bytes_transferred / (1024 * 1024):.2f} MB"
        )
        output.append(f"  Time: {result.download.time_seconds:.2f} seconds")
        output.append("")

    if result.upload:
        output.append("UPLOAD")
        output.append(f"  Speed: {result.upload.speed_mbps:.2f} Mbps")
        output.append(
            f"  Transferred: {result.upload.bytes_transferred / (1024 * 1024):.2f} MB"
        )
        output.append(f"  Time: {result.upload.time_seconds:.2f} seconds")
        output.append("")

    if result.errors:
        output.append("ERRORS")
        for error in result.errors:
            output.append(f"  - {error}")

    return "\n".join(output)


def format_json_output(result: SpeedTestResult) -> str:
    """
    Format test results as JSON.

    Args:
        result (SpeedTestResult): Speed test results to format

    Returns:
        str: JSON-formatted string
    """
    return json.dumps(result.to_dict(), indent=2)


def format_csv_output(result: SpeedTestResult) -> str:
    """
    Format test results as CSV.

    Args:
        result (SpeedTestResult): Speed test results to format

    Returns:
        str: CSV-formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Basic information
    writer.writerow(["Timestamp", result.formatted_timestamp])

    # Write sections for each test type
    if result.ping:
        writer.writerow([])
        writer.writerow(
            ["PING (ms)", "Min", "Avg", "Max", "Samples", "Failed", "Success Rate (%)"]
        )
        writer.writerow(
            [
                "",
                f"{result.ping.min_ms:.2f}",
                f"{result.ping.avg_ms:.2f}",
                f"{result.ping.max_ms:.2f}",
                result.ping.samples,
                result.ping.failed,
                f"{result.ping.success_rate_percent:.1f}",
            ]
        )

    if result.jitter:
        writer.writerow([])
        writer.writerow(
            [
                "JITTER (ms)",
                "Avg",
                "Min",
                "Max",
                "Std Dev",
                "Samples",
                "Failed",
                "Success Rate (%)",
            ]
        )
        writer.writerow(
            [
                "",
                f"{result.jitter.avg_jitter_ms:.2f}",
                f"{result.jitter.min_jitter_ms:.2f}",
                f"{result.jitter.max_jitter_ms:.2f}",
                f"{result.jitter.std_dev_ms:.2f}",
                result.jitter.samples,
                result.jitter.failed,
                f"{result.jitter.success_rate_percent:.1f}",
            ]
        )

    if result.download:
        writer.writerow([])
        writer.writerow(["DOWNLOAD", "Speed (Mbps)", "Transferred (MB)", "Time (s)"])
        writer.writerow(
            [
                "",
                f"{result.download.speed_mbps:.2f}",
                f"{result.download.bytes_transferred / (1024 * 1024):.2f}",
                f"{result.download.time_seconds:.2f}",
            ]
        )

    if result.upload:
        writer.writerow([])
        writer.writerow(["UPLOAD", "Speed (Mbps)", "Transferred (MB)", "Time (s)"])
        writer.writerow(
            [
                "",
                f"{result.upload.speed_mbps:.2f}",
                f"{result.upload.bytes_transferred / (1024 * 1024):.2f}",
                f"{result.upload.time_seconds:.2f}",
            ]
        )

    if result.errors:
        writer.writerow([])
        writer.writerow(["ERRORS"])
        for error in result.errors:
            writer.writerow(["", error])

    return output.getvalue()


def format_output(result: SpeedTestResult, output_format: str = "text") -> str:
    """
    Format test results based on the specified output format.

    Args:
        result (SpeedTestResult): Speed test results to format
        output_format (str): Desired output format (text, json, csv)

    Returns:
        str: Formatted output string
    """
    if output_format.lower() == "json":
        return format_json_output(result)
    elif output_format.lower() == "csv":
        return format_csv_output(result)
    else:
        return format_text_output(result)
