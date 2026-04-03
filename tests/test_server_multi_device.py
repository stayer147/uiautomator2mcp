from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import Mock, patch

from uiautomator2_mcp import server


class _FakeElement:
    exists = True
    info = {"text": "OK", "bounds": {"left": 0, "top": 0, "right": 10, "bottom": 10}}


class _FakeScrollable:
    exists = True

    def __init__(self) -> None:
        self.scroll = SimpleNamespace(
            vert=SimpleNamespace(forward=Mock(return_value=False)),
            horiz=SimpleNamespace(forward=Mock(return_value=False)),
        )


def test_recently_merged_tools_expose_device_id_parameter() -> None:
    tool_names = [
        'double_tap',
        'long_tap',
        'drag',
        'input_text',
        'find_element',
        'tap_element',
        'double_tap_element',
        'set_element_text',
        'element_exists',
        'wait_element',
        'scroll_to_element',
        'scroll',
        'fling',
        'wait_element_gone',
        'get_toast',
        'watcher_add',
        'watcher_start',
        'watcher_stop',
        'watcher_remove',
        'app_stop',
        'app_install',
        'app_uninstall',
        'app_clear',
        'app_info',
        'app_list_running',
        'screen_on',
        'screen_off',
        'unlock',
        'open_notification',
        'open_quick_settings',
        'get_clipboard',
        'set_clipboard',
        'push_file',
    ]

    missing = []
    for name in tool_names:
        signature = inspect.signature(getattr(server, name))
        if 'device_id' not in signature.parameters:
            missing.append(name)

    assert not missing, f'device_id is missing for: {missing}'


def test_double_tap_routes_to_explicit_device() -> None:
    device = Mock()

    with patch('uiautomator2_mcp.server._get_device', return_value=device) as get_device:
        result = server.double_tap(10, 20, device_id='serial-2')

    get_device.assert_called_once_with('serial-2')
    device.double_click.assert_called_once_with(10, 20)
    assert result == 'Double-tapped at (10, 20).'


def test_find_element_routes_to_explicit_device() -> None:
    device = Mock()
    device.return_value = _FakeElement()

    with patch('uiautomator2_mcp.server._get_device', return_value=device) as get_device:
        result = server.find_element(text='OK', device_id='serial-2')

    get_device.assert_called_once_with('serial-2')
    device.assert_called_once_with(text='OK')
    assert '"text": "OK"' in result


def test_scroll_routes_to_explicit_device() -> None:
    device = Mock(return_value=_FakeScrollable())

    with patch('uiautomator2_mcp.server._get_device', return_value=device) as get_device:
        result = server.scroll(device_id='serial-2')

    get_device.assert_called_once_with('serial-2')
    device.assert_called_once_with(scrollable=True)
    assert result == 'Scrolled forward. Reached end: False'


def test_unlock_turns_screen_on_and_attempts_overlay_dismissal() -> None:
    device = Mock()

    with patch('uiautomator2_mcp.server._get_device', return_value=device) as get_device:
        result = server.unlock(device_id='serial-2')

    get_device.assert_called_once_with('serial-2')
    device.screen_on.assert_called_once_with()
    device.unlock.assert_called_once_with()
    device.press.assert_any_call('back')
    device.press.assert_any_call('home')
    assert device.press.call_count == 3
    assert result == 'Device unlocked. Overlay dismissal attempted (back/back/home).'


def test_unlock_ignores_press_errors_after_successful_unlock() -> None:
    device = Mock()
    device.press.side_effect = RuntimeError('press failed')

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        result = server.unlock(device_id='serial-2')

    device.screen_on.assert_called_once_with()
    device.unlock.assert_called_once_with()
    assert result == 'Device unlocked. Overlay dismissal attempted (back/back/home).'
