from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from pathlib import Path

from services.mobile_api import MobileApiServer, build_mobile_api_server
from services.mobile_share import DEFAULT_MOBILE_PORT, is_mobile_backend_reachable

HEALTH_CHECK_TIMEOUT = 1.2
HEALTH_CHECK_POLL_INTERVAL = 0.05
HEALTH_CHECK_REACHABLE_TIMEOUT = 0.25
THREAD_SHUTDOWN_TIMEOUT = 2


@dataclass(slots=True)
class MobileBackendStartResult:
    running: bool
    owned: bool
    reused_existing: bool
    message: str = ""


class MobileBackendManager:
    def __init__(self, root: Path, host: str = "0.0.0.0", port: int = DEFAULT_MOBILE_PORT) -> None:
        self.root = root
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._server: MobileApiServer | None = None
        self._thread: threading.Thread | None = None
        self._last_result = MobileBackendStartResult(False, False, False, "")

    @property
    def last_result(self) -> MobileBackendStartResult:
        return self._last_result

    def ensure_running(self) -> MobileBackendStartResult:
        with self._lock:
            if self._owns_running_server():
                self._last_result = MobileBackendStartResult(True, True, False, "")
                return self._last_result

            if self._has_valid_existing_backend():
                self._last_result = MobileBackendStartResult(True, False, True, "")
                return self._last_result

            try:
                server = build_mobile_api_server(self.root, host=self.host, port=self.port)
            except OSError:
                if self._has_valid_existing_backend():
                    self._last_result = MobileBackendStartResult(True, False, True, "")
                    return self._last_result
                self._last_result = MobileBackendStartResult(
                    False,
                    False,
                    False,
                    f"Nao foi possivel iniciar o backend mobile na porta {self.port}.",
                )
                return self._last_result

            thread = threading.Thread(
                target=server.serve_forever,
                name="ConferixMobileBackend",
                daemon=True,
            )
            thread.start()
            self._server = server
            self._thread = thread

        if self._wait_until_healthy():
            self._last_result = MobileBackendStartResult(True, True, False, "")
            return self._last_result

        self.stop()
        self._last_result = MobileBackendStartResult(
            False,
            False,
            False,
            f"Nao foi possivel disponibilizar o backend mobile na porta {self.port}.",
        )
        return self._last_result

    def stop(self) -> None:
        with self._lock:
            if not self._owns_running_server():
                self._server = None
                self._thread = None
                return
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=THREAD_SHUTDOWN_TIMEOUT)
        self._last_result = MobileBackendStartResult(False, False, False, "")

    def _owns_running_server(self) -> bool:
        return self._server is not None and self._thread is not None and self._thread.is_alive()

    def _wait_until_healthy(self) -> bool:
        deadline = time.monotonic() + HEALTH_CHECK_TIMEOUT
        while time.monotonic() < deadline:
            if self._has_valid_existing_backend():
                return True
            time.sleep(HEALTH_CHECK_POLL_INTERVAL)
        return False

    def _has_valid_existing_backend(self) -> bool:
        return is_mobile_backend_reachable("127.0.0.1", self.port, timeout=HEALTH_CHECK_REACHABLE_TIMEOUT)
