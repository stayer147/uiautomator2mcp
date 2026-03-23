"""Device connection manager for uiautomator2 MCP server."""

from __future__ import annotations

import uiautomator2 as u2


class DeviceManager:
    """Manages a single uiautomator2 device connection."""

    def __init__(self) -> None:
        self._device: u2.Device | None = None
        self._serial: str | None = None

    @property
    def connected(self) -> bool:
        return self._device is not None

    def connect(self, serial: str | None = None) -> dict:
        """Connect to an Android device.

        Args:
            serial: Device serial number or IP address.
                    If None, connects to the first available device.

        Returns:
            Device info dict.
        """
        if self._device is not None:
            self.disconnect()

        self._device = u2.connect(serial) if serial else u2.connect()
        self._serial = serial or self._resolve_device_serial()
        return self._device.info

    def get_device(self) -> u2.Device:
        """Get the current device, raising if not connected."""
        if self._device is None:
            raise RuntimeError(
                "No device connected. Use the 'connect' tool first."
            )
        return self._device

    def get_serial(self) -> str:
        """Get the current device serial, raising if not connected."""
        if self._device is None:
            raise RuntimeError(
                "No device connected. Use the 'connect' tool first."
            )
        if self._serial:
            return self._serial
        self._serial = self._resolve_device_serial()
        return self._serial

    def _resolve_device_serial(self) -> str:
        """Best-effort resolve of the connected device serial."""
        if self._device is None:
            raise RuntimeError(
                "No device connected. Use the 'connect' tool first."
            )
        serial = getattr(self._device, "serial", None)
        if isinstance(serial, str) and serial.strip():
            return serial.strip()
        raise RuntimeError("Connected device serial could not be determined.")

    def disconnect(self) -> None:
        """Disconnect from the current device."""
        self._device = None
        self._serial = None


# Global singleton
device_manager = DeviceManager()
