from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from uiautomator2_mcp.device_manager import DeviceManager


class DeviceManagerDefaultSelectionTests(unittest.TestCase):
    def test_connect_keeps_latest_device_as_default(self) -> None:
        manager = DeviceManager()

        with patch("uiautomator2_mcp.device_manager.u2.connect") as connect_mock:
            connect_mock.side_effect = [
                SimpleNamespace(serial="device-1", info={"serial": "device-1"}),
                SimpleNamespace(serial="device-2", info={"serial": "device-2"}),
            ]

            manager.connect("device-1")
            manager.connect("device-2")

        self.assertEqual(manager.get_serial(), "device-2")
        self.assertIs(manager.get_device(), manager.get_device("device-2"))

    def test_disconnect_promotes_remaining_device_when_default_removed(self) -> None:
        manager = DeviceManager()

        with patch("uiautomator2_mcp.device_manager.u2.connect") as connect_mock:
            connect_mock.side_effect = [
                SimpleNamespace(serial="device-1", info={"serial": "device-1"}),
                SimpleNamespace(serial="device-2", info={"serial": "device-2"}),
            ]

            manager.connect("device-1")
            manager.connect("device-2")

        manager.disconnect("device-2")

        self.assertEqual(manager.get_serial(), "device-1")
        self.assertEqual(manager.connected_device_ids(), ["device-1"])

    def test_disconnect_all_clears_default_device(self) -> None:
        manager = DeviceManager()

        with patch("uiautomator2_mcp.device_manager.u2.connect") as connect_mock:
            connect_mock.return_value = SimpleNamespace(serial="device-1", info={})
            manager.connect("device-1")

        manager.disconnect_all()

        with self.assertRaisesRegex(RuntimeError, "No device connected"):
            manager.get_serial()


if __name__ == "__main__":
    unittest.main()
