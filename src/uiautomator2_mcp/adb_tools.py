"""ADB and Android SDK helper utilities."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess


def list_devices() -> list[dict[str, str]]:
    """List devices visible to adb."""
    result = _run_command(["adb", "devices", "-l"])
    devices: list[dict[str, str]] = []

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices attached"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue

        device: dict[str, str] = {
            "serial": parts[0],
            "state": parts[1],
        }
        for token in parts[2:]:
            if ":" not in token:
                continue
            key, value = token.split(":", 1)
            device[key] = value
        devices.append(device)

    return devices


def list_avds() -> list[str]:
    """List configured Android Virtual Devices."""
    emulator_path = _find_emulator_binary()
    result = _run_command([emulator_path, "-list-avds"])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def start_emulator(
    avd_name: str,
    *,
    no_window: bool = False,
    wipe_data: bool = False,
) -> dict[str, str | int | bool]:
    """Start an Android emulator process in the background."""
    emulator_path = _find_emulator_binary()
    available_avds = list_avds()
    if avd_name not in available_avds:
        raise RuntimeError(
            f"AVD {avd_name!r} not found. Available AVDs: {', '.join(available_avds) or '(none)'}"
        )

    command = [emulator_path, f"@{avd_name}"]
    if no_window:
        command.append("-no-window")
    if wipe_data:
        command.append("-wipe-data")

    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {
        "avd_name": avd_name,
        "pid": process.pid,
        "no_window": no_window,
        "wipe_data": wipe_data,
    }


def _find_emulator_binary() -> str:
    """Locate the Android emulator executable."""
    emulator = shutil.which("emulator")
    if emulator:
        return emulator

    for env_var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        root = os.environ.get(env_var)
        if not root:
            continue
        candidate = Path(root) / "emulator" / "emulator"
        if candidate.exists():
            return str(candidate)

    raise RuntimeError(
        "Android emulator binary not found. Install Android SDK emulator or set ANDROID_HOME/ANDROID_SDK_ROOT."
    )


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and raise a helpful error on failure."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise RuntimeError(f"{' '.join(command)} failed: {stderr}")
    return result
