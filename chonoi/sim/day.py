"""Chế độ `day` (Test Contract v1.1, TICKET-02 mục 2 + 4). Chủ: TV2 (lit1numyt).

Vòng một Ngày (headless): day_start → day_plan → phase_start(gather) → gather → gather_end
  → phase_start(quan) (cùng tick) → quan → quan_end → phase_start(shop) (cùng tick) → Shop → shop_end
  → days_completed += 1 → hết số Ngày thì kết thúc (reason "days_complete"), không thì dựng Ngày kế ngay tick đó.
DayIntro / EveningIntro / DayResult / Summary là màn hình của client (TV3), không có trong headless.

Trả sự kiện dạng (name, data, phase, day): sự kiện kết thúc mang pha cũ, phase_start mang pha mới.
Giao diện các sim theo hợp đồng chuyển pha (spec phase-2/README.md 3.2): `ctx`, một `Streams` và một `IdAllocator`
cho cả lượt. Tiền, earned, uy tín và cấp đã mua giữ qua Ngày. Oxy/Máu theo cấp ĐANG ÁP DỤNG (active_upgrades), chỉ sao từ
cấp đã mua khi dựng Ngày mới. Giỏ làm mới mỗi Ngày; kho dư bị bỏ sau Shop.
"""

import copy
import inspect

from ..errors import BadInput
from ..ids import IdAllocator, sort_by_id
from .gather import GatherSim
from .plan import plan_ingredients
from .quan import QuanSim
from .shop import UPGRADE_FIELD, ShopSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.streams = streams
        self.ids = ids  # dùng chung cả lượt (hợp đồng 3.2)
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
                                    "ingredients": plan_ingredients(p["dishes"], tuning["menu"])}
        self.g_tpl = scenario.get("gather", {})
        # v1.2 (TICKET-03, AC-P3-13): một allocator RIÊNG cho cá thể, sống suốt lượt; id có sẵn trong mẫu hold được giữ.
        self.item_ids = IdAllocator()
        for it in self.g_tpl.get("hold", []):
            if isinstance(it, dict):
                self.item_ids.reserve(it["id"])
        self.q_tpl = scenario.get("quan", {})
        self.day = 0
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0
        self.phase_changed = False
        self.child = None
        self.last_stats = None
        self.done = False
        self.reason = None
        self.pending = []  # sự kiện tick 0 (day_start, day_plan, phase_start) — runner ghi SAU snapshot tick 0 (clarify #19)
        self._start_day(self.pending)

    def _plan(self):
        """Kế hoạch của Ngày hiện tại; sau Ngày 5 lặp lại D1–D5 (TICKET-04 soak: Ngày 6–10 dùng D1–D5)."""
        return self.plans[(self.day - 1) % len(self.tuning["day_plan"]) + 1]

    # --- giao diện cho runner ----------------------------------------------------------
    @property
    def time_left_ticks(self):
        return self.child.time_left_ticks

    def snapshot(self) -> dict:
        snap = self.child.snapshot()
        if self.phase == "shop" and self.last_stats is not None:
            snap["day_result"] = self.last_stats  # DayResult: phục vụ, bỏ đi, tiền ca, boa, đổi uy tín, món bán chạy
        plan = self._plan()
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
        else:
            self._tag(events, self.child.step(inp))
            self.money, self.earned, self.reputation = self.child.money, self.child.earned, self.child.reputation
            if self.phase == "shop":
                self.upgrades = dict(self.child.upgrades)
            if self.child.done:
                if self.phase == "quan":
                    self._open_shop(events)
                else:
                    self._close_day(events)
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
        plan = self._plan()
        events.append(("day_start", {}, "gather", self.day))
        events.append(("day_plan", {"dishes": plan["dishes"], "ingredients": plan["ingredients"]}, "gather", self.day))
        # ctx cho gather (hp_max, oxygen_max_s theo cấp đang áp dụng). Khi GatherSim chưa nhận ctx (TV1),
        # vẫn ghi đè hai khóa đó trong bản sao tuning để cấp có hiệu lực.
        t = copy.deepcopy(self.tuning)
        ctx = {"day": self.day}
        for kind, field in UPGRADE_FIELD.items():
            level = self.active_upgrades.get(kind, 0)
            value = self.tuning["shop"]["upgrades"][kind][level - 1][field] if level > 0 else self.tuning["gather"][field]
            ctx[field] = t["gather"][field] = value
        params = inspect.signature(GatherSim.__init__).parameters
        kwargs = {k: v for k, v in (("ctx", ctx), ("item_ids", self.item_ids)) if k in params}
        self.child = GatherSim(t, self._gather_template(), self.streams, self.ids, **kwargs)
        self._enter("gather", events)

    def _gather_template(self):
        """Ngày 1 giữ nguyên id trong mẫu gather.hold; Ngày 2+ cấp id MỚI theo thứ tự mảng, giữ kind/fresh ban đầu."""
        hold = self.g_tpl.get("hold")
        if self.day == 1 or not hold or not isinstance(hold[0], dict):
            return self.g_tpl
        fresh_hold = [{"id": self.item_ids.new("I"), "kind": it["kind"], "fresh": it["fresh"]} for it in hold]
        return {**self.g_tpl, "hold": fresh_hold}

    def _open_quan(self, events):
        """Bàn giao trong CÙNG tick gather_end, không hao thêm; ngất ⇒ kho rỗng. Kho đếm (gather chưa v1.2) được đổi
        sang cá thể mới bằng allocator chung."""
        items = [] if self.child.reason == "fainted" else sort_by_id(self.child.hold)  # giữ fresh chưa làm tròn (ADR 0001)
        ctx = {"day": self.day, "plan_dishes": dict(self._plan()["dishes"]),
               "money": self.money, "earned": self.earned, "reputation": self.reputation}
        self.child = QuanSim(self.tuning, self.q_tpl, self.streams, self.ids, inventory=items, ctx=ctx,
                             item_ids=self.item_ids)
        self._enter("quan", events)

    def _open_shop(self, events):
        self.last_stats = self.child.stats()  # cho DayResult (TV3)
        ctx = {"day": self.day, "money": self.money, "earned": self.earned, "reputation": self.reputation,
               "upgrades": self.upgrades, "stock": self.child.stock}
        self.child = ShopSim(self.tuning, self.streams, self.ids, ctx)
        self._enter("shop", events)

    def _close_day(self, events):
        """Shop đã phát shop_end: tăng days_completed, kết thúc hoặc dựng Ngày kế ngay tick này (kho dư bị bỏ)."""
        self.days_completed += 1
        if self.days_completed >= self.days:
            self.done = True
            self.reason = "days_complete"
            return
        self._start_day(events)


def validate_days(days):
    if isinstance(days, bool) or not isinstance(days, int) or not (1 <= days <= 5):
        raise BadInput("--days phải là số nguyên từ 1 đến 5")
