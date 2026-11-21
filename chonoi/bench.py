"""Benchmark hiệu năng đồ họa trình duyệt qua Chrome/Chromium/Edge headless.

Lệnh:
    python -m chonoi.bench --seed 42 --duration 30 --out bench.json [--warmup 3] [--browser PATH] [--timeout 120]
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

from .contract import load_contract
from .live import LiveGame, LiveServer


class BadBenchArgs(Exception):
    """Lỗi đối số dòng lệnh benchmark."""


class _BenchArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"đối số sai: {message}\n")
        raise BadBenchArgs(message)


def bench_stats(frame_ms: list[float]) -> dict:
    """Tính các số liệu hiệu năng khung hình từ danh sách frame_ms (miligiây).

    Trả về số thô chưa làm tròn: avg_fps, p1_low_fps, frames, measured_s.
    Nếu danh sách rỗng, ném ValueError.
    """
    if not frame_ms or any(not math.isfinite(dt) or dt <= 0 for dt in frame_ms):
        raise ValueError("danh sách frame_ms không được rỗng")
    frames = len(frame_ms)
    measured_s = sum(frame_ms) / 1000.0
    if measured_s <= 0:
        raise ValueError("measured_s phải > 0")
    avg_fps = frames / measured_s
    k = max(1, math.ceil(0.01 * frames))
    slowest_k = sorted(frame_ms, reverse=True)[:k]
    mean_slowest = sum(slowest_k) / k
    p1_low_fps = 1000.0 / mean_slowest
    return {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": measured_s,
    }


def find_browser(explicit: str | None = None) -> str | None:
    """Tìm đường dẫn thực thi của trình duyệt phù hợp.

    Thứ tự ưu tiên:
    1. explicit nếu tồn tại file hoặc có trong PATH.
    2. Biến môi trường CHONOI_BROWSER.
    3. Tìm trong PATH: google-chrome, google-chrome-stable, chromium, chromium-browser, microsoft-edge.
    4. Đường dẫn chuẩn macOS và Windows.
    Không thấy => None.
    """
    if explicit is not None:
        if os.path.isfile(explicit):
            return explicit
        w = shutil.which(explicit)
        if w:
            return w
        return None

    env = os.environ.get("CHONOI_BROWSER")
    if env:
        if os.path.isfile(env):
            return env
        w = shutil.which(env)
        if w:
            return w

    path_names = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
    ]
    for name in path_names:
        w = shutil.which(name)
        if w:
            return w

    mac_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for p in mac_paths:
        if os.path.isfile(p):
            return os.path.abspath(p)

    win_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for env_var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env_var)
        if base:
            win_paths.extend([
                os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
            ])

    for p in win_paths:
        if os.path.isfile(p):
            return os.path.abspath(p)

    return None


def main(argv=None) -> int:
    t0 = time.perf_counter()
    if argv is None:
        argv = sys.argv[1:]

    p = _BenchArgumentParser(prog="chonoi.bench", description="Benchmark đồ họa qua trình duyệt headless.")
    p.add_argument("--seed", type=int, required=True, help="Hạt ngẫu nhiên")
    p.add_argument("--duration", type=float, required=True, help="Thời gian đo (giây, > 0)")
    p.add_argument("--out", required=True, help="Đường dẫn file kết quả")
    p.add_argument("--warmup", type=float, default=3.0, help="Thời gian làm nóng (giây, mặc định 3)")
    p.add_argument("--browser", help="Đường dẫn trình duyệt")
    p.add_argument("--timeout", type=float, default=120.0, help="Thời gian chờ tối đa (giây, mặc định 120)")

    try:
        args = p.parse_args(argv)
        if not math.isfinite(args.duration) or args.duration <= 0:
            sys.stderr.write("đối số sai: --duration phải > 0\n")
            return 2
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            sys.stderr.write("đối số sai: --timeout phải > 0\n")
            return 2
        if not math.isfinite(args.warmup) or args.warmup < 0:
            sys.stderr.write("đối số sai: --warmup phải >= 0\n")
            return 2
    except BadBenchArgs:
        return 2
    except SystemExit as e:
        return 0 if e.code == 0 else 2

    browser = find_browser(args.browser)
    if not browser:
        sys.stderr.write(
            "Không tìm thấy trình duyệt. Vui lòng cài Chrome/Chromium/Edge hoặc đặt biến môi trường CHONOI_BROWSER.\n"
        )
        return 3

    contract = load_contract()
    tuning = contract["tuning"]
    game = LiveGame(mode="gather", tuning=tuning, scenario={}, seed=args.seed, contract_version=contract["contract_version"], bench=True)
    game.t0 = t0
    server = LiveServer(game, host="127.0.0.1", port=0)
    server.start()

    tmpdir = tempfile.mkdtemp(prefix="chonoi-bench-")
    url = f"{server.url}?bench=1&warmup={args.warmup}&duration={args.duration}"

    cmd = [
        browser,
        "--headless=new",
        "--window-size=1280,720",
        f"--user-data-dir={tmpdir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        url,
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        sys.stderr.write(f"không khởi động được trình duyệt: {e}\n")
        server.stop()
        shutil.rmtree(tmpdir, ignore_errors=True)
        return 3

    try:
        elapsed = time.perf_counter() - t0
        remain = max(0.0, args.timeout - elapsed)
        finished = game.bench_done.wait(timeout=remain)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        server.stop()
        for _ in range(5):
            try:
                shutil.rmtree(tmpdir)
                break
            except Exception:
                time.sleep(0.1)
        shutil.rmtree(tmpdir, ignore_errors=True)

    if not finished:
        sys.stderr.write(f"quá thời gian chờ ({args.timeout}s)\n")
        return 4

    frame_ms = getattr(game, "frame_ms", None)
    if not frame_ms:
        sys.stderr.write("không nhận được dữ liệu khung hình từ trình duyệt\n")
        return 4

    try:
        stats = bench_stats(frame_ms)
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"lỗi tính chỉ số: {e}\n")
        return 4

    load_ms = getattr(game, "load_ms", 0.0)
    if load_ms is None:
        load_ms = 0.0

    output_data = {
        "avg_fps": round(stats["avg_fps"], 2),
        "p1_low_fps": round(stats["p1_low_fps"], 2),
        "frames": int(stats["frames"]),
        "measured_s": round(stats["measured_s"], 2),
        "load_ms": int(round(load_ms)),
    }

    out_path = os.path.abspath(args.out)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tmp_file = f"{out_path}.tmp.{os.getpid()}"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    os.replace(tmp_file, out_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
