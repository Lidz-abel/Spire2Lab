"""Browser integration test against a running loopback lab server."""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1480, "height": 1050})
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8765")
    page.get_by_text("已连接 · 实时状态").wait_for()
    page.locator("#encounter").select_option("slimes-weak")
    page.locator("#seed").fill("3")
    page.get_by_role("button", name="新建实验").click()
    page.wait_for_function(
        "document.querySelector('#encounter-title').textContent==='slimes-weak'"
    )
    page.locator("#step").click()
    page.wait_for_function("document.querySelectorAll('.history-row').length===1")
    checks.append("manual_step")
    # A non-proposed action is explicitly marked as manual intervention.
    candidates = page.locator(".candidate:not(.chosen)")
    if candidates.count():
        candidates.first.click()
        page.wait_for_function("document.querySelectorAll('.history-row').length===2")
        assert "人工干预" in page.locator("#history").inner_text()
        checks.append("manual_override_marked")
    page.locator("#speed").select_option("0.25")
    page.locator("#run").click()
    page.wait_for_function("document.querySelector('#status').textContent==='运行中'")
    page.locator("#run").click()
    page.wait_for_function("document.querySelector('#status').textContent==='已暂停'")
    checks.append("run_pause")
    page.screenshot(path=str(ROOT / "artifacts/dashboard-desktop.png"), full_page=True)
    page.locator("#run").click()
    page.wait_for_function(
        "document.querySelector('#status').textContent==='已结束'", timeout=60000
    )
    assert page.locator("#step").is_disabled()
    checks.append("automatic_full_battle")
    live_count = page.locator(".history-row").count()
    page.locator("#load-replay").click()
    page.wait_for_function("document.querySelector('#mode').textContent==='轨迹回放'")
    assert page.locator("#step").is_disabled()
    assert page.locator(".history-row").count() == 0
    page.locator("#replay-position").evaluate(
        "el => {el.value=el.max; el.dispatchEvent(new Event('input'));}"
    )
    assert page.locator(".history-row").count() == live_count
    checks.append("recorded_replay_first_and_last")
    page.locator("#back-live").click()
    page.wait_for_function("document.querySelector('#mode').textContent==='实时实验'")
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(ROOT / "artifacts/dashboard-mobile.png"), full_page=True)
    checks.append("mobile_no_horizontal_overflow")
    browser.close()
assert not errors, errors
report = {
    "passed": True,
    "checks": checks,
    "javascript_errors": errors,
    "scope": "native_simulator_dashboard",
}
(ROOT / "artifacts/browser-checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
