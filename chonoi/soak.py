"""Soak headless (TICKET-04 mục 2). Chủ: TV2 (lit1numyt).

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình bằng `runner.Session` mode `day` (cùng lớp sim với headless) và một bot TẤT ĐỊNH
(không ngẫu nhiên, không đồng hồ): mỗi Ngày đi gather → quan → shop; kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, earned,
uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt (DaySim lo).

Bot:
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
from .ids import id_key, sort_by_id
from .inputs import InputState
from .runner import Session

STOP = (0.0, 0.0)


def _toward(pos, target, slow_within=1.5):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return STOP
    k = 1.0 if d > slow_within else max(0.35, d / slow_within)
    return (dx / d * k, dy / d * k)


class Bot:
    """Bot tất định đọc trạng thái sim (chỉ đọc) và trả InputState cho bước kế."""

    def __init__(self, tuning):
        self.t = tuning
        self.cool = 0          # chờ vài bước sau mỗi lần bấm để trạng thái kịp đổi
        self.visited = set()   # nút đã hái trong Ngày (gather)
        self.day = None

    def act(self, day_sim) -> InputState:
        if day_sim.day != self.day:
            self.day, self.visited, self.cool = day_sim.day, set(), 0
        if self.cool > 0:
            self.cool -= 1
            return InputState(STOP, {}, set())
        phase, sim = day_sim.phase, day_sim.child
        if phase == "gather":
            return self._gather(sim)
        if phase == "quan":
            return self._quan(sim)
        return self._shop(day_sim)

    def _press(self, move=STOP, buy=None, button="interact"):
        self.cool = 3
        return InputState(move, {}, {button}, buy=buy)

    # --- gather ------------------------------------------------------------------------
    def _gather(self, g):
        t = self.t["gather"]
        reach = t["interact_radius"] * 0.6
        todo = [n for n in sorted(g.nodes, key=lambda n: (n["pos"][0], id_key(n["id"])))
                if n["id"] not in self.visited and n["regrow_ticks"] == 0 and len(g.hold) < t["hold_capacity"]]
        target = todo[0]["pos"] if todo else t["dock_pos"]
        pos = [g.pos[0], 0.0]  # giữ trên mặt nước
        if math.dist(pos, target) <= reach and abs(g.vel[0]) < 0.5:
            if todo:
                self.visited.add(todo[0]["id"])
            return self._press()
        mx, _ = _toward(pos, target)
        return InputState((mx, -1.0 if g.pos[1] > 0 else 0.0), {}, set())

    # --- quan --------------------------------------------------------------------------
    def _quan(self, q):
        reach = q.t["interact_radius"] * 0.6
        target = None
        if q.hand is not None:
            waiting = [c for c in sort_by_id(q.customers) if c["state"] == "waiting" and c["dish_id"] == q.hand]
            if waiting:
                target = next(tb["pos"] for tb in q.tables if tb["id"] == waiting[0]["table_id"])
        else:
            ready = [s for s in q.stoves if s["state"] == "ready"]
            idle = [s for s in q.stoves if s["state"] == "idle"]
            if ready:
                target = min(ready, key=lambda s: (math.dist(q.pos, s["pos"]), id_key(s["id"])))["pos"]
            elif idle and q._oldest_reserved_order() is not None:
                target = min(idle, key=lambda s: (math.dist(q.pos, s["pos"]), id_key(s["id"])))["pos"]
        if target is None:
            return InputState(STOP, {}, set())
        if math.dist(q.pos, target) <= reach and math.hypot(*q.vel) < 0.5:
            return self._press()
        return InputState(_toward(q.pos, target), {}, set())

    # --- shop --------------------------------------------------------------------------
    def _shop(self, d):
        shop = d.child
        table = self.t["shop"]["upgrades"]
        for kind in ("oxygen", "hp"):
            level = shop.upgrades.get(kind, 0) + 1
            if level <= len(table[kind]) and table[kind][level - 1]["price"] <= shop.money:
                return self._press(buy=kind, button="none")
        return self._press(button="shop_done")


def run_soak(tuning, seed, days):
    """Trả (days_completed, crashes, results). Lỗi trong sim được bắt và đếm là crash (dừng lượt)."""
    sess = Session("day", tuning, {}, seed, None, days)
    bot = Bot(tuning)
    results = []
    crashes = 0
    max_steps = days * (int(tuning["gather"]["duration_s"] * 60) + int(tuning["quan"]["duration_s"] * 60)
                        + int(tuning["shop"]["max_ticks"])) + 10
    try:
        while not sess.done and sess.tick < max_steps:
            sim = sess.sim
            for row in sess.step(bot.act(sim)):
                if row["name"] == "shop_end":
                    mult = tuning["score"]["reputation_multiplier"]
                    results.append({"day": row["day"], "earned": sim.earned, "reputation": sim.reputation,
                                    "score": sim.earned + mult * math.floor(sim.reputation)})
    except Exception:  # crash của luật: ghi nhận, không văng cả tiến trình
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
