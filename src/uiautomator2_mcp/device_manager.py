"""Device connection manager for uiautomator2 MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import uiautomator2 as u2

from uiautomator2_mcp.adb_tools import list_devices as list_adb_devices


@dataclass
class ShellCommandResult:
    """Normalized result of a device shell command."""

    command: str
    output: str
    exit_code: int = 0
    stderr: str = ""


@dataclass
class DeviceConnectionState:
    """Tracked device connection plus lazy metadata caches."""

    device: u2.Device
    serial: str
    info: dict[str, Any] | None = None
    device_info: dict[str, Any] | None = None
    window_size: tuple[int, int] | None = None
    sdk_version: Any | None = None
    shell_timeout: float | None = None
    shell_session: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DeviceManager:
    """Manages MCP-session device connections keyed by serial/device_id."""

    def __init__(self) -> None:
        self._devices: dict[str, DeviceConnectionState] = {}

    @property
    def connected(self) -> bool:
        return bool(self._devices)

    def list_devices(self) -> list[dict[str, str]]:
        """List devices currently visible to adb."""
        return list_adb_devices()

    def connect(self, serial: str | None = None) -> tuple[str, dict]:
        """Connect to an Android device and store it by serial.

        Args:
            serial: Device serial number or IP address.
                    If None, resolves to the only available ready device.

        Returns:
            Tuple of resolved serial and device info dict.
        """
        requested_serial = serial or self._resolve_default_serial()
        device = u2.connect(requested_serial)
        resolved_serial = self._resolve_device_serial(device, fallback=requested_serial)
        info = device.info
        self._devices[resolved_serial] = DeviceConnectionState(
            device=device,
            serial=resolved_serial,
            info=info,
            sdk_version=self._extract_sdk_version(info),
        )
        return resolved_serial, info

    def get_device(self, device_id: str | None = None) -> u2.Device:
        """Get a connected device, requiring explicit selection if ambiguous."""
        return self.get_connection_state(device_id).device

    def get_connection_state(self, device_id: str | None = None) -> DeviceConnectionState:
        """Get tracked state for a connected device."""
        resolved_serial = self.get_serial(device_id)
        return self._devices[resolved_serial]

    def get_serial(self, device_id: str | None = None) -> str:
        """Get the resolved serial for a connected device."""
        if device_id is not None and device_id.strip():
            serial = device_id.strip()
            if serial not in self._devices:
                connected = ", ".join(sorted(self._devices)) or "(none)"
                raise RuntimeError(
                    f"Device {serial!r} is not connected in this MCP session. "
                    f"Use connect(serial={serial!r}) first. Connected device_ids: {connected}"
                )
            return serial

        if not self._devices:
            raise RuntimeError("No device connected. Use the 'connect' tool first.")

        if len(self._devices) > 1:
            connected = ", ".join(sorted(self._devices))
            raise RuntimeError(
                "Multiple devices are connected in this MCP session. "
                f"Pass device_id explicitly. Connected device_ids: {connected}"
            )

        return next(iter(self._devices))

    def get_device_details(self, device_id: str | None = None) -> dict[str, Any]:
        """Return cached device metadata, populating it lazily on first access."""
        state = self.get_connection_state(device_id)
        if state.info is None:
            state.info = state.device.info

        if state.device_info is None:
            state.device_info = state.device.device_info

        if state.window_size is None:
            window = state.device.window_size()
            state.window_size = (int(window[0]), int(window[1]))

        if state.sdk_version is None:
            state.sdk_version = self._extract_sdk_version(state.info, state.device_info)

        state.metadata.update(
            {
                "serial": state.serial,
                "sdk_version": state.sdk_version,
            }
        )
        return {
            "device_id": state.serial,
            "serial": state.serial,
            "sdk_version": state.sdk_version,
            "info": state.info,
            "device_info": state.device_info,
            "window_size": {
                "width": state.window_size[0],
                "height": state.window_size[1],
            },
        }

    def execute_shell(
        self,
        command: str,
        device_id: str | None = None,
        *,
        timeout: float | None = None,
    ) -> ShellCommandResult:
        """Execute a shell command via a centralized abstraction layer.

        This wrapper provides a single place to add persistent shell sessions,
        timeout policy, stderr handling, and logging in the future.
        """
        state = self.get_connection_state(device_id)
        shell_callable = getattr(state.shell_session, "run", None) or state.device.shell
        effective_timeout = timeout if timeout is not None else state.shell_timeout

        try:
            if effective_timeout is None:
                raw_result = shell_callable(command)
            else:
                raw_result = shell_callable(command, timeout=effective_timeout)
        except TypeError:
            raw_result = shell_callable(command)

        return self._normalize_shell_result(command, raw_result)

    def disconnect(self, device_id: str | None = None) -> str | None:
        """Disconnect one connected device and return its serial."""
        serial = self.get_serial(device_id)
        self._devices.pop(serial, None)
        return serial

    def disconnect_all(self) -> list[str]:
        """Disconnect all tracked devices and return their serials."""
        serials = sorted(self._devices)
        self._devices.clear()
        return serials

    def connected_device_ids(self) -> list[str]:
        """Return device IDs connected in this MCP session."""
        return sorted(self._devices)

    def _resolve_default_serial(self) -> str:
        """Resolve the default target serial when none was provided."""
        ready_devices = [
            device["serial"]
            for device in self.list_devices()
            if device.get("state") == "device"
        ]
        if not ready_devices:
            raise RuntimeError(
                "No ready adb devices found. Use list_devices() to inspect connected devices."
            )
        if len(ready_devices) > 1:
            raise RuntimeError(
                "Multiple adb devices are available. "
                f"Pass serial/device_id explicitly. Available devices: {', '.join(sorted(ready_devices))}"
            )
        return ready_devices[0]

    def _resolve_device_serial(self, device: u2.Device, *, fallback: str | None = None) -> str:
        """Best-effort resolve of the connected device serial."""
        serial = getattr(device, "serial", None)
        if isinstance(serial, str) and serial.strip():
            return serial.strip()
        if fallback and fallback.strip():
            return fallback.strip()
        raise RuntimeError("Connected device serial could not be determined.")

    def _normalize_shell_result(self, command: str, raw_result: Any) -> ShellCommandResult:
        """Normalize different uiautomator2 shell response shapes."""
        if isinstance(raw_result, tuple):
            output = raw_result[0] if len(raw_result) > 0 else ""
            exit_code = raw_result[1] if len(raw_result) > 1 else 0
            stderr = raw_result[2] if len(raw_result) > 2 else ""
            return ShellCommandResult(
                command=command,
                output=self._coerce_shell_text(output),
                exit_code=self._coerce_exit_code(exit_code),
                stderr=self._coerce_shell_text(stderr),
            )

        output = getattr(raw_result, "output", None)
        exit_code = getattr(raw_result, "exit_code", None)
        stderr = getattr(raw_result, "stderr", None)
        if output is not None or exit_code is not None or stderr is not None:
            return ShellCommandResult(
                command=command,
                output=self._coerce_shell_text(output),
                exit_code=self._coerce_exit_code(exit_code),
                stderr=self._coerce_shell_text(stderr),
            )

        return ShellCommandResult(command=command, output=self._coerce_shell_text(raw_result))

    def _extract_sdk_version(self, *sources: dict[str, Any] | None) -> Any | None:
        """Extract SDK version from known uiautomator2 info payload shapes."""
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in ("sdkInt", "sdk_int", "sdk", "version_sdk"):
                value = source.get(key)
                if value is not None:
                    return value
            version = source.get("version")
            if isinstance(version, dict):
                for key in ("sdk", "sdkInt", "sdk_int"):
                    value = version.get(key)
                    if value is not None:
                        return value
        return None

    def _coerce_shell_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _coerce_exit_code(self, value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


# Global singleton
device_manager = DeviceManager()
