"""
SlopeSniper Daemon - Background target monitoring and execution.

Runs as a background process to monitor sell targets and execute trades
when conditions are met.

Usage:
    slopesniper daemon start    # Start the daemon
    slopesniper daemon stop     # Stop the daemon
    slopesniper daemon status   # Check daemon status
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tools.config import SLOPESNIPER_DIR

# Daemon files
PID_FILE = SLOPESNIPER_DIR / "daemon.pid"
LOG_FILE = SLOPESNIPER_DIR / "daemon.log"

# Default polling interval (seconds)
DEFAULT_POLL_INTERVAL = 15


def _setup_logger() -> logging.Logger:
    """Configure daemon logging."""
    logger = logging.getLogger("slopesniper.daemon")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # File handler
    SLOPESNIPER_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


class SlopeSniperDaemon:
    """Background daemon for target monitoring."""

    def __init__(self, poll_interval: int = DEFAULT_POLL_INTERVAL):
        self.poll_interval = poll_interval
        self.running = False
        self.logger = _setup_logger()

    async def run(self) -> None:
        """Main daemon loop."""
        self.running = True
        self.logger.info(f"Daemon started (interval: {self.poll_interval}s)")

        while self.running:
            try:
                await self._check_cycle()
            except Exception as e:
                self.logger.error(f"Check cycle error: {e}")

            # Use asyncio.sleep for proper async behavior
            await asyncio.sleep(self.poll_interval)

        self.logger.info("Daemon stopped")

    async def _check_cycle(self) -> None:
        """Single check cycle for all targets."""
        from .tools.targets import (
            TargetType,
            check_target,
            execute_target_sell,
            get_active_targets,
            get_target,
            mark_target_triggered,
            poll_targets_batch,
            update_trailing_peak,
        )

        targets = get_active_targets()

        if not targets:
            return

        self.logger.debug(f"Checking {len(targets)} active targets")

        # Batch fetch prices
        price_data = await poll_targets_batch(targets)

        for target in targets:
            try:
                data = price_data.get(target.mint, {})
                current_price = data.get("price_usd", 0)
                current_mcap = data.get("mcap")

                if current_price <= 0:
                    continue

                # Update trailing stop peak
                if target.target_type == TargetType.TRAILING_STOP:
                    update_trailing_peak(target.id, current_price)
                    # Refresh target to get updated peak
                    refreshed = get_target(target.id)
                    if refreshed:
                        target = refreshed

                # Check if target is met
                if check_target(target, current_price, current_mcap):
                    self.logger.info(
                        f"TARGET TRIGGERED: {target.symbol} ({target.target_type.value}) "
                        f"at ${current_price:.8g}"
                    )

                    # Mark as triggered
                    mark_target_triggered(target.id, current_price)

                    # Execute sell
                    result = await execute_target_sell(target, current_price)

                    if result.get("success") or result.get("auto_executed"):
                        self.logger.info(
                            f"SOLD: {target.symbol} - sig: {result.get('signature', 'N/A')}"
                        )
                    else:
                        self.logger.error(
                            f"SELL FAILED: {target.symbol} - {result.get('error')}"
                        )

            except Exception as e:
                self.logger.error(f"Error checking target {target.id}: {e}")

    def stop(self) -> None:
        """Signal daemon to stop."""
        self.running = False


def write_pid() -> None:
    """Write current PID to file."""
    SLOPESNIPER_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    os.chmod(PID_FILE, 0o600)


def read_pid() -> int | None:
    """Read daemon PID from file."""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except ValueError:
        return None


def is_daemon_running() -> bool:
    """Check if daemon is running."""
    pid = read_pid()
    if pid is None:
        return False

    try:
        os.kill(pid, 0)  # Signal 0 checks if process exists
        return True
    except OSError:
        # Process doesn't exist, clean up stale PID file
        PID_FILE.unlink(missing_ok=True)
        return False


def start_daemon(poll_interval: int = DEFAULT_POLL_INTERVAL) -> dict[str, Any]:
    """
    Start daemon as background process.

    Returns dict with status and PID.
    """
    if is_daemon_running():
        return {"error": "Daemon already running", "pid": read_pid()}

    # Fork to background
    try:
        pid = os.fork()
    except OSError as e:
        return {"error": f"Fork failed: {e}"}

    if pid > 0:
        # Parent process - wait briefly to ensure child starts
        time.sleep(0.5)
        if is_daemon_running():
            return {
                "success": True,
                "pid": read_pid(),
                "message": "Daemon started",
                "log_file": str(LOG_FILE),
            }
        return {"error": "Daemon failed to start, check logs", "log_file": str(LOG_FILE)}

    # Child process - become daemon
    try:
        os.setsid()  # Create new session
    except OSError:
        pass

    # Fork again to prevent zombie
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    # Write PID
    write_pid()

    # Setup signal handlers
    daemon = SlopeSniperDaemon(poll_interval=poll_interval)

    def handle_sigterm(signum: int, frame: Any) -> None:
        daemon.stop()

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    # Redirect stdout/stderr to log
    sys.stdout = open(LOG_FILE, "a")  # noqa: SIM115
    sys.stderr = sys.stdout

    # Run daemon
    try:
        asyncio.run(daemon.run())
    except Exception as e:
        daemon.logger.error(f"Daemon crashed: {e}")
    finally:
        # Cleanup
        PID_FILE.unlink(missing_ok=True)
        sys.exit(0)


def stop_daemon() -> dict[str, Any]:
    """Stop running daemon."""
    pid = read_pid()

    if pid is None:
        return {"error": "No daemon running (no PID file)"}

    if not is_daemon_running():
        PID_FILE.unlink(missing_ok=True)
        return {"error": "Daemon not running (stale PID file cleaned up)"}

    try:
        os.kill(pid, signal.SIGTERM)

        # Wait for process to exit (up to 5 seconds)
        for _ in range(50):
            if not is_daemon_running():
                PID_FILE.unlink(missing_ok=True)
                return {"success": True, "message": "Daemon stopped"}
            time.sleep(0.1)

        # Force kill if still running
        os.kill(pid, signal.SIGKILL)
        PID_FILE.unlink(missing_ok=True)
        return {"success": True, "message": "Daemon force stopped"}

    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        return {"success": True, "message": "Daemon already stopped"}


def get_daemon_status() -> dict[str, Any]:
    """Get daemon status."""
    running = is_daemon_running()
    pid = read_pid()

    status: dict[str, Any] = {
        "running": running,
        "pid": pid if running else None,
        "pid_file": str(PID_FILE),
        "log_file": str(LOG_FILE),
    }

    if running:
        # Get active target count
        from .tools.targets import get_active_targets

        targets = get_active_targets()
        status["active_targets"] = len(targets)

    # Recent log entries
    if LOG_FILE.exists():
        try:
            lines = LOG_FILE.read_text().strip().split("\n")
            status["recent_logs"] = lines[-5:]  # Last 5 lines
        except Exception:
            pass

    return status


def get_daemon_logs(tail: int = 50) -> dict[str, Any]:
    """Get daemon log entries."""
    if not LOG_FILE.exists():
        return {"logs": [], "message": "No log file found"}

    try:
        lines = LOG_FILE.read_text().strip().split("\n")
        return {
            "logs": lines[-tail:] if tail > 0 else lines,
            "total_lines": len(lines),
            "showing": min(tail, len(lines)),
            "log_file": str(LOG_FILE),
        }
    except Exception as e:
        return {"error": f"Failed to read logs: {e}"}
