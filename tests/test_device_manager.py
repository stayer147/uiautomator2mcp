import unittest
from unittest.mock import patch

from uiautomator2_mcp.device_manager import DeviceManager


class _HealthyDevice:
    def __init__(self, serial: str, info: dict):
        self.serial = serial
        self._info = info

    @property
    def info(self) -> dict:
        return self._info


class _FailingInfoDevice:
    def __init__(self, serial: str):
        self.serial = serial

    @property
    def info(self) -> dict:
        raise RuntimeError("atx-agent not ready")


class DeviceManagerConnectTests(unittest.TestCase):
    def test_failed_connect_does_not_store_ghost_device_or_replace_existing_device(self) -> None:
        manager = DeviceManager()
        healthy_device = _HealthyDevice("serial-1", {"model": "ok"})
        manager._devices["serial-1"] = healthy_device

        with patch(
            "uiautomator2_mcp.device_manager.u2.connect",
            return_value=_FailingInfoDevice("serial-2"),
        ):
            with self.assertRaisesRegex(RuntimeError, "atx-agent not ready"):
                manager.connect("serial-2")

        self.assertEqual(manager.connected_device_ids(), ["serial-1"])
        self.assertIs(manager.get_device("serial-1"), healthy_device)


if __name__ == "__main__":
    unittest.main()
