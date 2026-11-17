"""Browser QA of the running simulator dashboard, never original-game actions."""

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".tools/browsers"))

import httpx
from playwright.sync_api import sync_playwright
from sts2lab.learned_replay import audit_learned_trace
from sts2lab.rl_io import write_json, file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = "http://127.0.0.1:8766"
    with httpx.Client(base_url=base, trust_env=False, timeout=20) as client:
        state = client.get("/api/state").raise_for_status().json()
        act = client.get("/api/act/state").raise_for_status().json()
        if (
            state["metadata"]["backend"] != "native_simulator"
            or state["status"] not in ("paused", "finished", "closed")
            or act["status"] not in ("idle", "closed")
        ):
            raise ValueError(
                "Browser QA requires idle original controllers and a paused/finished simulator"
            )
        errors, replay_mutations = [], []
        replay_mode = False
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1480, "height": 1050})
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on(
                    "request",
                    lambda r: (
                        replay_mutations.append({"method": r.method, "url": r.url})
                        if replay_mode and r.method not in ("GET", "HEAD")
                        else None
                    ),
                )
                page.goto(base)
                page.wait_for_function(
                    "document.querySelector('#connection').textContent.includes('已连接')"
                )
                page.select_option("#policy", "ppo")
                page.fill("#seed", "3")
                with page.expect_response(
                    lambda r: r.url.endswith("/api/session")
                    and r.request.method == "POST"
                ) as event:
                    page.click("#new-session")
                state = event.value.json()
                assert (
                    event.value.status == 200 and state["metadata"]["policy"] == "ppo"
                )
                page.wait_for_function(
                    "document.querySelector('#decision-meta').textContent.includes('687a17eeac06')"
                )
                page.screenshot(path=str(args.output / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
                page.set_viewport_size({"width": 1480, "height": 1050})
                page.select_option("#speed", "0.25")
                with page.expect_response(
                    lambda r: r.url.endswith("/api/control")
                    and r.request.method == "POST"
                ) as control:
                    page.click("#run")
                assert control.value.status == 200, control.value.text()
                page.wait_for_function(
                    "!document.querySelector('#outcome').hidden", timeout=30000
                )
                state = client.get("/api/state").raise_for_status().json()
                assert state["status"] == "finished"
                path = ROOT / "artifacts/runs" / f"{state['metadata']['run_id']}.jsonl"
                proof = audit_learned_trace(path)
                assert proof["passed"]
                before = file_hash(path)
                page.select_option("#run-list", path.stem)
                replay_mode = True
                page.click("#load-replay")
                page.wait_for_function(
                    "!document.querySelector('#replay-controls').hidden"
                )
                maximum = int(page.get_attribute("#replay-position", "max"))
                for frame in range(maximum + 1):
                    page.eval_on_selector(
                        "#replay-position",
                        "(e,n) => {e.value=n;e.dispatchEvent(new Event('input'));}",
                        frame,
                    )
                    if frame < maximum:
                        assert (
                            "687a17eeac06"
                            in page.locator("#decision-meta").inner_text()
                        )
                page.screenshot(path=str(args.output / "replay.png"), full_page=True)
                assert not replay_mutations and not errors and file_hash(path) == before
                result = {
                    "passed": True,
                    "scope": "simulator_browser_ui_not_original_game",
                    "run_id": path.stem,
                    "replay_frames": maximum + 1,
                    "replay_mutations": replay_mutations,
                    "javascript_errors": errors,
                    "mobile_no_horizontal_overflow": True,
                    "model_audit": proof,
                    "original_game_actions": 0,
                }
                write_json(args.output / "result.json", result)
                print(json.dumps(result))
                browser.close()
        except BaseException as exc:
            write_json(
                args.output / "failure.json",
                {
                    "error": f"{type(exc).__name__}: {exc}",
                    "javascript_errors": errors,
                    "replay_mutations": replay_mutations,
                },
            )
            raise


if __name__ == "__main__":
    main()
