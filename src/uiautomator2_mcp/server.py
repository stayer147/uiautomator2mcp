"""MCP server for Android device automation via uiautomator2."""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from uiautomator2_mcp.device_manager import device_manager

mcp = FastMCP(
    "uiautomator2",
    instructions="Android device automation via uiautomator2. Connect to a device first, then use tools to interact with it.",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_selector(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
) -> dict[str, str]:
    """Build a uiautomator2 selector dict from optional parameters."""
    selector: dict[str, str] = {}
    if text is not None:
        selector["text"] = text
    if resource_id is not None:
        selector["resourceId"] = resource_id
    if class_name is not None:
        selector["className"] = class_name
    if description is not None:
        selector["description"] = description
    return selector


def _format_element_info(info: dict[str, Any]) -> str:
    """Format element info as readable JSON."""
    return json.dumps(info, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Connection tools
# ---------------------------------------------------------------------------

@mcp.tool()
def connect(serial: str | None = None) -> str:
    """Connect to an Android device.

    Args:
        serial: Device serial number or IP address (e.g. "emulator-5554" or "192.168.1.100").
                If not provided, connects to the first available device.
    """
    try:
        info = device_manager.connect(serial)
        target = serial or "default device"
        return f"Connected to {target}.\n\nDevice info:\n{_format_element_info(info)}"
    except Exception as e:
        return f"Failed to connect: {e}"


@mcp.tool()
def disconnect() -> str:
    """Disconnect from the current Android device."""
    device_manager.disconnect()
    return "Disconnected."


@mcp.tool()
def device_info() -> str:
    """Get detailed information about the connected device (model, screen size, Android version, etc.)."""
    try:
        d = device_manager.get_device()
        info = d.info
        device = d.device_info
        window = d.window_size()
        result = {
            "info": info,
            "device_info": device,
            "window_size": {"width": window[0], "height": window[1]},
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# UI interaction tools
# ---------------------------------------------------------------------------

@mcp.tool()
def tap(x: int, y: int) -> str:
    """Tap at the given screen coordinates.

    Args:
        x: Horizontal coordinate (pixels from left).
        y: Vertical coordinate (pixels from top).
    """
    try:
        d = device_manager.get_device()
        d.click(x, y)
        return f"Tapped at ({x}, {y})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def double_tap(x: int, y: int) -> str:
    """Double-tap at the given screen coordinates.

    Args:
        x: Horizontal coordinate.
        y: Vertical coordinate.
    """
    try:
        d = device_manager.get_device()
        d.double_click(x, y)
        return f"Double-tapped at ({x}, {y})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def long_tap(x: int, y: int, duration: float = 1.0) -> str:
    """Long-press at the given screen coordinates.

    Args:
        x: Horizontal coordinate.
        y: Vertical coordinate.
        duration: Hold duration in seconds (default 1.0).
    """
    try:
        d = device_manager.get_device()
        d.long_click(x, y, duration=duration)
        return f"Long-tapped at ({x}, {y}) for {duration}s."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def swipe(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.5,
) -> str:
    """Swipe from one point to another.

    Args:
        start_x: Start horizontal coordinate.
        start_y: Start vertical coordinate.
        end_x: End horizontal coordinate.
        end_y: End vertical coordinate.
        duration: Swipe duration in seconds (default 0.5).
    """
    try:
        d = device_manager.get_device()
        d.swipe(start_x, start_y, end_x, end_y, duration=duration)
        return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.5,
) -> str:
    """Drag from one point to another.

    Args:
        start_x: Start horizontal coordinate.
        start_y: Start vertical coordinate.
        end_x: End horizontal coordinate.
        end_y: End vertical coordinate.
        duration: Drag duration in seconds (default 0.5).
    """
    try:
        d = device_manager.get_device()
        d.drag(start_x, start_y, end_x, end_y, duration=duration)
        return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def input_text(text: str) -> str:
    """Type text using the keyboard. The focused input field will receive the text.

    Args:
        text: The text to type.
    """
    try:
        d = device_manager.get_device()
        d.send_keys(text)
        return f"Typed: {text!r}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def press_key(key: str) -> str:
    """Press a device key.

    Args:
        key: Key name — one of: home, back, enter, menu, recent,
             volume_up, volume_down, power, delete, tab, space.
    """
    try:
        d = device_manager.get_device()
        d.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Element tools
# ---------------------------------------------------------------------------

@mcp.tool()
def find_element(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
) -> str:
    """Find a UI element and return its properties (bounds, text, class, etc.).

    Provide at least one selector. If xpath is given, it takes precedence.

    Args:
        text: Exact text of the element.
        resource_id: Resource ID (e.g. "com.example:id/button").
        class_name: Class name (e.g. "android.widget.Button").
        description: Content description.
        xpath: XPath expression (e.g. "//android.widget.TextView[@text='Hello']").
    """
    try:
        d = device_manager.get_device()
        if xpath:
            elem = d.xpath(xpath)
            if elem.exists:
                info = elem.get()
                return _format_element_info(info.info)
            return f"Element not found with xpath: {xpath}"
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector (text, resource_id, class_name, description, or xpath)."
        elem = d(**selector)
        if elem.exists:
            return _format_element_info(elem.info)
        return f"Element not found with selector: {selector}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def tap_element(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
) -> str:
    """Find a UI element and tap on it.

    Provide at least one selector. If xpath is given, it takes precedence.

    Args:
        text: Exact text of the element.
        resource_id: Resource ID (e.g. "com.example:id/button").
        class_name: Class name (e.g. "android.widget.Button").
        description: Content description.
        xpath: XPath expression.
    """
    try:
        d = device_manager.get_device()
        if xpath:
            elem = d.xpath(xpath)
            if elem.exists:
                elem.click()
                return f"Tapped element (xpath: {xpath})."
            return f"Element not found with xpath: {xpath}"
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector."
        elem = d(**selector)
        if elem.exists:
            elem.click()
            return f"Tapped element: {selector}"
        return f"Element not found with selector: {selector}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def set_element_text(
    value: str,
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
) -> str:
    """Set text in an input field identified by a selector.

    Args:
        value: The text to set.
        text: Current text of the element.
        resource_id: Resource ID of the element.
        class_name: Class name of the element.
        description: Content description of the element.
        xpath: XPath expression.
    """
    try:
        d = device_manager.get_device()
        if xpath:
            elem = d.xpath(xpath)
            if elem.exists:
                elem.set_text(value)
                return f"Set text to {value!r} (xpath: {xpath})."
            return f"Element not found with xpath: {xpath}"
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector."
        elem = d(**selector)
        if elem.exists:
            elem.set_text(value)
            return f"Set text to {value!r} on element: {selector}"
        return f"Element not found with selector: {selector}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def element_exists(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
) -> str:
    """Check whether a UI element exists on screen.

    Args:
        text: Exact text of the element.
        resource_id: Resource ID.
        class_name: Class name.
        description: Content description.
        xpath: XPath expression.
    """
    try:
        d = device_manager.get_device()
        if xpath:
            exists = d.xpath(xpath).exists
            return json.dumps({"exists": exists, "xpath": xpath})
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector."
        exists = d(**selector).exists
        return json.dumps({"exists": exists, "selector": selector})
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def wait_element(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
    timeout: float = 10.0,
) -> str:
    """Wait for a UI element to appear on screen.

    Args:
        text: Exact text of the element.
        resource_id: Resource ID.
        class_name: Class name.
        description: Content description.
        xpath: XPath expression.
        timeout: Maximum wait time in seconds (default 10).
    """
    try:
        d = device_manager.get_device()
        if xpath:
            found = d.xpath(xpath).wait(timeout=timeout)
            if found:
                return f"Element appeared (xpath: {xpath})."
            return f"Timeout ({timeout}s): element not found (xpath: {xpath})."
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector."
        found = d(**selector).wait(timeout=timeout)
        if found:
            return f"Element appeared: {selector}"
        return f"Timeout ({timeout}s): element not found: {selector}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Scroll & fling tools
# ---------------------------------------------------------------------------

@mcp.tool()
def scroll_to_element(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    direction: str = "vertical",
    max_swipes: int = 50,
    reset_first: bool = True,
) -> str:
    """Scroll a scrollable container until a target element is found.

    Uses Android's native UiScrollable scrollTo, which is the most reliable
    way to find elements in long lists. Optionally resets scroll position
    to the beginning first for maximum reliability.

    Args:
        text: Exact text of the target element.
        resource_id: Resource ID of the target element.
        class_name: Class name of the target element.
        description: Content description of the target element.
        direction: Scroll direction — "vertical" (default) or "horizontal".
        max_swipes: Maximum number of swipes when resetting to beginning (default 50).
        reset_first: If True (default), scroll to beginning before searching.
                     Set to False if you know the element is ahead of current position.
    """
    try:
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector (text, resource_id, class_name, description)."
        d = device_manager.get_device()
        scrollable = d(scrollable=True)
        if not scrollable.exists:
            return "Error: no scrollable container found on screen."
        is_vertical = direction.lower() != "horizontal"
        scroll_obj = scrollable.scroll.vert if is_vertical else scrollable.scroll.horiz
        if reset_first:
            scroll_obj.toBeginning(max_swipes=max_swipes)
        scroll_obj.to(**selector)
        target = d(**selector)
        if target.exists:
            return f"Found element after scrolling: {_format_element_info(target.info)}"
        return f"Element not found after scrolling through the list: {selector}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def scroll(
    direction: str = "forward",
    orientation: str = "vertical",
    steps: int = 55,
) -> str:
    """Scroll the screen in a given direction.

    Uses Android's native UiScrollable for reliable scrolling.

    Args:
        direction: "forward" (default) or "backward".
        orientation: "vertical" (default) or "horizontal".
        steps: Number of steps (higher = slower scroll). Default 55.
    """
    try:
        d = device_manager.get_device()
        scrollable = d(scrollable=True)
        if not scrollable.exists:
            return "Error: no scrollable container found on screen."
        scroll_obj = scrollable.scroll.vert if orientation.lower() != "horizontal" else scrollable.scroll.horiz
        if direction.lower() == "backward":
            reached_end = scroll_obj.backward(steps=steps)
        else:
            reached_end = scroll_obj.forward(steps=steps)
        return f"Scrolled {direction}. Reached end: {reached_end}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def fling(
    direction: str = "forward",
    orientation: str = "vertical",
    max_swipes: int = 500,
) -> str:
    """Fling (fast scroll) the screen. Faster than scroll, but less precise.

    Args:
        direction: "forward", "backward", "toBeginning", or "toEnd". Default "forward".
        orientation: "vertical" (default) or "horizontal".
        max_swipes: Maximum swipes for toBeginning/toEnd (default 500).
    """
    try:
        d = device_manager.get_device()
        scrollable = d(scrollable=True)
        if not scrollable.exists:
            return "Error: no scrollable container found on screen."
        fling_obj = scrollable.fling.vert if orientation.lower() != "horizontal" else scrollable.fling.horiz
        dir_lower = direction.lower()
        if dir_lower == "backward":
            result = fling_obj.backward()
        elif dir_lower == "tobeginning":
            result = fling_obj.toBeginning(max_swipes=max_swipes)
        elif dir_lower == "toend":
            result = fling_obj.toEnd(max_swipes=max_swipes)
        elif dir_lower == "forward":
            result = fling_obj.forward()
        else:
            return f"Error: invalid direction '{direction}'. Use: forward, backward, toBeginning, toEnd."
        return f"Flung {direction}. Reached end: {result}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Wait tools
# ---------------------------------------------------------------------------

@mcp.tool()
def wait_element_gone(
    text: str | None = None,
    resource_id: str | None = None,
    class_name: str | None = None,
    description: str | None = None,
    xpath: str | None = None,
    timeout: float = 10.0,
) -> str:
    """Wait for a UI element to disappear from the screen.

    Useful for waiting for loading indicators, dialogs, or splash screens to go away.

    Args:
        text: Exact text of the element.
        resource_id: Resource ID.
        class_name: Class name.
        description: Content description.
        xpath: XPath expression.
        timeout: Maximum wait time in seconds (default 10).
    """
    try:
        d = device_manager.get_device()
        if xpath:
            gone = d.xpath(xpath).wait_gone(timeout=timeout)
            if gone:
                return f"Element gone (xpath: {xpath})."
            return f"Timeout ({timeout}s): element still present (xpath: {xpath})."
        selector = _build_selector(text, resource_id, class_name, description)
        if not selector:
            return "Error: provide at least one selector."
        gone = d(**selector).wait_gone(timeout=timeout)
        if gone:
            return f"Element gone: {selector}"
        return f"Timeout ({timeout}s): element still present: {selector}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Toast tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_toast(
    wait_timeout: float = 10.0,
    reset_first: bool = True,
) -> str:
    """Wait for and capture a toast message on screen.

    Call this BEFORE triggering the action that shows the toast, or immediately after.
    Toasts are ephemeral — they disappear quickly.

    Args:
        wait_timeout: Maximum seconds to wait for a toast (default 10).
        reset_first: If True (default), clear any previously cached toast first.
    """
    try:
        d = device_manager.get_device()
        if reset_first:
            d.toast.reset()
        message = d.toast.get_message(wait_timeout=wait_timeout, default=None)
        if message is None:
            return f"No toast detected within {wait_timeout}s."
        return json.dumps({"toast_message": message})
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Watcher tools
# ---------------------------------------------------------------------------

@mcp.tool()
def watcher_add(
    name: str,
    xpath_conditions: list[str],
    action: str = "click",
    press_key: str | None = None,
) -> str:
    """Register a watcher that auto-handles UI elements when they appear.

    Watchers run in the background and automatically respond to system dialogs,
    permission prompts, popups, etc. Call watcher_start() after adding watchers.

    Args:
        name: Unique name for this watcher (used to remove it later).
        xpath_conditions: List of XPath expressions that must ALL match to trigger.
                          For simple text matching, use "//*[@text='Allow']".
                          The action is performed on the LAST element in the list.
        action: What to do when triggered — "click" (default) or "press".
        press_key: Key to press if action is "press" (e.g. "back", "home").
    """
    try:
        d = device_manager.get_device()
        w = d.watcher(name)
        for xpath in xpath_conditions:
            w = w.when(xpath)
        if action.lower() == "press":
            if not press_key:
                return "Error: press_key is required when action is 'press'."
            w.press(press_key)
        else:
            w.click()
        return f"Watcher '{name}' added: conditions={xpath_conditions}, action={action}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def watcher_start(interval: float = 2.0) -> str:
    """Start the background watcher that polls for registered conditions.

    Must be called after adding watchers with watcher_add.

    Args:
        interval: Polling interval in seconds (default 2.0). Lower = more responsive but more CPU.
    """
    try:
        d = device_manager.get_device()
        if d.watcher.running():
            return "Watcher is already running."
        d.watcher.start(interval=interval)
        return f"Watcher started (polling every {interval}s)."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def watcher_stop() -> str:
    """Stop the background watcher."""
    try:
        d = device_manager.get_device()
        if not d.watcher.running():
            return "Watcher is not running."
        d.watcher.stop()
        return "Watcher stopped."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def watcher_remove(name: str | None = None) -> str:
    """Remove registered watchers.

    Args:
        name: Name of a specific watcher to remove. If not provided, removes ALL watchers.
    """
    try:
        d = device_manager.get_device()
        if name:
            d.watcher.remove(name)
            return f"Watcher '{name}' removed."
        else:
            d.watcher.remove()
            return "All watchers removed."
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Screenshot & hierarchy
# ---------------------------------------------------------------------------

@mcp.tool()
def screenshot(save_path: str = "/tmp/screenshot.png") -> str:
    """Take a screenshot and save it to a file.

    Returns the file path. The agent can then open the file to view it.
    Format is determined by file extension (.png or .jpg/.jpeg).

    Args:
        save_path: Path to save the screenshot (default "/tmp/screenshot.png").
                   Use .jpg extension for smaller file size.
    """
    try:
        d = device_manager.get_device()
        img = d.screenshot()
        img.save(save_path)
        width, height = img.size
        file_size = os.path.getsize(save_path)
        return (
            f"Screenshot saved to {save_path} "
            f"({width}x{height}, {file_size // 1024}KB)"
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def dump_hierarchy(compact: bool = True) -> str:
    """Dump the current UI hierarchy.

    Args:
        compact: If True (default), return a concise one-line-per-element format.
                 If False, return the full XML. Compact mode is 10-50x smaller.
    """
    try:
        d = device_manager.get_device()
        xml_str = d.dump_hierarchy()
        if not compact:
            return xml_str
        return _parse_hierarchy_compact(xml_str)
    except Exception as e:
        return f"Error: {e}"


def _parse_hierarchy_compact(xml_str: str) -> str:
    """Parse UI hierarchy XML into a compact text format."""
    from lxml import etree

    root = etree.fromstring(xml_str.encode("utf-8"))
    lines: list[str] = []
    idx = 0
    for node in root.iter("node"):
        text = node.get("text", "")
        resource_id = node.get("resource-id", "")
        class_name = node.get("class", "")
        description = node.get("content-desc", "")
        bounds = node.get("bounds", "")
        clickable = node.get("clickable", "false")

        # Skip empty containers that add noise
        if not text and not resource_id and not description:
            if class_name in (
                "android.view.View",
                "android.widget.FrameLayout",
                "android.widget.LinearLayout",
                "android.widget.RelativeLayout",
            ):
                continue

        parts = [f"[{idx}]"]
        # Short class name (strip android.widget. prefix)
        short_class = class_name.replace("android.widget.", "").replace(
            "android.view.", ""
        )
        parts.append(short_class)
        if text:
            parts.append(f'"{text}"')
        if description:
            parts.append(f'desc="{description}"')
        if resource_id:
            # Shorten com.package.name:id/foo → id/foo
            short_id = resource_id.split(":id/")[-1] if ":id/" in resource_id else resource_id
            parts.append(f"#{short_id}")
        if clickable == "true":
            parts.append("[clickable]")
        parts.append(bounds)

        lines.append(" ".join(parts))
        idx += 1

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# App management tools
# ---------------------------------------------------------------------------

@mcp.tool()
def app_start(package: str, activity: str | None = None) -> str:
    """Launch an application.

    Args:
        package: Package name (e.g. "com.android.settings").
        activity: Activity name (optional). If omitted, launches the default activity.
    """
    try:
        d = device_manager.get_device()
        if activity:
            d.app_start(package, activity)
        else:
            d.app_start(package)
        return f"Started {package}" + (f"/{activity}" if activity else "") + "."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_stop(package: str) -> str:
    """Force-stop an application.

    Args:
        package: Package name (e.g. "com.android.settings").
    """
    try:
        d = device_manager.get_device()
        d.app_stop(package)
        return f"Stopped {package}."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_install(path: str) -> str:
    """Install an APK file on the device.

    Args:
        path: Local path to the APK file.
    """
    try:
        d = device_manager.get_device()
        d.app_install(path)
        return f"Installed APK from {path}."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_uninstall(package: str) -> str:
    """Uninstall an application from the device.

    Args:
        package: Package name to uninstall.
    """
    try:
        d = device_manager.get_device()
        d.app_uninstall(package)
        return f"Uninstalled {package}."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_clear(package: str) -> str:
    """Clear all data for an application.

    Args:
        package: Package name.
    """
    try:
        d = device_manager.get_device()
        d.app_clear(package)
        return f"Cleared data for {package}."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_info(package: str) -> str:
    """Get information about an installed application.

    Args:
        package: Package name.
    """
    try:
        d = device_manager.get_device()
        info = d.app_info(package)
        return json.dumps(info, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def app_list_running() -> str:
    """List all currently running applications. Returns a list of package names."""
    try:
        d = device_manager.get_device()
        apps = d.app_list_running()
        return json.dumps(apps, indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def current_app() -> str:
    """Get information about the currently focused application (package name and activity)."""
    try:
        d = device_manager.get_device()
        info = d.app_current()
        return json.dumps(info, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Device control tools
# ---------------------------------------------------------------------------

@mcp.tool()
def screen_on() -> str:
    """Turn the screen on (wake up the device)."""
    try:
        d = device_manager.get_device()
        d.screen_on()
        return "Screen turned on."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def screen_off() -> str:
    """Turn the screen off."""
    try:
        d = device_manager.get_device()
        d.screen_off()
        return "Screen turned off."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def unlock() -> str:
    """Unlock the device (turns screen on and swipes to unlock)."""
    try:
        d = device_manager.get_device()
        d.unlock()
        return "Device unlocked."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def open_notification() -> str:
    """Open the notification panel."""
    try:
        d = device_manager.get_device()
        d.open_notification()
        return "Notification panel opened."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def open_quick_settings() -> str:
    """Open the quick settings panel."""
    try:
        d = device_manager.get_device()
        d.open_quick_settings()
        return "Quick settings opened."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_clipboard() -> str:
    """Get the current clipboard content."""
    try:
        d = device_manager.get_device()
        content = d.clipboard
        return content or "(clipboard is empty)"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def set_clipboard(text: str) -> str:
    """Set the device clipboard content.

    Args:
        text: Text to put in the clipboard.
    """
    try:
        d = device_manager.get_device()
        d.set_clipboard(text)
        return f"Clipboard set to: {text!r}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Shell & file tools
# ---------------------------------------------------------------------------

@mcp.tool()
def shell(command: str) -> str:
    """Execute a shell command on the device and return the output.

    Args:
        command: Shell command to execute (e.g. "ls /sdcard").
    """
    try:
        d = device_manager.get_device()
        result = d.shell(command)
        if isinstance(result, tuple):
            output, exit_code = result
            if exit_code != 0:
                return f"Exit code {exit_code}:\n{output}"
            return output
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def push_file(local: str, remote: str) -> str:
    """Push a local file to the device.

    Args:
        local: Local file path.
        remote: Destination path on the device (e.g. "/sdcard/file.txt").
    """
    try:
        d = device_manager.get_device()
        d.push(local, remote)
        return f"Pushed {local} -> {remote}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def pull_file(remote: str, local: str) -> str:
    """Pull a file from the device to local filesystem.

    Args:
        remote: File path on the device (e.g. "/sdcard/file.txt").
        local: Local destination path.
    """
    try:
        d = device_manager.get_device()
        d.pull(remote, local)
        return f"Pulled {remote} -> {local}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
