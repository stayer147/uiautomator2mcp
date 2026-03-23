"""Device connection manager for uiautomator2 MCP server."""

from __future__ import annotations

import uiautomator2 as u2

from uiautomator2_mcp.adb_tools import list_devices as list_adb_devices


class DeviceManager:
    """Manages MCP-session device connections keyed by serial/device_id."""

    def __init__(self) -> None:
        self._devices: dict[str, u2.Device] = {}
        self._default_serial: str | None = None

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
        resolved_serial = serial or self._resolve_default_serial()
        device = u2.connect(resolved_serial)
        resolved_serial = self._resolve_device_serial(device, fallback=resolved_serial)
        self._devices[resolved_serial] = device
        self._default_serial = resolved_serial
        return resolved_serial, device.info

    def get_device(self, device_id: str | None = None) -> u2.Device:
        """Get a connected device, falling back to the current default when available."""
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

        if self._default_serial in self._devices:
            return self._default_serial

        if len(self._devices) == 1:
            return next(iter(self._devices))

        connected = ", ".join(sorted(self._devices))
        raise RuntimeError(
            "Multiple devices are connected in this MCP session, but no default device is set. "
            f"Pass device_id explicitly. Connected device_ids: {connected}"
        )

    def disconnect(self, device_id: str | None = None) -> str | None:
        """Disconnect one connected device and return its serial."""
        serial = self.get_serial(device_id)
        self._devices.pop(serial, None)
        if not self._devices:
            self._default_serial = None
        elif self._default_serial == serial:
            self._default_serial = next(reversed(self._devices))
        return serial

    def disconnect_all(self) -> list[str]:
        """Disconnect all tracked devices and return their serials."""
        serials = sorted(self._devices)
        self._devices.clear()
        self._default_serial = None
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


# Global singleton
device_manager = DeviceManager()
