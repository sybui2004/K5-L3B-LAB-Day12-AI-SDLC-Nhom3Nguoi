"""Cổng kiểm trước khi đẩy / gắn tag. Chỉ dùng thư viện chuẩn.

    python .agents/skills/phase-check/phase_check.py [--proof docs/proof/phase-1]

In bảng đạt/không đạt; mã thoát 0 khi đạt hết, 1 khi có mục không đạt.
--proof: ghi log unittest, JSONL mẫu seed 1 (đuôi .jsonl.txt), kết quả so byte và bảng kết quả.
"""

import argparse
import filecmp
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TICKS = "600"


def run(cmd):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(["tests", "."]), PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           encoding="utf-8", errors="replace")
    except OSError as e:
        return 127, f"không chạy được {cmd[0]}: {e}"
    return p.returncode, p.stdout.replace(ROOT, ".")


def last_line(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return lines[-1] if lines else ""


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Kiểm phase trước khi đẩy / gắn tag")
    ap.add_argument("--proof", help="thư mục ghi bằng chứng, ví dụ docs/proof/phase-1")
    a = ap.parse_args(argv)

    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        headless = shlex.split(json.load(f)["headless_cmd"])
    if shutil.which(headless[0]) is None:
        print(f"KHÔNG ĐẠT: không tìm thấy lệnh `{headless[0]}` trong headless_cmd.")
        return 1

    rows = []

    def check(name, ok, note=""):
        rows.append((name, bool(ok), note))

    code, unit_log = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    check("unittest", code == 0, last_line(unit_log))
    code, out = run([sys.executable, "tools/check_team.py"])
    check("check_team", code == 0, last_line(out))

    with tempfile.TemporaryDirectory() as tmp:
        p = lambda name: os.path.join(tmp, name)
        same = {}
        for mode in ("gather", "quan"):
            results = [run([*headless, "--mode", mode, "--seed", "1", "--ticks", TICKS, "--out", p(f"{mode}{i}.jsonl")])
                       for i in (1, 2)]
            ok = all(c == 0 for c, _ in results)
            check(f"headless {mode} seed 1", ok, "mã thoát " + "/".join(str(c) for c, _ in results))
            same[mode] = ok and filecmp.cmp(p(f"{mode}1.jsonl"), p(f"{mode}2.jsonl"), shallow=False)
            check(f"so byte {mode} (2 lần)", same[mode], "giống từng byte" if same[mode] else "KHÁC hoặc thiếu file")

        with open(p("sc.json"), "w", encoding="utf-8") as f:
            json.dump({"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}}, f)
        with open(p("in.json"), "w", encoding="utf-8") as f:
            json.dump({"frames": [{"tick": 0, "interact": True}]}, f)
        c1, _ = run([*headless, "--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", p("sc.json"),
                     "--inputs", p("in.json"), "--inventory-out", p("kho.json"), "--out", p("flow_g.jsonl")])
        c2, _ = run([*headless, "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p("kho.json"),
                     "--out", p("flow_q.jsonl")]) if c1 == 0 else (1, "")
        stock = None
        if c2 == 0:
            with open(p("flow_q.jsonl"), encoding="utf-8") as f:
                stock = json.loads(f.readline()).get("stock")
        want = {"bong_sung": 2, "ca_loc": 1}
        check("luồng kho gather -> quan", stock == want, f"stock = {stock}")

        table = ["| Mục | Kết quả | Ghi chú |", "|---|---|---|"]
        table += [f"| {n} | {'ĐẠT' if ok else 'KHÔNG ĐẠT'} | {note} |" for n, ok, note in rows]
        passed = sum(ok for _, ok, _ in rows)
        table.append(f"\nTổng: {passed}/{len(rows)} mục đạt")
        print("\n".join(table))

        if a.proof:
            d = os.path.join(ROOT, a.proof)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "unittest.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write(unit_log)
            cmp_lines = []
            for mode in ("gather", "quan"):
                if os.path.exists(p(f"{mode}1.jsonl")):
                    shutil.copyfile(p(f"{mode}1.jsonl"), os.path.join(d, f"{mode}-seed1.jsonl.txt"))
                cmp_lines.append(f"{mode} seed 1, {TICKS} tick, 2 lần chạy: "
                                 + ("giống từng byte" if same[mode] else "KHÁC"))
            with open(os.path.join(d, "cmp.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(cmp_lines) + "\n")
            with open(os.path.join(d, "phase-check.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(table) + "\n")
    return 0 if all(ok for _, ok, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
