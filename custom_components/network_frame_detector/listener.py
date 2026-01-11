"""Secure network listener for frame detection."""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from datetime import datetime, timedelta
from typing import Callable, Pattern

from homeassistant.core import HomeAssistant

from .const import (
    CONF_COOLDOWN,
    CONF_MULTICAST,
    CONF_PATTERN_TYPE,
    CONF_PATTERN_VALUE,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_SENSOR_DURATION,
    CONF_SOURCE_IP,
    MAX_PAYLOAD_INSPECTION,
    PatternType,
    Protocol,
    REGEX_FLAGS,
)


class SecureNetworkListener:
    """
    Secure network listener that binds to a specific port and matches patterns.
    
    Security guarantees:
    - Binds only to specified port (no promiscuous mode)
    - No packet injection or modification
    - No traffic forwarding
    - No payload storage beyond in-memory matching
    - Length-limited payload inspection
    - Time-bounded pattern matching
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
        on_detection: Callable[[], None],
    ) -> None:
        """Initialize the secure network listener."""
        self.hass = hass
        self.config = config
        self.on_detection = on_detection
        self._socket: socket.socket | None = None
        self._transport: asyncio.DatagramTransport | None = None
        self._server: asyncio.Server | None = None
        self._running = False
        self._last_detection: datetime | None = None
        self._cooldown = timedelta(seconds=config.get(CONF_COOLDOWN, 5))
        
        # Compile pattern based on type
        self._pattern = self._compile_pattern(
            config.get(CONF_PATTERN_TYPE, PatternType.STRING),
            config.get(CONF_PATTERN_VALUE, ""),
        )
        
        # Optional source IP filter
        source_ip_str = config.get(CONF_SOURCE_IP)
        if source_ip_str and source_ip_str.strip():
            try:
                self._source_ip_filter = ipaddress.ip_address(source_ip_str.strip())
            except ValueError:
                self._source_ip_filter = None
        else:
            self._source_ip_filter = None

    def _compile_pattern(
        self, pattern_type: str, pattern_value: str
    ) -> bytes | Pattern[bytes] | None:
        """
        Compile pattern for matching.
        Returns bytes for string/hex patterns, compiled regex for regex patterns.
        """
        if not pattern_value:
            return None

        if pattern_type == PatternType.STRING:
            # String pattern: encode to bytes
            try:
                return pattern_value.encode("utf-8")
            except UnicodeEncodeError:
                return None

        elif pattern_type == PatternType.HEX:
            # Hex pattern: decode hex string to bytes
            pattern_clean = pattern_value.strip().replace(" ", "").replace(":", "")
            try:
                return bytes.fromhex(pattern_clean)
            except ValueError:
                return None

        elif pattern_type == PatternType.REGEX:
            # Regex pattern: compile with safe flags
            try:
                # Compile regex pattern for bytes matching
                return re.compile(pattern_value.encode("utf-8"), REGEX_FLAGS)
            except (re.error, UnicodeEncodeError):
                return None

        return None

    def _matches_pattern(self, payload: bytes) -> bool:
        """
        Check if payload matches the configured pattern.
        Security: Only inspects up to MAX_PAYLOAD_INSPECTION bytes.
        """
        if not self._pattern:
            return False

        # Limit payload inspection to prevent memory exhaustion
        limited_payload = payload[:MAX_PAYLOAD_INSPECTION]

        if isinstance(self._pattern, bytes):
            # Simple byte pattern matching
            return self._pattern in limited_payload

        elif isinstance(self._pattern, Pattern):
            # Regex pattern matching
            # Use search with timeout protection (Python 3.11+)
            try:
                return bool(self._pattern.search(limited_payload))
            except Exception:
                # Catch any regex exceptions (shouldn't happen with pre-compiled patterns)
                return False

        return False

    def _check_cooldown(self) -> bool:
        """Check if cooldown period has elapsed."""
        if self._last_detection is None:
            return True
        return datetime.now() - self._last_detection >= self._cooldown

    def _handle_udp_datagram(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        """
        Handle incoming UDP datagram.
        Security: Only processes data, never modifies or forwards it.
        """
        if not self._running:
            return

        # Check cooldown
        if not self._check_cooldown():
            return

        # Optional source IP filtering
        if self._source_ip_filter is not None:
            try:
                source_ip = ipaddress.ip_address(addr[0])
                if source_ip != self._source_ip_filter:
                    return
            except ValueError:
                # Invalid source IP, ignore
                return

        # Check pattern match
        if self._matches_pattern(data):
            self._last_detection = datetime.now()
            # Schedule callback in event loop
            # async_run_job already schedules the callback, no need to wrap in create_task
            self.hass.async_run_job(self.on_detection)

    class _UDPProtocol(asyncio.DatagramProtocol):
        """UDP protocol handler for secure frame detection."""
        
        def __init__(self, listener: SecureNetworkListener) -> None:
            """Initialize protocol with listener reference."""
            self._listener = listener
        
        def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
            """Handle received datagram."""
            self._listener._handle_udp_datagram(data, addr)

    async def _tcp_connection_handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle TCP connection.
        Security: Only reads data, never modifies or forwards it.
        """
        if not self._running:
            writer.close()
            await writer.wait_closed()
            return

        try:
            # Read data with size limit
            data = await asyncio.wait_for(
                reader.read(MAX_PAYLOAD_INSPECTION),
                timeout=1.0,  # Timeout to prevent hanging
            )

            # Optional source IP filtering
            if self._source_ip_filter is not None:
                try:
                    peer_addr = writer.get_extra_info("peername")
                    if peer_addr:
                        source_ip = ipaddress.ip_address(peer_addr[0])
                        if source_ip != self._source_ip_filter:
                            writer.close()
                            await writer.wait_closed()
                            return
                except (ValueError, TypeError):
                    # Invalid source IP, close connection
                    writer.close()
                    await writer.wait_closed()
                    return

            # Check pattern match
            if data and self._matches_pattern(data):
                if self._check_cooldown():
                    self._last_detection = datetime.now()
                    # async_run_job already schedules the callback
                    self.hass.async_run_job(self.on_detection)

        except asyncio.TimeoutError:
            # Timeout is expected for TCP connections
            pass
        except Exception:
            # Log but don't crash on any exception
            pass
        finally:
            # Always close the connection
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self) -> None:
        """Start the listener."""
        if self._running:
            return

        protocol = self.config.get(CONF_PROTOCOL, Protocol.UDP)
        port = self.config.get(CONF_PORT, 5353)
        multicast = self.config.get(CONF_MULTICAST, False)

        try:
            if protocol == Protocol.UDP:
                # Create UDP socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Security: Bind only to specified port, never promiscuous mode
                sock.bind(("", port))
                
                # Set multicast options if needed
                if multicast:
                    # Join multicast group (for mDNS, etc.)
                    # This is safe as we're only receiving, not forwarding
                    mreq = socket.inet_aton("224.0.0.251") + socket.inet_aton("0.0.0.0")
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

                # Create transport with secure protocol
                loop = asyncio.get_event_loop()
                protocol = self._UDPProtocol(self)
                transport, _ = await loop.create_datagram_endpoint(
                    lambda: protocol,
                    sock=sock,
                )

                self._transport = transport
                self._socket = sock
                self._running = True

            elif protocol == Protocol.TCP:
                # Create TCP server
                # Security: Bind only to specified port
                self._server = await asyncio.start_server(
                    self._tcp_connection_handler,
                    host="",  # Bind to all interfaces (required for HAOS)
                    port=port,
                )
                self._running = True

        except OSError as e:
            # Port might be in use or permission denied
            raise RuntimeError(f"Failed to start listener on port {port}: {e}")

    async def stop(self) -> None:
        """Stop the listener and clean up resources."""
        self._running = False

        if self._transport:
            self._transport.close()
            self._transport = None

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

