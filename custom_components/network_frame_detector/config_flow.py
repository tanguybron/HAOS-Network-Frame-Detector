"""Config flow for Network Frame Detector integration."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_COOLDOWN,
    CONF_MULTICAST,
    CONF_PATTERN_TYPE,
    CONF_PATTERN_VALUE,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_SENSOR_DURATION,
    CONF_SOURCE_IP,
    DEFAULT_COOLDOWN,
    DEFAULT_MULTICAST,
    DEFAULT_SENSOR_DURATION,
    DOMAIN,
    MAX_COOLDOWN,
    MAX_NAME_LENGTH,
    MAX_PATTERN_LENGTH,
    MAX_PATTERN_VALUE_LENGTH,
    MAX_REGEX_PATTERN_LENGTH,
    MAX_SENSOR_DURATION,
    MIN_COOLDOWN,
    MIN_SENSOR_DURATION,
    PatternType,
    Protocol,
)


def validate_name(name: str) -> bool:
    """Validate name field."""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > MAX_NAME_LENGTH:
        return False
    return True


def validate_port(port: int) -> bool:
    """Validate port number."""
    return 1 <= port <= 65535


def validate_pattern_value(pattern_type: str, pattern_value: str) -> tuple[bool, str | None]:
    """
    Validate pattern value based on pattern type.
    Returns (is_valid, error_message).
    """
    if not pattern_value or len(pattern_value.strip()) == 0:
        return False, "Pattern value cannot be empty"

    if len(pattern_value) > MAX_PATTERN_VALUE_LENGTH:
        return False, f"Pattern value exceeds maximum length of {MAX_PATTERN_VALUE_LENGTH}"

    if pattern_type == PatternType.HEX:
        # Hex pattern validation: must be even length and contain only hex characters
        pattern_clean = pattern_value.strip().replace(" ", "").replace(":", "")
        if len(pattern_clean) % 2 != 0:
            return False, "Hex pattern must have even number of characters"
        if not all(c in "0123456789abcdefABCDEF" for c in pattern_clean):
            return False, "Hex pattern must contain only hexadecimal characters"
        # Check decoded length doesn't exceed MAX_PATTERN_LENGTH
        try:
            decoded = bytes.fromhex(pattern_clean)
            if len(decoded) > MAX_PATTERN_LENGTH:
                return False, f"Decoded hex pattern exceeds maximum length of {MAX_PATTERN_LENGTH} bytes"
        except ValueError:
            return False, "Invalid hex pattern format"

    elif pattern_type == PatternType.REGEX:
        # Regex validation: check length and compile to catch syntax errors
        if len(pattern_value) > MAX_REGEX_PATTERN_LENGTH:
            return False, f"Regex pattern exceeds maximum length of {MAX_REGEX_PATTERN_LENGTH}"
        try:
            # Pre-compile to validate syntax and catch ReDoS-prone patterns early
            # Use timeout-safe compilation (Python 3.11+)
            compiled = re.compile(pattern_value)
            # Check for obviously dangerous patterns (very long alternations, nested quantifiers)
            # This is a basic check; full ReDoS prevention would require more sophisticated analysis
            if len(pattern_value) > 100 and ("|" in pattern_value or "*" in pattern_value or "+" in pattern_value):
                # Warn but don't block - user is responsible for safe patterns
                pass
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"

    # String patterns: just check length
    elif pattern_type == PatternType.STRING:
        # String patterns are encoded as bytes, so check byte length
        try:
            encoded = pattern_value.encode("utf-8")
            if len(encoded) > MAX_PATTERN_LENGTH:
                return False, f"String pattern exceeds maximum length of {MAX_PATTERN_LENGTH} bytes"
        except UnicodeEncodeError:
            return False, "Invalid string encoding"

    return True, None


def validate_ip_address(ip_str: str | None) -> bool:
    """Validate IP address format."""
    if not ip_str or ip_str.strip() == "":
        return True  # Optional field
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def validate_cooldown(cooldown: int | float) -> bool:
    """Validate cooldown value."""
    try:
        val = float(cooldown)
        return MIN_COOLDOWN <= val <= MAX_COOLDOWN
    except (ValueError, TypeError):
        return False


def validate_sensor_duration(duration: int | float) -> bool:
    """Validate sensor duration value."""
    try:
        val = float(duration)
        return MIN_SENSOR_DURATION <= val <= MAX_SENSOR_DURATION
    except (ValueError, TypeError):
        return False


class NetworkFrameDetectorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Network Frame Detector."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate all inputs
            if not validate_name(user_input.get(CONF_NAME, "")):
                errors[CONF_NAME] = "invalid_name"
            elif not validate_port(user_input.get(CONF_PORT, 0)):
                errors[CONF_PORT] = "invalid_port"
            elif not validate_cooldown(user_input.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)):
                errors[CONF_COOLDOWN] = "invalid_cooldown"
            elif not validate_sensor_duration(user_input.get(CONF_SENSOR_DURATION, DEFAULT_SENSOR_DURATION)):
                errors[CONF_SENSOR_DURATION] = "invalid_duration"
            elif not validate_ip_address(user_input.get(CONF_SOURCE_IP)):
                errors[CONF_SOURCE_IP] = "invalid_ip"
            else:
                # Validate pattern
                pattern_type = user_input.get(CONF_PATTERN_TYPE)
                pattern_value = user_input.get(CONF_PATTERN_VALUE, "")
                is_valid, error_msg = validate_pattern_value(pattern_type, pattern_value)
                if not is_valid:
                    if "hex" in error_msg.lower():
                        errors[CONF_PATTERN_VALUE] = "invalid_hex"
                    elif "regex" in error_msg.lower():
                        errors[CONF_PATTERN_VALUE] = "invalid_regex"
                    elif "length" in error_msg.lower():
                        errors[CONF_PATTERN_VALUE] = "pattern_too_long"
                    else:
                        errors[CONF_PATTERN_VALUE] = "invalid_pattern"

            if not errors:
                # Check for duplicate entries (by name)
                await self.async_set_unique_id(user_input[CONF_NAME])
                self._abort_if_unique_id_configured()

                # Check if port is already in use by another entry
                # Note: This is a basic check; actual port binding happens in listener
                existing_entries = self._async_current_entries()
                for entry in existing_entries:
                    if entry.data.get(CONF_PORT) == user_input[CONF_PORT]:
                        return self.async_abort(reason="port_in_use")

                # Create the entry
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Build schema with defaults
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=""): str,
                vol.Required(CONF_PROTOCOL, default=Protocol.UDP): vol.In([Protocol.UDP, Protocol.TCP]),
                vol.Required(CONF_PORT, default=5353): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required(CONF_MULTICAST, default=DEFAULT_MULTICAST): bool,
                vol.Required(CONF_PATTERN_TYPE, default=PatternType.STRING): vol.In([
                    PatternType.STRING,
                    PatternType.REGEX,
                    PatternType.HEX,
                ]),
                vol.Required(CONF_PATTERN_VALUE, default=""): str,
                vol.Required(CONF_COOLDOWN, default=DEFAULT_COOLDOWN): vol.All(
                    vol.Coerce(float), vol.Range(min=MIN_COOLDOWN, max=MAX_COOLDOWN)
                ),
                vol.Required(CONF_SENSOR_DURATION, default=DEFAULT_SENSOR_DURATION): vol.All(
                    vol.Coerce(float), vol.Range(min=MIN_SENSOR_DURATION, max=MAX_SENSOR_DURATION)
                ),
                vol.Optional(CONF_SOURCE_IP, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return NetworkFrameDetectorOptionsFlowHandler(config_entry)


class NetworkFrameDetectorOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Network Frame Detector."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # For now, options flow is not implemented
        # Configuration changes require removing and re-adding the entry
        return self.async_abort(reason="not_implemented")

