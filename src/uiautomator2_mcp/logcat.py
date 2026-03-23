"""Helpers for retrieving Android logcat output via ADB."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import subprocess

THREADTIME_PATTERN = re.compile(
    r"^(?P<ts>\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+"
    r"(?P<pid>\d+)\s+"
    r"(?P<tid>\d+)\s+"
    r"(?P<level>[VDIWEFA])\s+"
    r"(?P<tag>.*)$"
)

LEVEL_ALIASES = {
    "V": "V",
    "VERBOSE": "V",
    "D": "D",
    "DEBUG": "D",
    "I": "I",
    "INFO": "I",
    "W": "W",
    "WARN": "W",
    "WARNING": "W",
    "E": "E",
    "ERROR": "E",
    "F": "F",
    "FATAL": "F",
    "A": "A",
    "ASSERT": "A",
}

LEVEL_PRIORITY = {"V": 0, "D": 1, "I": 2, "W": 3, "E": 4, "F": 5, "A": 6}


@dataclass(frozen=True)
class LogQuery:
    """Normalized logcat query parameters."""

    serial: str
    package: str | None = None
    level: str | None = None
    since: str | None = None
    lines: int = 200


def clear_logs(serial: str) -> str:
    """Clear logcat buffers for a device."""
    _run_adb(serial, "logcat", "-c")
    return f"Cleared logcat buffers for device {serial}."


def get_logs(query: LogQuery) -> str:
    """Fetch filtered logcat output for a device."""
    normalized_level = normalize_level(query.level)
    normalized_since = parse_since(query.since) if query.since else None
    lines = max(1, query.lines)
    package_pids = resolve_package_pids(query.serial, query.package) if query.package else set()

    adb_result = _run_adb(query.serial, "logcat", "-d", "-v", "threadtime")
    filtered_lines: list[str] = []

    for line in adb_result.stdout.splitlines():
        if not line.strip():
            continue
        if line.startswith("---------"):
            continue
        if _matches_filters(
            line=line,
            package=query.package,
            package_pids=package_pids,
            min_level=normalized_level,
            since_dt=normalized_since,
        ):
            filtered_lines.append(line)

    filtered_lines = filtered_lines[-lines:]

    header = [
        "Logcat query result",
        f"device: {query.serial}",
        f"package: {query.package or '(not set)'}",
        f"level: {normalized_level or '(not set)'}",
        f"since: {query.since or '(not set)'}",
        f"lines: {lines}",
        "format: threadtime",
    ]

    if query.package and not package_pids:
        header.append("package_pid_resolution: pidof returned no active PID; used line text fallback only")
    elif query.package:
        header.append(
            "package_pid_resolution: "
            + ", ".join(str(pid) for pid in sorted(package_pids))
        )

    if not filtered_lines:
        return "\n".join(
            [
                *header,
                "",
                "No log entries matched the provided filters.",
            ]
        )

    return "\n".join([*header, "", *filtered_lines])


def normalize_level(level: str | None) -> str | None:
    """Normalize log level aliases to Android one-letter priorities."""
    if level is None:
        return None
    normalized = LEVEL_ALIASES.get(level.strip().upper())
    if normalized is None:
        valid_levels = ", ".join(sorted(LEVEL_ALIASES))
        raise ValueError(f"Invalid log level {level!r}. Use one of: {valid_levels}")
    return normalized


def parse_since(value: str) -> datetime:
    """Parse a 'since' timestamp from common formats."""
    value = value.strip()
    for parser in (
        datetime.fromisoformat,
        lambda raw: datetime.strptime(raw, "%Y-%m-%d %H:%M:%S"),
        lambda raw: datetime.strptime(raw, "%Y-%m-%d %H:%M:%S.%f"),
        lambda raw: _parse_threadtime_timestamp(raw),
    ):
        try:
            return parser(value)
        except ValueError:
            continue
    raise ValueError(
        "Invalid 'since' value. Use ISO-8601, 'YYYY-MM-DD HH:MM:SS', "
        "'YYYY-MM-DD HH:MM:SS.sss', or 'MM-DD HH:MM:SS.sss'."
    )


def resolve_package_pids(serial: str, package: str | None) -> set[int]:
    """Resolve active PIDs for a package via adb shell pidof."""
    if not package:
        return set()
    result = _run_adb(serial, "shell", "pidof", package, check=False)
    if result.returncode != 0:
        return set()
    return {
        int(pid)
        for pid in result.stdout.split()
        if pid.isdigit()
    }


def _matches_filters(
    *,
    line: str,
    package: str | None,
    package_pids: set[int],
    min_level: str | None,
    since_dt: datetime | None,
) -> bool:
    """Check whether a threadtime log line matches all requested filters."""
    parsed = parse_threadtime_line(line)

    if min_level and parsed and LEVEL_PRIORITY[parsed.level] < LEVEL_PRIORITY[min_level]:
        return False

    if since_dt and parsed and parsed.timestamp < since_dt:
        return False

    if package:
        if parsed and package_pids:
            if parsed.pid in package_pids:
                return True
            return package in line
        return package in line

    return True


@dataclass(frozen=True)
class ParsedLogLine:
    """Structured representation of a logcat threadtime line."""

    timestamp: datetime
    pid: int
    level: str


def parse_threadtime_line(line: str) -> ParsedLogLine | None:
    """Parse a logcat line emitted with '-v threadtime'."""
    match = THREADTIME_PATTERN.match(line)
    if not match:
        return None
    return ParsedLogLine(
        timestamp=_parse_threadtime_timestamp(match.group("ts")),
        pid=int(match.group("pid")),
        level=match.group("level"),
    )


def _parse_threadtime_timestamp(raw: str) -> datetime:
    """Parse logcat's threadtime timestamp without a year component."""
    now = datetime.now()
    parsed = datetime.strptime(raw, "%m-%d %H:%M:%S.%f").replace(year=now.year)
    if parsed > now and (parsed - now).days >= 1:
        parsed = parsed.replace(year=now.year - 1)
    return parsed


def _run_adb(serial: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run adb for a specific serial and return the completed process."""
    command = ["adb", "-s", serial, *args]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "adb command failed"
        raise RuntimeError(f"{' '.join(command)} failed: {stderr}")
    return result
