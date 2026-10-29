"""Django management command to execute automated follow-up processing (Phase 12).

Usage:
    python manage.py process_follow_ups --once
    python manage.py process_follow_ups --dry-run
    python manage.py process_follow_ups --interval=30
"""
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crm.scheduler import run_automated_followup_cycle


class ProcessLock:
    """Guards against concurrent or overlapping process_follow_ups worker runs on the same host.

    Architecture & Concurrency Semantics:
    - Implements cross-platform advisory file locking on an open file descriptor:
      * Windows: Uses `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` to acquire an exclusive non-blocking byte lock.
      * POSIX: Uses `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)` to acquire an exclusive non-blocking lock.
    - Operating-System Kernel Authority:
      * Mutual exclusion is governed directly by the OS kernel, not by reading a PID string from disk.
      * When a process terminates (normally or abnormally via SIGKILL, crash, or exception), the operating
        system kernel automatically closes all open file descriptors and frees the advisory lock.
      * Stale process crash recovery requires zero manual lock file deletion and suffers zero TOCTOU unlinking races.
    - Persistent Lock File Model:
      * The lock file is persistent and NOT unlinked during ordinary release. This eliminates competing
        inodes and guarantees race-free concurrency across simultaneous startup attempts.
      * PID and start timestamp written into the file are strictly informational metadata for system operators.
    - Deployment Boundary:
      * Single-host mutual exclusion only. In multi-container production environments (e.g. Kubernetes, AWS ECS),
        the worker must either be deployed as a singleton service or coordinate via PostgreSQL advisory locks
        (`pg_try_advisory_lock`) or Redis distributed locks.
    """

    def __init__(self, lock_name: str = "gqt_hrms_process_follow_ups.lock"):
        self.lock_path = Path(tempfile.gettempdir()) / lock_name
        self._fd: Optional[int] = None
        self._acquired: bool = False

    def acquire(self) -> bool:
        """Attempt non-blocking exclusive lock acquisition. Return True if acquired, False otherwise."""
        if self._acquired:
            return True

        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            # Open or create persistent lock file with read/write access
            fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        except OSError:
            return False

        # Apply OS-level non-blocking advisory lock
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError, PermissionError):
            # Another process currently holds the lock; close descriptor and reject
            try:
                os.close(fd)
            except OSError:
                pass
            return False

        # Lock granted by OS kernel; record informational metadata
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            payload = f"{os.getpid()}\n{int(time.time())}\n".encode("utf-8")
            os.write(fd, payload)
            if hasattr(os, "ftruncate"):
                os.ftruncate(fd, len(payload))
        except OSError:
            pass

        self._fd = fd
        self._acquired = True
        return True

    def release(self) -> None:
        """Release OS advisory lock and close the file descriptor."""
        if not self._acquired or self._fd is None:
            return

        fd = self._fd
        self._fd = None
        self._acquired = False

        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass

        try:
            os.close(fd)
        except OSError:
            pass

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire ProcessLock on {self.lock_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        """Informational utility to inspect whether a process ID is active on this host."""
        if pid <= 0:
            return False
        try:
            if sys.platform == "win32":
                import ctypes

                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                SYNCHRONIZE = 0x00100000
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid
                )
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            return False


class Command(BaseCommand):
    help = "Execute Phase 12 Automated Follow-Up and Escalation cycle (Idempotent worker)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single automation cycle and exit immediately.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect eligible follow-ups and reminders without making state mutations.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Poll interval in seconds when running as a continuous background daemon (default: 60s).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum reminder items to process per batch (default: 50).",
        )
        parser.add_argument(
            "--no-lock",
            action="store_true",
            help="Bypass single-process lock guard (used in isolated unit test environments).",
        )

    def handle(self, *args, **options):
        once = options["once"]
        dry_run = options["dry_run"]
        interval = max(options["interval"], 5)
        no_lock = options.get("no_lock", False)

        self.stdout.write(
            self.style.NOTICE(
                f"Starting GQT HRMS Automated Follow-Up Worker "
                f"[once={once}, dry_run={dry_run}, interval={interval}s]..."
            )
        )

        lock = None
        if not no_lock:
            lock = ProcessLock()
            if not lock.acquire():
                self.stdout.write(
                    self.style.WARNING(
                        f"Another instance of process_follow_ups is already active (Lock file: {lock.lock_path}). Exiting to prevent overlap."
                    )
                )
                return

        try:
            if once or dry_run:
                results = run_automated_followup_cycle(dry_run=dry_run)
                self.stdout.write(self.style.SUCCESS(f"Cycle completed successfully: {results}"))
                return

            # Continuous execution mode
            self.stdout.write(self.style.SUCCESS("Worker running. Press Ctrl+C to terminate."))
            try:
                while True:
                    results = run_automated_followup_cycle(dry_run=False)
                    self.stdout.write(
                        f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Cycle summary: {results}"
                    )
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.NOTICE("Automated follow-up worker received shutdown signal. Exiting.")
                )
        finally:
            if lock:
                lock.release()
