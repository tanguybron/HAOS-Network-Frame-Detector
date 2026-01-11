"""Constants for Network Frame Detector integration."""

from enum import Enum
from typing import Final

DOMAIN: Final = "network_frame_detector"
PLATFORM: Final = "binary_sensor"

# Security constraints - hard limits to prevent abuse
MAX_PATTERN_LENGTH: Final = 1024  # Maximum pattern length in bytes
MAX_NAME_LENGTH: Final = 64  # Maximum name length
MAX_PAYLOAD_INSPECTION: Final = 4096  # Maximum bytes to inspect per packet
MIN_COOLDOWN: Final = 0  # Minimum cooldown in seconds
MAX_COOLDOWN: Final = 3600  # Maximum cooldown (1 hour)
MIN_SENSOR_DURATION: Final = 1  # Minimum sensor ON duration in seconds
MAX_SENSOR_DURATION: Final = 3600  # Maximum sensor ON duration (1 hour)
MAX_PATTERN_VALUE_LENGTH: Final = 2048  # Maximum pattern value string length

# Regex compilation flags for security
# re.NOFLAG is Python 3.11+, fallback to 0 for older versions
import re
try:
    REGEX_FLAGS = re.NOFLAG
except AttributeError:
    REGEX_FLAGS = 0

# Maximum regex pattern length to prevent ReDoS
MAX_REGEX_PATTERN_LENGTH: Final = 256

# Event types
EVENT_NETWORK_FRAME_DETECTED: Final = "network_frame_detected"

# Configuration keys
CONF_NAME: Final = "name"
CONF_PROTOCOL: Final = "protocol"
CONF_PORT: Final = "port"
CONF_MULTICAST: Final = "multicast"
CONF_PATTERN_TYPE: Final = "pattern_type"
CONF_PATTERN_VALUE: Final = "pattern_value"
CONF_COOLDOWN: Final = "cooldown"
CONF_SENSOR_DURATION: Final = "sensor_duration"
CONF_SOURCE_IP: Final = "source_ip"  # Optional source IP filter

# Default values
DEFAULT_COOLDOWN: Final = 5
DEFAULT_SENSOR_DURATION: Final = 30
DEFAULT_MULTICAST: Final = False


class Protocol(str, Enum):
    """Supported network protocols."""

    UDP = "udp"
    TCP = "tcp"


class PatternType(str, Enum):
    """Supported pattern matching types."""

    STRING = "string"
    REGEX = "regex"
    HEX = "hex"

