"""Soak headless (TICKET-04 mục 2). Chủ: TV2 (lit1numyt).

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình bằng `runner.Session` mode `day` (cùng lớp sim với headless) và một bot TẤT ĐỊNH
(không ngẫu nhiên, không đồng hồ): mỗi Ngày đi gather → quan → shop; kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, earned,
uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt (DaySim lo).

Bot (`chonoi/sim/bot.py`, chỉ đọc snapshot):
- gather: bơi trên mặt nước (an toàn khỏi Cá Sấu, không tốn oxy) qua các nút hái theo x tăng dần, hái mỗi nút một lần,
  rồi quay về bến và cập bến.
- quan: tay trống + bếp có món chín ⇒ tới nhặt; có đơn reserved + bếp rảnh ⇒ tới bếp nấu; đang cầm món ⇒ tới bàn của
  khách đang chờ đúng món. Đi thẳng tới mục tiêu (xuyên nội thất), dừng trong bán kính rồi bấm interact.
- shop: mua cấp kế tiếp rẻ nhất đủ tiền (oxygen trước hp), rồi shop_done.

Xuất soak.json {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}; `results` lấy ở
tick Shop đóng. Chỉ `duration_s` là số đo thời gian thực (bỏ khi so lặp). Không ghi file xếp hạng.
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .runner import Session
from .sim.bot import Bot

def run_soak(tuning, seed, days):
    """Trả (days_completed, crashes, results). Lỗi trong sim hoặc kẹt quá giới hạn tick ⇒ crash (dừng lượt)."""
    sess = Session("day", tuning, {}, seed, None, days)
    bot = Bot(tuning)
    results = []
    crashes = 0
    mult = tuning["score"]["reputation_multiplier"]
    max_steps = days * (int(tuning["gather"]["duration_s"] * 60) + int(tuning["quan"]["duration_s"] * 60)
                        + int(tuning["shop"]["max_ticks"]) + 10)
    try:
        while not sess.done:
            if sess.tick >= max_steps:
                raise RuntimeError(f"stuck: quá {max_steps} tick mà chưa xong {days} Ngày")
            for row in sess.step(bot.next(sess.snapshot())):
                if row["name"] == "shop_end":
                    sim = sess.sim  # giá trị LŨY KẾ của lượt lúc Shop đóng (clarify #37)
                    results.append({"day": row["day"], "earned": sim.earned, "reputation": round(sim.reputation, 3),
                                    "score": sim.earned + mult * math.floor(sim.reputation)})
    except Exception:  # crash của luật / kẹt: ghi nhận, vẫn ghi soak.json
        crashes += 1
        traceback.print_exc(file=sys.stderr)
    return sess.sim.days_completed, crashes, results


def write_json_atomic(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=d)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.days < 1:
        sys.stderr.write("đầu vào sai: --days phải >= 1\n")
        return 2
    try:
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    t0 = time.perf_counter()
    done, crashes, results = run_soak(tuning, a.seed, a.days)
    out = {"days": a.days, "days_completed": done, "crashes": crashes, "results": results,
           "duration_s": round(time.perf_counter() - t0, 3)}
    try:
        write_json_atomic(a.out, out)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0 if crashes == 0 and done == a.days else 1


if __name__ == "__main__":
    sys.exit(main())
