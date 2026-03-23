import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from uiautomator2_mcp.device_manager import DeviceConnectionState, DeviceManager


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


class _MetadataDevice:
    def __init__(self) -> None:
        self.serial = "serial-1"
        self.info_calls = 0
        self.device_info_calls = 0
        self.window_size_calls = 0

    @property
    def info(self) -> dict:
        self.info_calls += 1
        return {"model": "Pixel", "sdkInt": 34}

    @property
    def device_info(self) -> dict:
        self.device_info_calls += 1
        return {"manufacturer": "Google"}

    def window_size(self) -> tuple[int, int]:
        self.window_size_calls += 1
        return (1080, 2400)


class DeviceManagerConnectTests(unittest.TestCase):
    def test_failed_connect_does_not_store_ghost_device_or_replace_existing_device(self) -> None:
        manager = DeviceManager()
        healthy_device = _HealthyDevice("serial-1", {"model": "ok"})
        manager._devices["serial-1"] = DeviceConnectionState(
            device=healthy_device,
            serial="serial-1",
            info={"model": "ok"},
        )

        with patch(
            "uiautomator2_mcp.device_manager.u2.connect",
            return_value=_FailingInfoDevice("serial-2"),
        ):
            with self.assertRaisesRegex(RuntimeError, "atx-agent not ready"):
                manager.connect("serial-2")

        self.assertEqual(manager.connected_device_ids(), ["serial-1"])
        self.assertIs(manager.get_device("serial-1"), healthy_device)

    def test_get_device_details_populates_metadata_cache_once(self) -> None:
        manager = DeviceManager()
        device = _MetadataDevice()
        manager._devices[device.serial] = DeviceConnectionState(
            device=device,
            serial=device.serial,
        )

        first = manager.get_device_details(device.serial)
        second = manager.get_device_details(device.serial)

        self.assertEqual(first, second)
        self.assertEqual(device.info_calls, 1)
        self.assertEqual(device.device_info_calls, 1)
        self.assertEqual(device.window_size_calls, 1)
        self.assertEqual(first["sdk_version"], 34)
        self.assertEqual(first["window_size"], {"width": 1080, "height": 2400})

    def test_execute_shell_normalizes_exit_code_and_stderr(self) -> None:
        manager = DeviceManager()
        device = Mock()
        device.shell.return_value = (b"hello", 7, b"boom")
        manager._devices["serial-1"] = DeviceConnectionState(
            device=device,
            serial="serial-1",
        )

        result = manager.execute_shell("echo hi", "serial-1")

        device.shell.assert_called_once_with("echo hi")
        self.assertEqual(result.output, "hello")
        self.assertEqual(result.exit_code, 7)
        self.assertEqual(result.stderr, "boom")

    def test_execute_shell_uses_shell_timeout_when_supported(self) -> None:
        manager = DeviceManager()
        shell = Mock(return_value=SimpleNamespace(output="ok", exit_code=0, stderr=""))
        device = SimpleNamespace(shell=shell)
        manager._devices["serial-1"] = DeviceConnectionState(
            device=device,
            serial="serial-1",
            shell_timeout=3.5,
        )

        manager.execute_shell("echo hi", "serial-1")

        shell.assert_called_once_with("echo hi", timeout=3.5)


if __name__ == "__main__":
    unittest.main()
