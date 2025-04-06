import logging
import secrets
import statistics
import time
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import requests

from exceptions import InvalidResponseError, NetworkConnectionError, TestTimeoutError
from models import (
    DownloadResult,
    JitterResult,
    PingResult,
    SpeedTestConfig,
    SpeedTestResult,
    UploadResult,
)


class BaseTest(ABC):
    """Abstract base class for all network performance tests."""

    def __init__(
        self, config: SpeedTestConfig, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the base test.

        Args:
            config (SpeedTestConfig): Configuration parameters for the test
            logger (Optional[logging.Logger]): Logger instance for logging
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    def run_test(self) -> Any:
        """
        Run the test and return the result.

        Returns:
            Test result object
        """
        pass


class PingTest(BaseTest):
    """Test for measuring network latency (ping)."""

    def run_test(self) -> PingResult:
        """
        Run ping test to measure network latency.

        Returns:
            PingResult: Results of the ping test

        Raises:
            NetworkConnectionError: If there's an issue connecting to the server
            TestTimeoutError: If the test times out
        """
        self.logger.info(f"Starting ping test ({self.config.ping_count} samples)...")

        ping_times: List[float] = []
        failed_pings = 0

        for i in range(self.config.ping_count):
            try:
                start_time = time.time()
                response = requests.get(
                    self.config.url,
                    timeout=self.config.timeout_seconds,
                    headers={"Cache-Control": "no-cache"},
                    params={"_": int(time.time() * 1000)},  # Cache buster
                )
                end_time = time.time()

                if response.status_code == 200:
                    ping_time = (end_time - start_time) * 1000  # Convert to ms
                    ping_times.append(ping_time)
                    self.logger.debug(
                        f"Ping {i + 1}/{self.config.ping_count}: {ping_time:.2f} ms"
                    )
                else:
                    self.logger.warning(
                        f"Ping request {i + 1} failed with status code: {response.status_code}"
                    )
                    failed_pings += 1

            except requests.exceptions.Timeout:
                self.logger.warning(f"Ping request {i + 1} timed out")
                failed_pings += 1

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Ping request {i + 1} failed: {e}")
                failed_pings += 1

            # Small delay between pings to avoid overwhelming the server
            if i < self.config.ping_count - 1:
                time.sleep(0.2)

        # Calculate statistics if we have any successful pings
        if ping_times:
            min_ping = min(ping_times)
            max_ping = max(ping_times)
            avg_ping = statistics.mean(ping_times)

            success_rate = (len(ping_times) / self.config.ping_count) * 100

            self.logger.info(
                f"Ping test completed: min={min_ping:.2f}ms, avg={avg_ping:.2f}ms, max={max_ping:.2f}ms"
            )

            return PingResult(
                min_ms=min_ping,
                max_ms=max_ping,
                avg_ms=avg_ping,
                samples=len(ping_times),
                failed=failed_pings,
                success_rate_percent=success_rate,
            )
        else:
            raise NetworkConnectionError("All ping requests failed")


class JitterTest(BaseTest):
    """Test for measuring jitter (variation in ping times)."""

    def run_test(self) -> JitterResult:
        """
        Run jitter test to measure stability of network latency.

        Returns:
            JitterResult: Results of the jitter test

        Raises:
            NetworkConnectionError: If there's an issue connecting to the server
            TestTimeoutError: If the test times out
        """
        self.logger.info(
            f"Starting jitter test ({self.config.jitter_samples} samples)..."
        )

        ping_times: List[float] = []
        failed_pings = 0

        for i in range(self.config.jitter_samples):
            try:
                start_time = time.time()
                response = requests.get(
                    self.config.url,
                    timeout=self.config.timeout_seconds,
                    headers={"Cache-Control": "no-cache"},
                    params={"_": int(time.time() * 1000)},  # Cache buster
                )
                end_time = time.time()

                if response.status_code == 200:
                    ping_time = (end_time - start_time) * 1000  # Convert to ms
                    ping_times.append(ping_time)
                    self.logger.debug(
                        f"Jitter sample {i + 1}/{self.config.jitter_samples}: {ping_time:.2f} ms"
                    )
                else:
                    self.logger.warning(
                        f"Jitter request {i + 1} failed with status code: {response.status_code}"
                    )
                    failed_pings += 1

            except requests.exceptions.Timeout:
                self.logger.warning(f"Jitter request {i + 1} timed out")
                failed_pings += 1

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Jitter request {i + 1} failed: {e}")
                failed_pings += 1

            # Small delay between pings to avoid overwhelming the server
            if i < self.config.jitter_samples - 1:
                time.sleep(0.2)

        # Calculate jitter if we have at least two successful pings
        if len(ping_times) >= 2:
            # Calculate differences between consecutive ping times
            differences = [
                abs(ping_times[i] - ping_times[i - 1])
                for i in range(1, len(ping_times))
            ]

            jitter = statistics.mean(differences)
            max_jitter = max(differences)
            min_jitter = min(differences)
            std_dev = statistics.stdev(differences) if len(differences) > 1 else 0

            success_rate = (len(ping_times) / self.config.jitter_samples) * 100

            self.logger.info(f"Jitter test completed: {jitter:.2f}ms avg jitter")

            return JitterResult(
                avg_jitter_ms=jitter,
                min_jitter_ms=min_jitter,
                max_jitter_ms=max_jitter,
                std_dev_ms=std_dev,
                samples=len(ping_times),
                failed=failed_pings,
                success_rate_percent=success_rate,
            )
        else:
            raise NetworkConnectionError(
                "Not enough successful jitter samples to calculate result"
            )


class DownloadTest(BaseTest):
    """Test for measuring download speed."""

    def run_test(self) -> DownloadResult:
        """
        Run download test to measure download speed.

        Returns:
            DownloadResult: Results of the download test

        Raises:
            NetworkConnectionError: If there's an issue connecting to the server
            TestTimeoutError: If the test times out
            InvalidResponseError: If the server response is invalid
        """
        size_bytes = self.config.download_size_mb * 1024 * 1024
        url = f"{self.config.url}?bytes={size_bytes}"

        self.logger.info(
            f"Starting download test ({self.config.download_size_mb} MB)..."
        )

        try:
            start_time = time.time()

            # Stream the response to handle large downloads efficiently
            response = requests.get(
                url,
                timeout=self.config.timeout_seconds,
                stream=True,
                headers={"Cache-Control": "no-cache"},
            )

            if response.status_code != 200:
                raise InvalidResponseError(
                    f"Download test failed with status code: {response.status_code}"
                )

            # Read the content in chunks to avoid memory issues
            chunk_size = 8192
            downloaded_bytes = 0

            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    downloaded_bytes += len(chunk)

            end_time = time.time()
            duration = end_time - start_time

            # Calculate the speed in Mbps (megabits per second)
            if duration > 0:
                speed_bps = (downloaded_bytes * 8) / duration
                speed_mbps = speed_bps / 1_000_000

                self.logger.info(f"Download test completed: {speed_mbps:.2f} Mbps")

                return DownloadResult(
                    speed_mbps=speed_mbps,
                    bytes_transferred=downloaded_bytes,
                    time_seconds=duration,
                    requested_size_mb=self.config.download_size_mb,
                )
            else:
                raise InvalidResponseError("Download completed too quickly to measure")

        except requests.exceptions.Timeout:
            raise TestTimeoutError("Download test timed out")

        except requests.exceptions.RequestException as e:
            raise NetworkConnectionError(f"Download test failed: {e}")


class UploadTest(BaseTest):
    """Test for measuring upload speed."""

    def run_test(self) -> UploadResult:
        """
        Run upload test to measure upload speed.

        Returns:
            UploadResult: Results of the upload test

        Raises:
            NetworkConnectionError: If there's an issue connecting to the server
            TestTimeoutError: If the test times out
            InvalidResponseError: If the server response is invalid
        """
        size_bytes = self.config.upload_size_mb * 1024 * 1024

        # Generate random data for upload
        # Using secrets for cryptographically strong random data
        self.logger.info(
            f"Generating {self.config.upload_size_mb} MB of data for upload test..."
        )

        # Generate data in chunks to avoid memory issues with large uploads
        chunk_size = min(1024 * 1024, size_bytes)  # 1 MB chunks or smaller
        remaining_bytes = size_bytes

        self.logger.info(f"Starting upload test ({self.config.upload_size_mb} MB)...")

        try:
            start_time = time.time()

            with requests.Session() as session:
                # Function to generate chunks of random data
                def data_generator():
                    nonlocal remaining_bytes
                    while remaining_bytes > 0:
                        current_chunk_size = min(chunk_size, remaining_bytes)
                        chunk = secrets.token_bytes(current_chunk_size)
                        remaining_bytes -= current_chunk_size
                        yield chunk

                # Use POST to upload the data
                response = session.post(
                    self.config.url,
                    data=data_generator(),
                    timeout=self.config.timeout_seconds,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Cache-Control": "no-cache",
                    },
                )

            end_time = time.time()
            duration = end_time - start_time

            if response.status_code not in (200, 201, 202, 204):
                raise InvalidResponseError(
                    f"Upload test failed with status code: {response.status_code}"
                )

            # Calculate the speed in Mbps (megabits per second)
            if duration > 0:
                speed_bps = (size_bytes * 8) / duration
                speed_mbps = speed_bps / 1_000_000

                self.logger.info(f"Upload test completed: {speed_mbps:.2f} Mbps")

                return UploadResult(
                    speed_mbps=speed_mbps,
                    bytes_transferred=size_bytes,
                    time_seconds=duration,
                    requested_size_mb=self.config.upload_size_mb,
                )
            else:
                raise InvalidResponseError("Upload completed too quickly to measure")

        except requests.exceptions.Timeout:
            raise TestTimeoutError("Upload test timed out")

        except requests.exceptions.RequestException as e:
            raise NetworkConnectionError(f"Upload test failed: {e}")


class SpeedTester:
    """Main class for running internet speed tests."""

    def __init__(self, config: SpeedTestConfig):
        """
        Initialize the speed tester with configuration.

        Args:
            config (SpeedTestConfig): Configuration for speed tests
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run_ping_test(self) -> PingResult:
        """
        Run ping test to measure network latency.

        Returns:
            PingResult: Results of the ping test
        """
        test = PingTest(self.config, self.logger)
        return test.run_test()

    def run_jitter_test(self) -> JitterResult:
        """
        Run jitter test to measure stability of network latency.

        Returns:
            JitterResult: Results of the jitter test
        """
        test = JitterTest(self.config, self.logger)
        return test.run_test()

    def run_download_test(self) -> DownloadResult:
        """
        Run download test to measure download speed.

        Returns:
            DownloadResult: Results of the download test
        """
        test = DownloadTest(self.config, self.logger)
        return test.run_test()

    def run_upload_test(self) -> UploadResult:
        """
        Run upload test to measure upload speed.

        Returns:
            UploadResult: Results of the upload test
        """
        test = UploadTest(self.config, self.logger)
        return test.run_test()

    def run_all_tests(self) -> SpeedTestResult:
        """
        Run all network performance tests and aggregate results.

        Returns:
            SpeedTestResult: Combined results of all tests
        """
        result = SpeedTestResult()

        # Run tests in sequence to avoid interference
        try:
            result.ping = self.run_ping_test()
        except Exception as e:
            self.logger.error(f"Ping test failed: {e}")
            result.errors.append(f"Ping test error: {str(e)}")

        try:
            result.jitter = self.run_jitter_test()
        except Exception as e:
            self.logger.error(f"Jitter test failed: {e}")
            result.errors.append(f"Jitter test error: {str(e)}")

        try:
            result.download = self.run_download_test()
        except Exception as e:
            self.logger.error(f"Download test failed: {e}")
            result.errors.append(f"Download test error: {str(e)}")

        try:
            result.upload = self.run_upload_test()
        except Exception as e:
            self.logger.error(f"Upload test failed: {e}")
            result.errors.append(f"Upload test error: {str(e)}")

        # Record test completion time
        result.timestamp = time.time()

        return result
