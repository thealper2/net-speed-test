class SpeedTestError(Exception):
    """Base exception for all speed test errors."""

    pass


class NetworkConnectionError(SpeedTestError):
    """Exception raised when there's an issue connecting to the server."""

    pass


class TestTimeoutError(SpeedTestError):
    """Exception raised when a test times out."""

    pass


class InvalidResponseError(SpeedTestError):
    """Exception raised when the server response is invalid or unexpected."""

    pass


class ConfigurationError(SpeedTestError):
    """Exception raised when there's an issue with the configuration."""

    pass


class DataValidationError(SpeedTestError):
    """Exception raised when data validation fails."""

    pass
