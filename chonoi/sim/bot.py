"""Bot tất định cho soak (TICKET-04 mục 2; spec phase-4/bench-soak.md B3). Chủ: TV2 (lit1numyt).

CHỈ đọc snapshot (dict như dòng JSONL) + số liệu tuning; không RNG, không đồng hồ ⇒ tất định theo seed.
Mức nâng (B3): gather bơi trên mặt nước (an toàn khỏi Cá Sấu, không tốn oxy) qua các nút `ready` theo x tăng dần,
hái mỗi nút một lần, về bến khi giỏ đầy / hết nút / còn ≤ 20 s; quán: tay trống + bếp chín ⇒ nhặt, có đơn `reserved`
+ bếp rảnh ⇒ nấu, đang cầm món ⇒ giao cho khách đang chờ đúng món; Shop: mua cấp kế rẻ nhất đủ tiền rồi `shop_done`.
"""

import math

from ..ids import id_key
from ..inputs import InputState

STOP = (0.0, 0.0)
NONE = InputState(STOP, {}, set())


def _toward(pos, target, slow_within=1.5):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return STOP
    k = 1.0 if d > slow_within else max(0.35, d / slow_within)
    return (dx / d * k, dy / d * k)


class Bot:
    def __init__(self, tuning):
        self.t = tuning
        self.cool = 0          # chờ vài bước sau mỗi lần bấm để trạng thái kịp đổi
        self.visited = set()   # nút đã hái trong Ngày
        self.day = None

    def next(self, snap) -> InputState:
        if snap.get("day") != self.day:
            self.day, self.visited, self.cool = snap.get("day"), set(), 0
        if self.cool > 0:
            self.cool -= 1
            return NONE
        if snap["phase"] == "gather":
            return self._gather(snap)
        if snap["phase"] == "quan":
            return self._quan(snap)
        return self._shop(snap)

    def _press(self, move=STOP, buy=None, button="interact"):
        self.cool = 3
        return InputState(move, {}, {button}, buy=buy)

    def _gather(self, s):
        t = self.t["gather"]
        p = s["player"]
        reach = t["interact_radius"] * 0.6
        late = s["time_left_ticks"] <= 20 * 60
        todo = [] if late or len(s["hold"]) >= s["hold_capacity"] else \
            [n for n in sorted(s["nodes"], key=lambda n: (n["pos"][0], id_key(n["id"])))
             if n["ready"] and n["id"] not in self.visited]
        target = todo[0]["pos"] if todo else t["dock_pos"]
        pos = [p["pos"][0], 0.0]
        if math.dist(pos, target) <= reach and abs(p["vel"][0]) < 0.5:
            if todo:
                self.visited.add(todo[0]["id"])
            return self._press()
        mx, _ = _toward(pos, target)
        return InputState((mx, -1.0 if p["pos"][1] > 0 else 0.0), {}, set())

    def _quan(self, s):
        p = s["player"]
        reach = self.t["quan"]["interact_radius"] * 0.6
        target = None
        if s["hand"] is not None:
            waiting = [c for c in s["customers"] if c["state"] == "waiting" and c["dish_id"] == s["hand"]]
            if waiting:
                target = next(tb["pos"] for tb in s["tables"] if tb["id"] == waiting[0]["table_id"])
        else:
            ready = [st for st in s["stoves"] if st["state"] == "ready"]
            idle = [st for st in s["stoves"] if st["state"] == "idle"]
            has_order = any(c["state"] == "waiting" and c["order_status"] == "reserved" for c in s["customers"])
            pool = ready or (idle if has_order else [])
            if pool:
                target = min(pool, key=lambda st: (math.dist(p["pos"], st["pos"]), id_key(st["id"])))["pos"]
        if target is None:
            return NONE
        if math.dist(p["pos"], target) <= reach and math.hypot(*p["vel"]) < 0.5:
            return self._press()
        return InputState(_toward(p["pos"], target), {}, set())

    def _shop(self, s):
        table = self.t["shop"]["upgrades"]
        for kind in ("oxygen", "hp"):
            level = s["upgrades"].get(kind, 0) + 1
            if level <= len(table[kind]) and table[kind][level - 1]["price"] <= s["money"]:
                return self._press(buy=kind, button="none")
        return self._press(button="shop_done")
