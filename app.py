# -*- coding: utf-8 -*-
"""AfterFlow 本地演示服务，仅使用 Python 标准库。"""

from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from data import DEMO_TICKETS, POLICIES
from engine import dashboard_payload, evaluate, process_ticket


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
TICKETS: Dict[str, Dict[str, Any]] = {
    item["id"]: copy.deepcopy(item) for item in DEMO_TICKETS
}
RESULTS: Dict[str, Dict[str, Any]] = {}
LOCK = threading.Lock()


def _engine_status() -> Dict[str, str]:
    configured = bool(
        os.environ.get("LLM_BASE_URL")
        and os.environ.get("LLM_API_KEY")
        and os.environ.get("LLM_MODEL")
    )
    return {
        "mode": "LLM 辅助" if configured else "离线评测引擎",
        "detail": (
            "分类、检索和风险门禁保持确定性，LLM 仅改写草稿"
            if configured
            else "规则分类 + BM25 RAG + 风险门禁，无需联网或密钥"
        ),
    }


def _ticket_stats() -> Dict[str, int]:
    pending = sum(1 for ticket in TICKETS.values() if ticket["status"] == "待处理")
    completed = sum(
        1
        for ticket in TICKETS.values()
        if ticket["status"] in {"已完成", "已采纳草稿"}
    )
    handoff = sum(1 for ticket in TICKETS.values() if ticket["status"] == "已转人工")
    high_risk = sum(
        1
        for ticket in TICKETS.values()
        if ticket["priority"] in {"较高", "紧急"} and ticket["status"] in {"待处理", "待确认"}
    )
    return {
        "pending": pending,
        "completed": completed,
        "handoff": handoff,
        "high_risk": high_risk,
    }


def bootstrap_payload() -> Dict[str, Any]:
    evaluation = evaluate()
    workflow = next(item for item in evaluation["methods"] if item["id"] == "workflow")
    return {
        "tickets": [
            {**copy.deepcopy(ticket), "result": RESULTS.get(ticket["id"])}
            for ticket in TICKETS.values()
        ],
        "policies": copy.deepcopy(POLICIES),
        "dashboard": {
            **_ticket_stats(),
            "workflow_success": workflow["task_success_rate"],
            "critical_error_rate": workflow["critical_error_rate"],
            "evaluation_total": evaluation["dataset"]["total"],
            "policy_count": len(POLICIES),
        },
        "engine": _engine_status(),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AfterFlow/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int) -> None:
        self._send_json({"error": message}, status)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("请求 JSON 格式无效") from exc

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/bootstrap":
            self._send_json(bootstrap_payload())
            return
        if parsed.path == "/api/evaluation":
            self._send_json(evaluate())
            return
        if parsed.path == "/api/health":
            self._send_json({"ok": True, "engine": _engine_status()})
            return
        if parsed.path.startswith("/api/"):
            self._send_error_json("接口不存在", HTTPStatus.NOT_FOUND)
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_error_json(str(exc), HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/process":
            ticket_id = str(payload.get("ticket_id", ""))
            with LOCK:
                ticket = TICKETS.get(ticket_id)
                if not ticket:
                    self._send_error_json("工单不存在", HTTPStatus.NOT_FOUND)
                    return
                result = process_ticket(ticket, use_llm=bool(payload.get("use_llm", False)))
                RESULTS[ticket_id] = result
                ticket["status"] = "已转人工" if result["risk"]["requires_review"] else "待确认"
            self._send_json(
                {"result": result, "ticket": ticket, "dashboard": _ticket_stats()}
            )
            return

        if parsed.path == "/api/action":
            ticket_id = str(payload.get("ticket_id", ""))
            action = str(payload.get("action", ""))
            with LOCK:
                ticket = TICKETS.get(ticket_id)
                if not ticket:
                    self._send_error_json("工单不存在", HTTPStatus.NOT_FOUND)
                    return
                if action == "adopt":
                    ticket["status"] = "已采纳草稿"
                elif action == "handoff":
                    ticket["status"] = "已转人工"
                else:
                    self._send_error_json("未知操作", HTTPStatus.BAD_REQUEST)
                    return
            self._send_json({"ok": True, "ticket": ticket, "dashboard": _ticket_stats()})
            return

        if parsed.path == "/api/reset":
            with LOCK:
                TICKETS.clear()
                TICKETS.update(
                    {item["id"]: copy.deepcopy(item) for item in DEMO_TICKETS}
                )
                RESULTS.clear()
            self._send_json({"ok": True, "dashboard": _ticket_stats()})
            return

        self._send_error_json("接口不存在", HTTPStatus.NOT_FOUND)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            candidate = STATIC_DIR / "index.html"
        body = candidate.read_bytes()
        mime, _ = mimetypes.guess_type(str(candidate))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="AfterFlow 售后工单 AI 助手")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print("AfterFlow 已启动")
    print(f"访问地址：{url}")
    print("按 Ctrl+C 停止服务")
    if args.open:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
