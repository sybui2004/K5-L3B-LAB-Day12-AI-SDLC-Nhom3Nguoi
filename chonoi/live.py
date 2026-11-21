"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python -m chonoi.live --mode gather|quan|day [--days N] [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/` và các API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool, "pause": bool, "shop_done": bool, "buy": str}
    POST /advance -> {"gate": tên màn} rời màn chờ của mode day (menu, intro, kết quả)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mode day: màn chờ (`gate`) chỉ có ở client, sim KHÔNG chạy trong lúc màn hiện (TICKET-02, spec day-ui mục D1).

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario
from .sim.day import validate_days

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
MAX_BENCH_BODY = 1024 * 1024
RECENT_EVENTS = 40
MAX_BUY = 32
DEFAULT_DAYS = 5
GATES = ("menu", "day_intro", "evening_intro", "day_result", "summary")
NEXT_GATE = {"menu": "day_intro"}  # các màn khác rời thẳng vào gameplay; Summary chỉ rời bằng /restart
GATE_ON_PHASE = {"gather": "day_intro", "quan": "evening_intro", "shop": "day_result"}
STATIC_JS = {"/creative.js": "creative.js", "/screens.js": "screens.js"}


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=DEFAULT_DAYS,
                 contract_version="1.2", bench=False):
        self._args = (mode, tuning, scenario, seed, inventory, days, contract_version)
        self.mode = mode
        self.days = days
        self.tuning = tuning
        self.inventory_out = inventory_out
        self.bench = bench
        self.t0 = None
        self.load_ms = None
        self.frame_ms = None
        self.bench_done = threading.Event()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        self.session = Session(*self._args)
        self.inputs = LiveInputs()
        self.events = self.session.initial_events()
        self.gate = "menu" if self.mode == "day" else None
        self.tally = {"served": 0, "left": 0, "tips": 0, "dishes": {}}
        self._saved = False
        self.error = None

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if self.gate or s.done:
            return
        rows = s.step(self.inputs.advance())
        self.events.extend(rows)
        del self.events[:-RECENT_EVENTS]
        self._count(rows)
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")
        if self.mode == "day":
            gate = "summary" if s.done else (GATE_ON_PHASE.get(s.sim.phase) if s.phase_changed else None)
            if gate:
                self.gate = gate
                self.inputs = LiveInputs()  # phím đang giữ không lọt qua màn chờ

    def _count(self, rows):
        """Số liệu cả lượt cho màn Summary; chỉ đọc event, không đụng sim."""
        t = self.tally
        for row in rows:
            name, data = row["name"], row["data"]
            if name == "served":
                dish = data.get("dish_id", data.get("dish"))
                t["served"] += 1
                t["dishes"][dish] = t["dishes"].get(dish, 0) + 1
            elif name == "paid":
                t["tips"] += data.get("tip", 0)
            elif name == "customer_left" and data.get("reason") == "patience":
                t["left"] += 1

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            snap["meta"] = self.tuning[snap["phase"]]
            snap["menu"] = self.tuning["menu"]
            snap["gate"] = self.gate
            snap["freshness"] = self.tuning.get("freshness")
            if self.mode == "day":
                snap["days"] = self.days
                snap["tally"] = self.tally
                if snap["phase"] == "shop":
                    snap["shop_table"] = self.tuning["shop"]["upgrades"]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "pause", "shop_done"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if "buy" in body and not (isinstance(buy, str) and 1 <= len(buy) <= MAX_BUY):
            raise ValueError("buy phải là chuỗi khác rỗng")
        with self._lock:
            self.inputs.set(move, buy=buy, **buttons)

    def advance_gate(self, gate):
        """Rời màn chờ. Bấm trùng hoặc màn đã qua thì bỏ qua; Summary chỉ rời bằng restart."""
        if gate not in GATES:
            raise ValueError("gate không hợp lệ")
        with self._lock:
            if self.gate != gate or gate == "summary":
                return
            self.gate = NEXT_GATE.get(gate)
            self.inputs = LiveInputs()

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    content = f.read()
                    if self.game.bench and parse_qs(urlsplit(self.path).query).get("bench") == ["1"]:
                        content = content.replace(b"</body>", b'<script src="/bench.js"></script>\n</body>')
                    self._send(200, content, "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        elif path == "/bench.js" and getattr(self.game, "bench", False):
            try:
                with open(os.path.join(WEB_DIR, "bench.js"), "rb") as f:
                    self._send(200, f.read(), "text/javascript; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu file"}')
        elif path in STATIC_JS:  # creative.js chỉ được trình duyệt nạp khi ?creative=1
            try:
                with open(os.path.join(WEB_DIR, STATIC_JS[path]), "rb") as f:
                    self._send(200, f.read(), "text/javascript; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu file"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/bench/") and not self.game.bench:
            self._send(404, b'{"error":"khong co"}')
            return
        max_body = MAX_BENCH_BODY if path == "/bench/result" else MAX_BODY
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > max_body:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/advance":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.advance_gate(body.get("gate"))
            elif path == "/restart":
                self.game.restart()
            elif path == "/bench/first-frame":
                if not getattr(self.game, "bench", False):
                    self._send(404, b'{"error":"khong co"}')
                    return
                if getattr(self.game, "load_ms", None) is None:
                    t0 = getattr(self.game, "t0", None)
                    self.game.load_ms = (time.perf_counter() - t0) * 1000.0 if t0 is not None else 0.0
            elif path == "/bench/result":
                if not getattr(self.game, "bench", False):
                    self._send(404, b'{"error":"khong co"}')
                    return
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict) or "frame_ms" not in body or not isinstance(body["frame_ms"], list):
                    raise ValueError("body phải có frame_ms là list")
                if self.game.load_ms is None:
                    raise ValueError("chưa nhận khung hình đầu")
                self.game.frame_ms = body["frame_ms"]
                if hasattr(self.game, "bench_done"):
                    self.game.bench_done.set()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--days", type=int, help=f"chỉ với day: số Ngày 1..5, mặc định {DEFAULT_DAYS}")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với day")
        days = DEFAULT_DAYS if a.days is None else a.days
        if a.mode == "day":
            validate_days(days)
        contract = load_contract()
        tuning, version = contract["tuning"], contract["contract_version"]
        scenario = load_scenario(a.scenario, a.mode, tuning, version)
        inventory = read_inventory(a.inventory, version) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, days, version)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
