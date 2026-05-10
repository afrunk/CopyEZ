"""
Log utilities.

Provides centralized logging helpers with automatic rotation for long-running apps.
"""

import os
import datetime


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
MAX_LOG_LINES = 200


def ensure_log_dir():
    """Ensure the logs directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)


def get_log_path(filename: str) -> str:
    """Get absolute path for a log file inside the logs/ directory."""
    ensure_log_dir()
    return os.path.join(LOG_DIR, filename)


def write_log(filename: str, content: str):
    """
    Append content to a log file, then rotate if it exceeds MAX_LOG_LINES.

    Rotation: keeps only the last MAX_LOG_LINES lines, discarding older entries.
    """
    log_path = get_log_path(filename)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")

    # Rotate if over limit
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) > MAX_LOG_LINES:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                f"[Rotated at {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()}] "
                f"Log truncated to last {MAX_LOG_LINES} lines (was {len(lines)} lines).\n"
            )
            f.writelines(lines[-MAX_LOG_LINES:])
