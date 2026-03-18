from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from core.page_lock import BlockLockedError, PageLockedError
from services.mobile_service import MobileSessionService, MobileVisibilityError, NoActiveSessionError
from services.mobile_share import DEFAULT_MOBILE_PATH, DEFAULT_MOBILE_PORT

LOGGER = logging.getLogger(__name__)


class MobileApiServer(ThreadingHTTPServer):
    allow_reuse_address = True


def build_mobile_api_server(root: Path, host: str = "127.0.0.1", port: int = DEFAULT_MOBILE_PORT) -> MobileApiServer:
    service = MobileSessionService(root)
    return MobileApiServer((host, port), _build_handler(root, service))


def _build_handler(root: Path, service: MobileSessionService):
    packaged_mobile_root = Path(__file__).resolve().parent.parent / "mobile_web"
    mobile_root = root / "mobile_web"
    if not mobile_root.exists():
        mobile_root = packaged_mobile_root
    assets_root = mobile_root / "assets"
    index_path = mobile_root / "index.html"

    class MobileApiHandler(BaseHTTPRequestHandler):
        server_version = "BancaMobileAPI/2.0"

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch("POST")

        def log_message(self, format, *args) -> None:  # noqa: A003
            del format, args

        def _dispatch(self, method: str) -> None:
            parsed = urlparse(self.path)
            raw_path = parsed.path or "/"
            api_path = raw_path.rstrip("/") or "/"
            try:
                if method == "GET" and self._is_mobile_asset_path(raw_path):
                    self._serve_asset(raw_path)
                    return
                if method == "GET" and self._is_mobile_app_path(raw_path):
                    self._serve_index()
                    return
                if method == "GET" and api_path == "/health":
                    self._send_json(200, {"status": "ok"})
                    return
                if method == "GET" and api_path == "/api/mobile/session":
                    self._send_json(200, service.get_session_overview())
                    return
                if method == "GET":
                    block_id = self._extract_id(api_path, "blocks", "pages")
                    if block_id is not None:
                        self._send_json(200, service.list_pages(block_id))
                        return
                    page_id = self._extract_id(api_path, "pages")
                    if page_id is not None:
                        self._send_json(200, service.get_page_detail(page_id))
                        return
                if method == "POST":
                    line_id = self._extract_id(api_path, "lines", "value")
                    if line_id is not None:
                        payload = self._read_json_body()
                        self._send_json(200, service.set_line_value(line_id, str(payload.get("value", ""))))
                        return
                    page_id = self._extract_id(api_path, "pages", "fill")
                    if page_id is not None:
                        payload = self._read_json_body()
                        self._send_json(200, service.fill_page(page_id, str(payload.get("value", ""))))
                        return
                self._send_json(404, {"error": "Rota nao encontrada."})
            except NoActiveSessionError as exc:
                self._send_json(404, {"error": str(exc), "code": "no_active_session"})
            except MobileVisibilityError as exc:
                self._send_json(409, {"error": str(exc), "code": "not_mobile_visible"})
            except (BlockLockedError, PageLockedError) as exc:
                self._send_json(409, {"error": str(exc), "code": "locked"})
            except ValueError as exc:
                self._send_json(400, {"error": str(exc), "code": "invalid_request"})
            except Exception:
                LOGGER.exception("Erro inesperado no backend mobile")
                self._send_json(500, {"error": "Falha interna no backend mobile.", "code": "internal_error"})

        def _extract_id(self, path: str, resource: str, suffix: str | None = None) -> str | None:
            parts = [part for part in path.split("/") if part]
            if len(parts) < 4 or parts[0:2] != ["api", "mobile"] or parts[2] != resource:
                return None
            if suffix is None:
                return parts[3] if len(parts) == 4 else None
            if len(parts) == 5 and parts[4] == suffix:
                return parts[3]
            return None

        def _is_mobile_asset_path(self, path: str) -> bool:
            return path.startswith("/mobile/assets/")

        def _is_mobile_app_path(self, path: str) -> bool:
            return path == "/mobile" or (path.startswith("/mobile/") and not self._is_mobile_asset_path(path))

        def _serve_index(self) -> None:
            if not index_path.exists():
                self._send_json(500, {"error": "UI mobile nao encontrada.", "code": "mobile_ui_missing"})
                return
            body = index_path.read_bytes()
            self._send_bytes(200, "text/html; charset=utf-8", body)

        def _serve_asset(self, path: str) -> None:
            relative_path = path.removeprefix("/mobile/assets/")
            target = (assets_root / relative_path).resolve()
            try:
                target.relative_to(assets_root.resolve())
            except ValueError:
                self._send_json(404, {"error": "Asset nao encontrado."})
                return
            if not target.is_file():
                self._send_json(404, {"error": "Asset nao encontrado."})
                return
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            body = target.read_bytes()
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                content_type = f"{content_type}; charset=utf-8"
            self._send_bytes(200, content_type, body)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw_payload = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_payload)
            if not isinstance(payload, dict):
                raise ValueError("O corpo da requisicao precisa ser um objeto JSON.")
            return payload

        def _send_json(self, status_code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status_code, "application/json; charset=utf-8", body)

        def _send_bytes(self, status_code: int, content_type: str, body: bytes) -> None:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return MobileApiHandler


def _local_display_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    return host


def _network_display_host(host: str) -> str | None:
    if host not in {"0.0.0.0", "::"}:
        return None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def main(root: Path | None = None) -> int:
    project_root = root or Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Backend HTTP para o cliente mobile de valores.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_MOBILE_PORT)
    args = parser.parse_args()

    server = build_mobile_api_server(project_root, host=args.host, port=args.port)
    _, port = server.server_address[:2]
    local_host = _local_display_host(args.host)
    print(f"API mobile: http://{local_host}:{port}/api/mobile/session")
    print(f"UI mobile:  http://{local_host}:{port}{DEFAULT_MOBILE_PATH}")
    network_host = _network_display_host(args.host)
    if network_host:
        print(f"Rede local: http://{network_host}:{port}{DEFAULT_MOBILE_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
