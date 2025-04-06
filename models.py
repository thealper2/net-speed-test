import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, conint, validator


class OutputFormat(Enum):
    """
    Enumeration of supported output formats.
    """

    TEXT = auto()
    JSON = auto()
    CSV = auto()


class SpeedTestConfig(BaseModel):
    """
    Configuration for speed tests.
    """

    url: str = Field(..., description="URL of the speed test server")
    download_size_mb: conint(gt=0, lt=1000) = Field(
        10, description="Size of download test in MB"
    )
    upload_size_mb: conint(gt=0, lt=1000) = Field(
        5, description="Size of upload test in MB"
    )
    ping_count: conint(gt=0, lt=100) = Field(
        10, description="Number of ping measurements"
    )
    jitter_samples: conint(gt=0, lt=100) = Field(
        20, description="Number of samples for jitter measurement"
    )
    timeout_seconds: conint(gt=0, lt=300) = Field(
        30, description="Timeout for network operations in seconds"
    )

    @validator("url")
    def validate_url(cls, v):
        """
        Validate that the URL uses HTTPS.
        """
        if not v.startswith("https://"):
            raise ValueError("URL must use HTTPS for security")

        return v


@dataclass
class PingResult:
    """
    Results from ping (latency) test.
    """

    min_ms: float
    max_ms: float
    avg_ms: float
    samples: int
    failed: int = 0
    success_rate_percent: float = 100.0


@dataclass
class JitterResult:
    """
    Results from jitter (latency variation) test.
    """

    avg_jitter_ms: float
    min_jitter_ms: float
    max_jitter_ms: float
    std_dev_ms: float
    samples: int
    failed: int = 0
    success_rate_percent: float = 100.0


@dataclass
class DownloadResult:
    """
    Results from download speed test.
    """

    speed_mbps: float
    bytes_transferred: int
    time_seconds: float
    requested_size_mb: int


@dataclass
class UploadResult:
    """
    Results from upload speed test.
    """

    speed_mbps: float
    bytes_transferred: int
    time_seconds: float
    requested_size_mb: int


@dataclass
class SpeedTestResult:
    """
    Combined results from all speed tests.
    """

    ping: Optional[PingResult] = None
    jitter: Optional[JitterResult] = None
    download: Optional[DownloadResult] = None
    upload: Optional[UploadResult] = None
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def formatted_timestamp(self) -> str:
        """
        Get a human-readable timestamp string.
        """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))

    @property
    def is_successful(self) -> bool:
        """
        Check if at least one test completed successfully.
        """
        return any([self.ping, self.jitter, self.download, self.upload])

    @property
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary for serialization.
        """
        result = {"timestamp": self.formatted_timestamp, "errors": self.errors}

        if self.ping:
            result["ping"] = {
                "min_ms": round(self.ping.min_ms, 2),
                "max_ms": round(self.ping.max_ms, 2),
                "avg_ms": round(self.ping.avg_ms, 2),
                "samples": self.ping.samples,
                "failed": self.ping.failed,
                "success_rate_percent": round(self.ping.success_rate_percent, 2),
            }

        if self.jitter:
            result["jitter"] = {
                "min_ms": round(self.jitter.min_jitter_ms, 2),
                "max_ms": round(self.jitter.max_jitter_ms, 2),
                "avg_ms": round(self.jitter.avg_jitter_ms, 2),
                "samples": self.jitter.samples,
                "failed": self.jitter.failed,
                "success_rate_percent": round(self.jitter.success_rate_percent, 2),
            }

        if self.download:
            result["download"] = {
                "speed_mbps": round(self.download.speed_mbps, 2),
                "bytes": self.download.bytes_transferred,
                "time_seconds": round(self.download.time_seconds, 2),
                "size_mb": self.download.requested_size_mb,
            }

        if self.upload:
            result["upload"] = {
                "speed_mbps": round(self.upload.speed_mbps, 2),
                "bytes": self.upload.bytes_transferred,
                "time_seconds": round(self.upload.time_seconds, 2),
                "size_mb": self.upload.requested_size_mb,
            }

        return result
