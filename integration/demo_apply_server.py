"""
Demo 本地 Apply 服务（不依赖队友前后端）
启动: python integration/demo_apply_server.py
接口: POST http://127.0.0.1:8765/apply-and-rerun
"""
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8765
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_apply_and_rerun() -> dict:
    script = PROJECT_ROOT / "integration" / "apply_and_rerun.py"
    if not script.exists():
        return {"success": False, "message": f"缺少脚本: {script}"}
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({"overwrite_rules": True}, ensure_ascii=False),
        text=True,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = (proc.stdout or "").strip()
    if not raw:
        return {"success": False, "message": proc.stderr.strip() or "脚本无输出"}
    try:
        data = json.loads(raw)
    except Exception:
        return {"success": False, "message": raw}
    return data


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._write_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/health":
            self._write_json(200, {"ok": True, "service": "demo-apply-server"})
            return
        self._write_json(404, {"ok": False, "message": "Not Found"})

    def do_POST(self):
        if self.path != "/apply-and-rerun":
            self._write_json(404, {"success": False, "message": "Not Found"})
            return
        result = _run_apply_and_rerun()
        self._write_json(200 if result.get("success") else 500, result)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Demo apply server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
