from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.enums import CommitMode
from services.controller import BancaController
from services.mobile_backend_manager import MobileBackendManager
from services.mobile_api import build_mobile_api_server
from services.mobile_service import MobileSessionService


def _seed_active_session(tmp_path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao mobile")
    _, page_id, first_line_id = controller.create_block("452")
    controller.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)
    controller.set_line_value(first_line_id, "10")
    controller.create_block("453")
    return controller, page_id, first_line_id, second_line_id


def _request_json(url: str, payload: dict | None = None, method: str = "GET") -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def _request_text(url: str) -> tuple[int, str, str]:
    with urlopen(url) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read().decode("utf-8")


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_controller_restores_active_session_on_startup(tmp_path):
    _seed_active_session(tmp_path)

    restored = BancaController(tmp_path)

    assert restored.state.blocks[0].number == "452"
    assert restored.state.session_name == "Operacao mobile"
    assert str(restored.state.blocks[0].pages[0].lines[0].value) == "10.00"


def test_mobile_service_reads_progress_and_updates_values(tmp_path):
    _, page_id, _, second_line_id = _seed_active_session(tmp_path)
    service = MobileSessionService(tmp_path)

    overview = service.get_session_overview()
    detail = service.get_page_detail(page_id)
    updated = service.set_line_value(second_line_id, "5")
    refreshed = BancaController(tmp_path)

    assert overview["session"]["blocks_count"] == 1
    assert overview["session"]["name"] == "Operacao mobile"
    assert overview["session"]["status"] == "pending"
    assert overview["session"]["draft_block_hidden"] is True
    assert overview["session"]["session_revision"]
    assert overview["blocks"][0]["block_revision"]
    assert overview["blocks"][0]["filled_values"] == 1
    assert detail["page"]["filled_values"] == 1
    assert detail["page"]["locked"] is False
    assert detail["page"]["page_revision"]
    assert detail["lines"][0]["placeholder"] == "555"
    assert updated["page"]["filled_values"] == 2
    assert str(refreshed.state.blocks[0].pages[0].lines[1].value) == "5.00"


def test_mobile_api_serves_page_detail_and_updates_value(tmp_path):
    _, page_id, _, second_line_id = _seed_active_session(tmp_path)
    server = build_mobile_api_server(tmp_path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]

    try:
        health_status, health_payload = _request_json(f"http://{host}:{port}/health")
        session_status, session_payload = _request_json(f"http://{host}:{port}/api/mobile/session")
        detail_status, detail_payload = _request_json(f"http://{host}:{port}/api/mobile/pages/{page_id}")
        update_status, update_payload = _request_json(
            f"http://{host}:{port}/api/mobile/lines/{second_line_id}/value",
            payload={"value": "7"},
            method="POST",
        )
        html_status, html_content_type, html_payload = _request_text(f"http://{host}:{port}/mobile")
        blocks_html_status, _, blocks_html_payload = _request_text(f"http://{host}:{port}/mobile/blocks")
        asset_status, asset_content_type, asset_payload = _request_text(f"http://{host}:{port}/mobile/assets/app.js")

        assert health_status == 200
        assert health_payload["status"] == "ok"
        assert session_status == 200
        assert session_payload["session"]["name"] == "Operacao mobile"
        assert session_payload["session"]["session_revision"]
        assert detail_status == 200
        assert detail_payload["page"]["filled_values"] == 1
        assert update_status == 200
        assert update_payload["page"]["filled_values"] == 2
        assert html_status == 200
        assert "text/html" in html_content_type
        assert "Conferix Mobile" in html_payload
        assert blocks_html_status == 200
        assert "Conferix Mobile" in blocks_html_payload
        assert asset_status == 200
        assert "javascript" in asset_content_type
        assert "renderRoute" in asset_payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fill_page_endpoint_only_updates_pending_lines(tmp_path):
    _, page_id, _, _ = _seed_active_session(tmp_path)
    server = build_mobile_api_server(tmp_path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]

    try:
        fill_status, fill_payload = _request_json(
            f"http://{host}:{port}/api/mobile/pages/{page_id}/fill",
            payload={"value": "3"},
            method="POST",
        )

        assert fill_status == 200
        assert fill_payload["page"]["status"] == "complete"
        assert fill_payload["lines"][0]["value_display"] == "10,00"
        assert fill_payload["lines"][1]["value_display"] == "3,00"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mobile_session_waits_for_publish_when_only_draft_block_exists(tmp_path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao mobile")
    controller.create_block("452")
    service = MobileSessionService(tmp_path)

    overview = service.get_session_overview()

    assert overview["session"]["status"] == "waiting_publish"
    assert overview["session"]["blocks_count"] == 0
    assert overview["session"]["draft_block_hidden"] is True
    assert overview["session"]["hidden_blocks_count"] == 1
    assert overview["blocks"] == []


def test_last_locked_block_remains_visible_on_mobile(tmp_path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao mobile")
    first_block_id, _, first_line_id = controller.create_block("452")
    controller.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_line_value(first_line_id, "10")
    second_block_id, _, second_line_id = controller.create_block("453")
    controller.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)
    controller.set_block_money(second_block_id, "50")
    service = MobileSessionService(tmp_path)

    overview = service.get_session_overview()

    assert overview["session"]["blocks_count"] == 2
    assert overview["session"]["draft_block_hidden"] is False
    assert {block["block_id"] for block in overview["blocks"]} == {first_block_id, second_block_id}


def test_hidden_page_returns_not_mobile_visible(tmp_path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao mobile")
    _, visible_page_id, visible_line_id = controller.create_block("452")
    controller.upsert_bet_text(visible_line_id, "555", commit_mode=CommitMode.ENTER)
    _, hidden_page_id, hidden_line_id = controller.create_block("453")
    controller.upsert_bet_text(hidden_line_id, "666", commit_mode=CommitMode.ENTER)
    server = build_mobile_api_server(tmp_path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]

    try:
        visible_status, _ = _request_json(f"http://{host}:{port}/api/mobile/pages/{visible_page_id}")
        hidden_status, hidden_payload = _request_json(f"http://{host}:{port}/api/mobile/pages/{hidden_page_id}")

        assert visible_status == 200
        assert hidden_status == 409
        assert hidden_payload["code"] == "not_mobile_visible"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mobile_backend_manager_starts_and_stops_owned_server(tmp_path):
    _seed_active_session(tmp_path)
    port = _reserve_port()
    manager = MobileBackendManager(tmp_path, host="0.0.0.0", port=port)

    started = manager.ensure_running()
    status, payload = _request_json(f"http://127.0.0.1:{port}/health")

    assert started.running is True
    assert started.owned is True
    assert started.reused_existing is False
    assert status == 200
    assert payload["status"] == "ok"

    manager.stop()

    assert manager.last_result.running is False


def test_mobile_backend_manager_reuses_existing_backend_when_port_is_busy(tmp_path):
    _seed_active_session(tmp_path)
    port = _reserve_port()
    server = build_mobile_api_server(tmp_path, host="127.0.0.1", port=port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        manager = MobileBackendManager(tmp_path, host="0.0.0.0", port=port)
        started = manager.ensure_running()

        assert started.running is True
        assert started.owned is False
        assert started.reused_existing is True
    finally:
        manager.stop()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mobile_backend_manager_reports_invalid_port_conflict(tmp_path):
    port = _reserve_port()
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", port))
    blocker.listen(1)

    try:
        manager = MobileBackendManager(tmp_path, host="0.0.0.0", port=port)
        started = manager.ensure_running()

        assert started.running is False
        assert "porta" in started.message
    finally:
        blocker.close()


def test_mobile_web_ok_flow_preserves_focus_handoff_hooks():
    app_js = (Path(__file__).resolve().parents[1] / "mobile_web" / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'enterkeyhint="next"' in app_js
    assert 'appRoot.addEventListener("pointerdown"' in app_js
    assert "event.preventDefault();" in app_js
    assert 'patchPageScreen(payload, { focusLineId: nextLineId, smoothFocus: false });' in app_js
    assert "function syncActiveLineState" in app_js
    assert 'element.dataset.active = isLineActive(line) && line.editable ? "true" : "false";' in app_js


def test_mobile_web_assets_keep_visual_hierarchy_hooks():
    assets_root = Path(__file__).resolve().parents[1] / "mobile_web" / "assets"
    app_js = (assets_root / "app.js").read_text(encoding="utf-8")
    mobile_css = (assets_root / "mobile.css").read_text(encoding="utf-8")

    assert "renderContextHeadline" in app_js
    assert "progress-caption" in app_js
    assert ".context-headline" in mobile_css
    assert ".progress-caption" in mobile_css
    assert '.line-card[data-active="true"]' in mobile_css
