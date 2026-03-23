from unittest.mock import patch

from uiautomator2_mcp import server
from uiautomator2_mcp.device_manager import ShellCommandResult


def test_device_info_uses_cached_manager_details() -> None:
    payload = {
        "device_id": "serial-1",
        "serial": "serial-1",
        "sdk_version": 34,
        "info": {"model": "Pixel"},
        "device_info": {"manufacturer": "Google"},
        "window_size": {"width": 1080, "height": 2400},
    }

    with patch(
        "uiautomator2_mcp.server.device_manager.get_device_details",
        return_value=payload,
    ) as get_details:
        result = server.device_info(device_id="serial-1")

    get_details.assert_called_once_with("serial-1")
    assert '"sdk_version": 34' in result
    assert '"manufacturer": "Google"' in result


def test_shell_routes_through_device_manager_helper() -> None:
    shell_result = ShellCommandResult(command="ls", output="out", exit_code=5, stderr="err")

    with patch(
        "uiautomator2_mcp.server.device_manager.execute_shell",
        return_value=shell_result,
    ) as execute_shell:
        result = server.shell("ls", device_id="serial-2")

    execute_shell.assert_called_once_with("ls", "serial-2")
    assert result == "Exit code 5:\nout\n[stderr]\nerr"
