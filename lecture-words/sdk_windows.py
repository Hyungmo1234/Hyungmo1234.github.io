"""Make the bundled Cursor bridge usable on this machine.

Windows cannot select() on the bridge stderr pipe (WinError 10038). The
bundled Node also ignores custom CAs in the OS store, so API calls fail
with "Network request failed" behind TLS inspection unless Node is started
with --use-system-ca.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
from typing import Any, Mapping

_SYSTEM_CA_FLAG = "--use-system-ca"
_installed = False


def configure_bridge_tls() -> None:
    current = os.environ.get("NODE_OPTIONS", "")
    if _SYSTEM_CA_FLAG in current.split():
        return
    os.environ["NODE_OPTIONS"] = f"{current} {_SYSTEM_CA_FLAG}".strip()


def install_windows_bridge() -> None:
    global _installed
    if _installed or sys.platform != "win32":
        return
    import cursor_sdk._bridge as bridge

    def _read_discovery(
        process: subprocess.Popen[str], timeout: float
    ) -> Mapping[str, Any]:
        return read_bridge_discovery(process, timeout)

    bridge._read_discovery = _read_discovery
    _installed = True


def read_bridge_discovery(
    process: subprocess.Popen[str], timeout: float
) -> Mapping[str, Any]:
    from cursor_sdk._bridge import CursorSDKError, parse_discovery_line

    if process.stderr is None:
        raise CursorSDKError("Bridge process stderr is unavailable")

    found: queue.Queue[tuple[str, object]] = queue.Queue()
    lines: list[str] = []
    lines_lock = threading.Lock()

    def snapshot() -> str:
        with lines_lock:
            return "".join(lines)

    def reader() -> None:
        stream = process.stderr
        assert stream is not None
        try:
            while True:
                line = stream.readline()
                if line == "":
                    found.put(("eof", None))
                    return
                if not line.endswith("\n"):
                    line += "\n"
                with lines_lock:
                    lines.append(line)
                discovery = parse_discovery_line(line)
                if discovery is not None:
                    found.put(("discovery", discovery))
                    while stream.readline() != "":
                        pass
                    return
        except Exception as exc:
            found.put(("error", exc))

    threading.Thread(
        target=reader, name="cursor-bridge-discovery", daemon=True
    ).start()

    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            exit_code = process.poll()
            if exit_code is not None:
                raise CursorSDKError(
                    f"Bridge exited before discovery with status {exit_code}: "
                    + snapshot()
                )
            raise CursorSDKError("Timed out waiting for bridge discovery")
        try:
            kind, payload = found.get(timeout=min(0.1, remaining))
        except queue.Empty:
            if process.poll() is None:
                continue
            try:
                kind, payload = found.get(timeout=0.2)
            except queue.Empty:
                raise CursorSDKError(
                    "Bridge exited before discovery with status "
                    f"{process.poll()}: {snapshot()}"
                ) from None
        if kind == "discovery":
            assert isinstance(payload, Mapping)
            return payload
        if kind == "error":
            assert isinstance(payload, BaseException)
            raise payload
        exit_code = process.poll()
        raise CursorSDKError(
            f"Bridge exited before discovery with status {exit_code}: " + snapshot()
        )
