"""Real-browser QA with synthetic HTTP transport. NOT original-game parity evidence."""

import copy
import json
from pathlib import Path
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import httpx
from playwright.sync_api import sync_playwright
import uvicorn
from test_original import SyntheticGame, raw_state
from sts2lab.server import create_app

qa = ROOT / "artifacts/original-dashboard-synthetic"
qa.mkdir(parents=True, exist_ok=True)
game = SyntheticGame(lose_response=True)
base_handle = game.handle


async def handle(request):
    if request.method == "POST" and game.posts:
        command = json.loads(request.content)
        assert command["action"] == "end_turn"
        game.posts.append(command)
        game.raw.update(
            state_type="rewards",
            lab_last_request_id=command["lab_request_id"],
            lab_state_token="terminal",
            lab_action_ready=False,
        )
        for key in (
            "energy",
            "max_energy",
            "hand",
            "draw_pile",
            "discard_pile",
            "exhaust_pile",
        ):
            game.raw["player"].pop(key, None)
        return httpx.Response(200, json={"status": "ok"})
    return await base_handle(request)


game.handle = handle
app = create_app(qa / "runs", original_factory=game.factory(qa))
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
port = sock.getsockname()[1]
server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
thread.start()
checks, errors = [], []
try:
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        if not thread.is_alive():
            raise RuntimeError("Synthetic QA server stopped before startup")
        time.sleep(0.05)
    assert server.started
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1480, "height": 1050})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{port}")
        page.get_by_text("已连接 · 实时状态").wait_for()
        page.locator("#backend").select_option("original_game")
        assert page.locator("#seed").is_disabled()
        page.locator("#new-session").click()
        page.wait_for_function(
            "document.querySelector('#backend-label').textContent==='Windows 原版游戏'"
        )
        checks.append("original_backend_selection_and_unknown_seed")
        page.locator('.candidate[data-action="play:0:0"]').click()
        page.wait_for_function(
            "document.querySelector('#status').textContent==='结果待确认'"
        )
        assert page.locator("#step").is_disabled()
        assert page.locator("#new-session").is_disabled()
        assert page.locator("#reconcile").is_visible()
        page.locator("#reconcile").click()
        page.wait_for_function(
            "document.querySelector('#status').textContent==='已暂停'"
        )
        assert len(game.posts) == 1
        assert page.locator(".history-row").count() == 1
        assert not page.locator("#error").is_visible()
        checks.append("lost_response_reconciled_without_repost")
        page.locator('.candidate[data-action="end_turn"]').click()
        page.wait_for_function(
            "document.querySelector('#status').textContent==='已结束'"
        )
        assert "不可读取" in page.locator("#hand-count").inner_text()
        assert "—" in page.locator("#player").inner_text()
        assert "不再提供敌人状态" in page.locator("#enemies").inner_text()
        assert "null" not in page.locator("#player").inner_text()
        checks.append("terminal_unavailable_fields_are_not_zero_values")
        page.screenshot(path=str(qa / "desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        page.screenshot(path=str(qa / "mobile.png"), full_page=True)
        checks.append("mobile_layout")
        # A second synthetic episode tests explicitly detaching an unknown command.
        game.raw = raw_state()
        game.posts.clear()
        page.locator("#new-session").click()
        page.wait_for_function(
            "document.querySelector('#status').textContent==='已暂停'"
        )
        page.locator('.candidate[data-action="play:0:0"]').click()
        page.wait_for_function(
            "document.querySelector('#status').textContent==='结果待确认'"
        )
        page.locator("#archive").click()
        page.wait_for_function(
            "document.querySelector('#status').textContent.startsWith('已归档')"
        )
        assert len(game.posts) == 1
        assert page.locator("#step").is_disabled()
        assert "最后确认" in page.locator("#source-note").inner_text()
        page.locator("#backend").select_option("native_simulator")
        page.locator("#new-session").click()
        page.wait_for_function(
            "document.querySelector('#backend-label').textContent==='C# 原生模拟器' && document.querySelector('#status').textContent==='已暂停'"
        )
        assert len(game.posts) == 1
        checks.append("archive_unknown_then_restart_without_game_actions")
        browser.close()
    assert not errors, errors
    report = {
        "passed": True,
        "scope": "synthetic_original_transport_browser_qa",
        "original_game_verified": False,
        "checks": checks,
        "javascript_errors": errors,
    }
    (qa / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
finally:
    server.should_exit = True
    thread.join(timeout=10)
    sock.close()
    if thread.is_alive():
        raise RuntimeError("Synthetic QA server failed to stop")
