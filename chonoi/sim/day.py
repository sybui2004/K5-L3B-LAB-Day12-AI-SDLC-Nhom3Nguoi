"""Chế độ `day` (Test Contract v1.1, TICKET-02 mục 2 + 4). Chủ: TV2 (lit1numyt).

Vòng một Ngày (headless): day_start → day_plan → phase_start(gather) → gather → gather_end
  → phase_start(quan) (cùng tick) → quan → quan_end → phase_start(shop) (cùng tick) → Shop → shop_end
  → days_completed += 1 → hết số Ngày thì kết thúc (reason "days_complete"), không thì dựng Ngày kế ngay tick đó.
DayIntro / EveningIntro / DayResult / Summary là màn hình của client (TV3), không có trong headless.

Trả sự kiện dạng (name, data, phase, day): sự kiện kết thúc mang pha cũ, phase_start mang pha mới.
Tiền, earned, uy tín và cấp đã mua giữ qua Ngày. Oxy/Máu theo cấp ĐANG ÁP DỤNG (active_upgrades), chỉ sao từ
cấp đã mua khi dựng Ngày mới. Giỏ làm mới mỗi Ngày; kho dư bị bỏ sau Shop.
"""

import copy
import inspect

from ..errors import BadInput
from ..ids import IdAllocator
from .gather import GatherSim
from .quan import QuanSim

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}  # id nâng cấp -> khóa tuning gather bị ghi đè


def plan_ingredients(menu, dishes):
    out = {}
    for dish, n in dishes.items():
        for k, m in menu[dish]["recipe"].items():
            out[k] = out.get(k, 0) + m * n
    return {k: out[k] for k in sorted(out)}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.streams = streams
        self.days = days
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", 0)
        self.reputation = d.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = {}
        self.plans = {p["day"]: {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
                      for p in tuning["day_plan"]}
        for p in d.get("day_plan", []):  # ghi đè theo số Ngày; ingredients tính lại (scenario đã so nếu có khai)
            self.plans[p["day"]] = {"dishes": dict(p["dishes"]),
                                    "ingredients": plan_ingredients(tuning["menu"], p["dishes"])}
        self.g_tpl = scenario.get("gather", {})
        self.q_tpl = scenario.get("quan", {})
        self.day = 0
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0
        self.phase_changed = False
        self.child = None
        self.shop_left = 0
        self.leftover = {}
        self.done = False
        self.reason = None
        self.pending = []  # sự kiện tick 0 (day_start, day_plan, phase_start) — runner ghi trước snapshot tick 0
        self._start_day(self.pending)

    # --- giao diện cho runner ----------------------------------------------------------
    @property
    def time_left_ticks(self):
        return self.shop_left if self.phase == "shop" else self.child.time_left_ticks

    def snapshot(self) -> dict:
        if self.phase == "shop":
            snap = {"stock": {k: self.leftover[k] for k in sorted(self.leftover) if self.leftover[k] > 0}}
        else:
            snap = self.child.snapshot()
        plan = self.plans[self.day]
        snap.update({"day": self.day, "days_completed": self.days_completed,
                     "day_plan": {"dishes": plan["dishes"], "ingredients": plan["ingredients"]},
                     "upgrades": {k: self.upgrades[k] for k in sorted(self.upgrades)},
                     "active_upgrades": {k: self.active_upgrades[k] for k in sorted(self.active_upgrades)}})
        return snap

    def step(self, inp):
        events = []
        self.phase_changed = False
        self.phase_tick += 1
        if self.phase == "gather":
            self._tag(events, self.child.step(inp))
            if self.child.done:
                self._open_quan(events)
        elif self.phase == "quan":
            self._tag(events, self.child.step(inp))
            self.money, self.earned, self.reputation = self.child.money, self.child.earned, self.child.reputation
            if self.child.done:
                self._open_shop(events)
        else:
            self._shop_step(inp, events)
        return events

    # --- đổi pha -------------------------------------------------------------------------
    def _tag(self, events, evs, phase=None):
        for name, data in evs:
            events.append((name, data, phase or self.phase, self.day))

    def _enter(self, phase, events):
        self.phase = phase
        self.phase_tick = 0
        self.phase_changed = True
        events.append(("phase_start", {}, phase, self.day))

    def _start_day(self, events):
        self.day += 1
        self.active_upgrades = dict(self.upgrades)
        plan = self.plans[self.day]
        events.append(("day_start", {}, "gather", self.day))
        events.append(("day_plan", {"dishes": plan["dishes"], "ingredients": plan["ingredients"]}, "gather", self.day))
        t = copy.deepcopy(self.tuning)
        for kind, level in self.active_upgrades.items():
            if level > 0:
                row = self.tuning["shop"]["upgrades"][kind][level - 1]
                t["gather"][UPGRADE_FIELD[kind]] = row[UPGRADE_FIELD[kind]]
        kwargs = {"day": self.day} if "day" in inspect.signature(GatherSim.__init__).parameters else {}
        self.child = GatherSim(t, self.g_tpl, self.streams, IdAllocator(), **kwargs)
        self._enter("gather", events)

    def _open_quan(self, events):
        items = {} if self.child.reason == "fainted" else self.child.inventory_items()
        dishes = sorted(self.plans[self.day]["dishes"])
        carry = {"money": self.money, "earned": self.earned, "reputation": self.reputation}
        self.child = QuanSim(self.tuning, self.q_tpl, self.streams, IdAllocator(), inventory=items,
                             dishes=dishes, carry=carry)
        self._enter("quan", events)

    def _open_shop(self, events):
        self.leftover = dict(self.child.stock)
        self.child = None
        self.shop_left = int(self.tuning["shop"]["max_ticks"])
        self._enter("shop", events)

    # --- Shop ----------------------------------------------------------------------------
    def _shop_step(self, inp, events):
        self.shop_left = max(0, self.shop_left - 1)
        if inp.buy:
            self._buy(inp.buy, events)  # một lệnh mua xử lý TRƯỚC cạnh shop_done, kể cả bước cuối
        if inp.pressed("shop_done"):
            self._close_shop("done", events)
        elif self.shop_left == 0:
            self._close_shop("time", events)

    def _buy(self, action, events):
        table = self.tuning["shop"]["upgrades"].get(action)
        if action not in UPGRADE_FIELD or table is None:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}, "shop", self.day))
            return
        level = self.upgrades.get(action, 0) + 1
        if level > len(table):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}, "shop", self.day))
            return
        price = table[level - 1]["price"]
        if price > self.money:
            events.append(("buy_failed", {"action": action, "reason": "funds"}, "shop", self.day))
            return
        self.money -= price  # earned và điểm giữ nguyên
        self.upgrades[action] = level
        events.append(("bought", {"upgrade": action, "level": level, "price": price, "money": self.money},
                       "shop", self.day))

    def _close_shop(self, reason, events):
        events.append(("shop_end", {"reason": reason}, "shop", self.day))
        self.days_completed += 1
        self.leftover = {}
        if self.days_completed >= self.days:
            self.done = True
            self.reason = "days_complete"
            return
        self._start_day(events)


def validate_days(days):
    if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= 5):
        raise BadInput("--days phải là số nguyên từ 1 đến 5")
