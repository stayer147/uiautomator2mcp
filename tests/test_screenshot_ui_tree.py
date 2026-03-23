from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from uiautomator2_mcp import server


_XML = '''<hierarchy>
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="pkg" content-desc="" clickable="false" enabled="true" focused="false" selected="false" checked="false" scrollable="false" bounds="[0,0][1080,2400]">
    <node index="1" text="Login" resource-id="com.example:id/login" class="android.widget.Button" package="pkg" content-desc="Sign in" clickable="true" enabled="true" focused="true" selected="false" checked="false" scrollable="false" bounds="[10,20][110,120]" />
    <node index="2" text="Remember me" resource-id="com.example:id/remember" class="android.widget.CheckBox" package="pkg" content-desc="" clickable="true" enabled="false" focused="false" selected="true" checked="true" scrollable="false" bounds="[10,140][220,200]" />
  </node>
</hierarchy>'''


def test_screenshot_saves_resized_jpeg(tmp_path: Path) -> None:
    image = Image.new('RGBA', (200, 100), color=(255, 0, 0, 255))
    device = Mock()
    device.screenshot.return_value = image
    save_path = tmp_path / 'screen.jpg'

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        result = server.screenshot(
            save_path=str(save_path),
            image_format='jpeg',
            max_width=100,
            quality=70,
            device_id='serial-1',
        )

    assert 'Screenshot saved to' in result
    saved = Image.open(save_path)
    assert saved.size == (100, 50)
    assert saved.format == 'JPEG'


def test_screenshot_creates_parent_directories_for_nested_save_path(tmp_path: Path) -> None:
    image = Image.new('RGB', (20, 10), color='green')
    device = Mock()
    device.screenshot.return_value = image
    save_path = tmp_path / 'nested' / 'screens' / 'screen.png'

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        result = server.screenshot(save_path=str(save_path), device_id='serial-3')

    assert 'Screenshot saved to' in result
    assert save_path.exists()
    saved = Image.open(save_path)
    assert saved.size == (20, 10)
    assert saved.format == 'PNG'


def test_screenshot_can_return_inline_image_content_without_writing_file() -> None:
    image = Image.new('RGB', (40, 20), color='blue')
    device = Mock()
    device.screenshot.return_value = image

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        result = server.screenshot(inline=True, save_path=None, max_height=10)

    assert result['mime_type'] == 'image/png'
    assert result['width'] == 20
    assert result['height'] == 10
    assert result['byte_size'] > 0
    assert result['format'] == 'png'

    decoded = base64.b64decode(result['data'])
    decoded_image = Image.open(server.io.BytesIO(decoded))
    assert decoded_image.size == (20, 10)


def test_get_ui_tree_returns_structured_elements() -> None:
    device = Mock()
    device.dump_hierarchy.return_value = _XML

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        content, elements = server.get_ui_tree(device_id='serial-2')

    assert content[0].type == 'text'
    assert isinstance(elements, list)
    assert elements[0]['class_name'] == 'android.widget.FrameLayout'
    assert elements[1] == {
        'text': 'Login',
        'resource_id': 'com.example:id/login',
        'class_name': 'android.widget.Button',
        'content_desc': 'Sign in',
        'bounds': {'left': 10, 'top': 20, 'right': 110, 'bottom': 120},
        'clickable': True,
        'enabled': True,
        'focused': True,
        'selected': False,
        'checked': False,
        'scrollable': False,
        'index': 1,
    }
    assert elements[2]['checked'] is True
    assert elements[2]['enabled'] is False


def test_get_ui_tree_can_render_json_string() -> None:
    device = Mock()
    device.dump_hierarchy.return_value = _XML

    with patch('uiautomator2_mcp.server._get_device', return_value=device):
        result = server.get_ui_tree(structured=False)

    payload = json.loads(result)
    assert payload[1]['resource_id'] == 'com.example:id/login'
    assert payload[2]['selected'] is True


def test_parse_hierarchy_compact_skips_empty_container_noise() -> None:
    compact = server._parse_hierarchy_compact(_XML)

    lines = compact.splitlines()
    assert len(lines) == 2
    assert lines[0] == '[0] Button "Login" desc="Sign in" #login [clickable] [10,20][110,120]'
    assert lines[1] == '[1] CheckBox "Remember me" #remember [clickable] [10,140][220,200]'
