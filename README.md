# uiautomator2-mcp

MCP (Model Context Protocol) server for Android device automation via [uiautomator2](https://github.com/openatx/uiautomator2).

Enables AI agents (Claude, etc.) to control Android devices — tap, swipe, type text, take screenshots, manage apps, and more.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
- Android device with USB debugging enabled (or an emulator)
- ADB installed and device visible via `adb devices`

## Quick Start

### Claude Code — one command to add & auto-run:

```bash
claude mcp add uiautomator2 -- uvx uiautomator2-mcp
```

That's it. Claude will auto-launch the server when needed.

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uiautomator2": {
      "command": "uvx",
      "args": ["uiautomator2-mcp"]
    }
  }
}
```

### Before PyPI publish — install from git

```bash
# Claude Code
claude mcp add uiautomator2 -- uvx --from "git+https://github.com/stayer147/uiautomator2mcp" uiautomator2-mcp

# Claude Desktop — use in config:
{
  "command": "uvx",
  "args": ["--from", "git+https://github.com/stayer147/uiautomator2mcp", "uiautomator2-mcp"]
}
```

### Alternative methods

```bash
# Using pipx
pipx run uiautomator2-mcp

# Using pip (global install)
pip install uiautomator2-mcp
uiautomator2-mcp

# Using python -m
pip install uiautomator2-mcp
python -m uiautomator2_mcp

# From source
git clone https://github.com/stayer147/uiautomator2mcp.git
cd uiautomator2mcp
pip install -e .
uiautomator2-mcp
```

## Available Tools (36)

### Connection
| Tool | Description |
|------|-------------|
| `connect` | Connect to a device by serial/IP or auto-detect |
| `disconnect` | Disconnect from the current device |
| `device_info` | Get device model, screen size, Android version |

### UI Interaction
| Tool | Description |
|------|-------------|
| `tap` | Tap at screen coordinates |
| `double_tap` | Double-tap at coordinates |
| `long_tap` | Long-press at coordinates |
| `swipe` | Swipe between two points |
| `drag` | Drag between two points |
| `input_text` | Type text into the focused field |
| `press_key` | Press a device key (home, back, enter, etc.) |

### Element Operations
| Tool | Description |
|------|-------------|
| `find_element` | Find element by text, resource ID, class, description, or XPath |
| `tap_element` | Find and tap an element |
| `double_tap_element` | Find and double-tap an element by selector or XPath |
| `set_element_text` | Set text in an input field |
| `element_exists` | Check if an element exists |
| `wait_element` | Wait for an element to appear |

### Screenshots & UI Hierarchy
| Tool | Description |
|------|-------------|
| `screenshot` | Take a screenshot (base64 PNG) |
| `dump_hierarchy` | Get XML UI hierarchy |

### App Management
| Tool | Description |
|------|-------------|
| `app_start` | Launch an app |
| `app_stop` | Force-stop an app |
| `app_install` | Install an APK |
| `app_uninstall` | Uninstall an app |
| `app_clear` | Clear app data |
| `app_info` | Get app information |
| `app_list_running` | List running apps |
| `current_app` | Get current foreground app |

### Device Control
| Tool | Description |
|------|-------------|
| `screen_on` | Wake up the device |
| `screen_off` | Turn off the screen |
| `unlock` | Unlock the device |
| `open_notification` | Open notification panel |
| `open_quick_settings` | Open quick settings |
| `get_clipboard` | Get clipboard content |
| `set_clipboard` | Set clipboard content |

### Shell & Files
| Tool | Description |
|------|-------------|
| `shell` | Run a shell command on the device |
| `push_file` | Push a file to the device |
| `pull_file` | Pull a file from the device |

## Example Workflow

1. **Connect** to a device: `connect("emulator-5554")`
2. **Take a screenshot** to see the current screen
3. **Dump hierarchy** to understand the UI structure
4. **Tap elements** by text or resource ID
5. **Double-tap directly via XPath** when needed, e.g. `double_tap_element(xpath="//android.widget.TextView[@text='Gallery']")`
6. **Type text** into input fields
7. **Take another screenshot** to verify results

## Publishing to PyPI

```bash
uv build
uv publish
```

After publishing, `uvx uiautomator2-mcp` will work out of the box.

## License

MIT
