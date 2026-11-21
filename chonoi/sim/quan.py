"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Chia việc trong file (docs/spec/phase-1/quan.md mục 0):
  TV2 (lát 3 — khách): `_tick_customers`, `_spawn_customer`, `_pick_dish`, `_can_cook`, `_free_stock`,
                       `_reserve`, `_release`, `_change_reputation`, phần khách trong `__init__`.
  TV1 (lát 4 — bếp):   `_tick_stoves`, `_tick_eating`, `_interact` (+ `_cook`, `_pick_up`, `_serve`, `_pay`).

Trường khách (snapshot + scenario `customers[]`), theo tên mà client khung (`chonoi/web/index.html`) đọc:
  id, table_id, dish_id, state ("waiting" | "eating"), patience_ticks_left, reserved {kind: n}
  (+ eat_ticks_left, price, tip khi "eating").
`reserved` = nguyên liệu đã GIỮ CHỖ nhưng CHƯA trừ khỏi kho. Khi bắt đầu nấu, lát 4 trừ kho rồi đặt reserved = {}.
Giả định chưa có trong PRD-0: xem docs/clarify.md #7–#12.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
CUSTOMER_STATES = ("waiting", "eating")
STOVE_STATES = ("idle", "cooking", "ready")


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # --- khách (TV2) ---
        self.patience_max = int(round(t["patience_s"] * TICK))
        self.eat_max = int(round(t["eat_s"] * TICK))
        self.first_customer_tick = int(t["first_customer_tick"])
        self.customer_interval = max(1, int(round(t["customer_interval_s"] * TICK)))
        self.random_customers = scenario.get("random_customers", True)
        self.customers = [self._customer_from_scenario(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._check_reserved_vs_stock()
        self.ticks = 0  # số bước đã chạy (= tick của dòng event trong bước này sau khi tăng)
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _customer_from_scenario(self, c):
        """Khách dựng sẵn; suy ra trường thiếu. Scenario đã kiểm schema ở chonoi/scenario.py."""
        state = c.get("state", "waiting")
        dish = c["dish_id"]
        out = {"id": c["id"], "table_id": c["table_id"], "dish_id": dish, "state": state,
               "patience_ticks_left": c.get("patience_ticks_left", self.patience_max)}
        if state == "waiting":
            out["reserved"] = dict(c.get("reserved", self.menu[dish]["recipe"]))
        else:
            out["reserved"] = {}
            out["eat_ticks_left"] = c.get("eat_ticks_left", self.eat_max)
            out["price"] = c["price"]
            out["tip"] = c["tip"]
        return out

    def _check_reserved_vs_stock(self):
        """Mâu thuẫn mức luật (kho có thể đến từ --inventory nên phải kiểm ở đây): tổng giữ chỗ > kho -> mã 2."""
        total = {}
        for c in self.customers:
            for k, n in c["reserved"].items():
                total[k] = total.get(k, 0) + n
        for k in sorted(total):
            if total[k] > self.stock.get(k, 0):
                raise BadInput(f"khách giữ chỗ {total[k]} {k} nhưng kho chỉ có {self.stock.get(k, 0)}")

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{**c, "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"])}}
                          for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        self.ticks += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # TODO(nhóm): giảm kiên nhẫn / nấu / ăn; bếp chín -> ready; xử lý khách theo thứ tự PRD-0 mục F.
        self._tick_customers(events)   # TV2: kiên nhẫn, bỏ đi        [đối chiếu thứ tự PRD-0 mục F]
        self._tick_stoves(events)      # TV1: nấu -> dish_ready
        self._tick_eating(events)      # TV1: ăn xong -> paid
        self._move(inp)                # khung
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        if inp.pressed("interact"):
            self._interact(events)     # TV1: tối đa MỘT đối tượng
        # TODO(nhóm): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish.
        self._spawn_customer(events)   # TV2: khách mới theo lịch, no_dish
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # --- TV2: khách (lát 3) ---------------------------------------------------------------
    def _free_stock(self) -> dict:
        """Kho chưa bị giữ chỗ = stock - Σ reserved."""
        free = dict(self.stock)
        for c in self.customers:
            for k, n in c["reserved"].items():
                free[k] = free.get(k, 0) - n
        return free

    def _can_cook(self, dish, stock_free) -> bool:
        return all(stock_free.get(k, 0) >= n for k, n in self.menu[dish]["recipe"].items())

    def _pick_dish(self):
        """Món ngẫu nhiên trong các món nấu được từ kho chưa giữ chỗ; None nếu không có. Ứng viên sắp theo tên."""
        free = self._free_stock()
        candidates = [d for d in sorted(self.menu) if self._can_cook(d, free)]
        if not candidates:
            return None
        return self.rng.get("customers").choice(candidates)

    def _reserve(self, customer, dish):
        customer["reserved"] = dict(self.menu[dish]["recipe"])

    def _release(self, customer):
        customer["reserved"] = {}

    def _change_reputation(self, delta):
        """Dùng chung với lát 4 (boa). Kẹp [reputation_min, reputation_max], làm tròn 3 chữ số để tránh trôi số thực."""
        r = self.reputation + delta
        r = max(self.t["reputation_min"], min(self.t["reputation_max"], r))
        self.reputation = round(r, 3)

    def _is_spawn_tick(self) -> bool:
        k, first = self.ticks, self.first_customer_tick
        return k >= first and (k - first) % self.customer_interval == 0

    def _spawn_customer(self, events):
        if not self.random_customers or not self._is_spawn_tick():
            return
        taken = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in taken]  # self.tables đã sắp theo id
        if not free_tables:
            return  # clarify #9: hết bàn -> bỏ lượt, không phát sự kiện
        dish = self._pick_dish()
        if dish is None:
            events.append(("no_dish", {"table_id": free_tables[0]["id"]}))
            return
        c = {"id": self.ids.new("C"), "table_id": free_tables[0]["id"], "dish_id": dish, "state": "waiting",
             "patience_ticks_left": self.patience_max, "reserved": {}}
        self._reserve(c, dish)
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": dish}))

    def _tick_customers(self, events):
        for c in sort_by_id(self.customers):
            if c["state"] != "waiting":
                continue
            c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            if c["patience_ticks_left"] == 0:
                self._release(c)
                self.customers.remove(c)
                self._change_reputation(self.t["left_reputation_delta"])
                events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                 "dish_id": c["dish_id"]}))

    # --- TV1: bếp, bưng, phục vụ, tiền (lát 4) -----------------------------------------
    def _interact(self, events):
        """Tối đa MỘT đối tượng: (khoảng cách, bếp trước bàn, id); không hợp lệ thì thôi."""
        near = []
        for kind, obj in [("stove", s) for s in self.stoves] + [("table", tb) for tb in self.tables]:
            d = math.dist(self.pos, obj["pos"])
            if d <= self.t["interact_radius"]:
                near.append((d, 0 if kind == "stove" else 1, id_key(obj["id"]), kind, obj))
        if not near:
            return
        near.sort(key=lambda e: (e[0], e[1], e[2]))
        _, _, _, kind, obj = near[0]  # chỉ xử lý đối tượng đầu, không thử đối tượng kế
        if kind == "stove":
            if obj["state"] == "idle":
                self._cook(obj, events)
            elif obj["state"] == "ready":
                self._pick_up(obj, events)
        else:
            self._serve(obj, events)

    def _cook(self, stove, events):
        """Bếp idle + tay trống + khách waiting chưa có món đang nấu -> nấu món khách id nhỏ nhất."""
        if stove["state"] != "idle" or self._hands_full():
            return
        busy = {s.get("dish") for s in self.stoves if s.get("state") in ("cooking", "ready")}
        customer = None
        for c in sort_by_id(self.customers):
            if c.get("state") != "waiting":
                continue
            dish = c.get("dish_id")
            if dish in self.menu and dish not in busy:
                customer = c
                break
        if customer is None:
            return
        dish = customer["dish_id"]
        # B2: chỉ trừ đúng phần đã giữ chỗ (không suy ra recipe khi reserved rỗng)
        recipe = customer.get("reserved") or {}
        if any(self.stock.get(k, 0) < n for k, n in recipe.items()):
            return
        # trừ kho phần nguyên liệu đã giữ chỗ; giữ chỗ coi như đã dùng xong
        for k, n in recipe.items():
            self.stock[k] = self.stock.get(k, 0) - n
        customer["reserved"] = {}
        stove["state"] = "cooking"
        stove["dish"] = dish
        stove["cook_ticks_left"] = int(round(self.menu[dish]["cook_s"] * TICK))
        stove["ready_ticks"] = 0
        events.append(("cook_started", {"stove_id": stove["id"], "dish": dish}))

    def _tick_stoves(self, events):
        """Nấu -> chín; burn_s null nên bếp ready chỉ đếm tick, không cháy món."""
        for stove in sort_by_id(self.stoves):
            if stove.get("state") == "cooking":
                stove["cook_ticks_left"] = max(0, stove.get("cook_ticks_left", 0) - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": stove["id"], "dish": stove["dish"]}))
            elif stove.get("state") == "ready":
                stove["ready_ticks"] = stove.get("ready_ticks", 0) + 1

    def _hands_full(self) -> bool:
        """Tay đầy khi đã cầm >= carry_limit món (số liệu đọc từ self.t; P1 = 1)."""
        carried = 0 if self.hand is None else 1
        return carried >= self.t["carry_limit"]

    def _pick_up(self, stove, events):
        """Bếp ready + tay trống (carry_limit) -> cầm món, bếp về idle."""
        if stove.get("state") != "ready" or self._hands_full():
            return
        dish = stove["dish"]
        self.hand = dish
        stove["state"] = "idle"
        stove["dish"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0
        events.append(("dish_picked", {"stove_id": stove["id"], "dish": dish}))

    def _serve(self, table, events):
        """Bàn có khách waiting đúng món đang cầm -> served, chốt price/tip."""
        customer = None
        for c in sort_by_id(self.customers):
            if c.get("table_id") == table["id"] and c.get("state") == "waiting":
                customer = c
                break
        if customer is None or self.hand is None or customer.get("dish_id") != self.hand:
            return
        dish = customer["dish_id"]
        price = self.menu[dish]["price"]
        full = self.t["patience_s"] * TICK
        patience = customer.get("patience_ticks_left", full)
        tip = round(price * self.t["tip_rate"]) if patience / full >= self.t["tip_min_patience_ratio"] else 0
        self.hand = None
        customer["state"] = "eating"
        customer["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        customer["price"] = price
        customer["tip"] = tip
        events.append(("served", {"customer_id": customer["id"], "table_id": table["id"], "dish": dish}))

    def _tick_eating(self, events):
        """Ăn xong -> paid (tiền + uy tín), khách rời bàn."""
        paid_ids = []
        for c in sort_by_id(self.customers):
            if c.get("state") != "eating":
                continue
            c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", int(round(self.t["eat_s"] * TICK))) - 1)
            if c["eat_ticks_left"] == 0:
                self._pay(c, events)
                paid_ids.append(c["id"])
        if paid_ids:
            self.customers = [c for c in self.customers if c["id"] not in paid_ids]

    def _pay(self, customer, events):
        """Cộng tiền/doanh thu; có boa thì cộng uy tín (kẹp [reputation_min, reputation_max])."""
        price = customer.get("price", 0)
        tip = customer.get("tip", 0)
        amount = price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._change_reputation(self.t["tip_reputation"])
        events.append(("paid", {"customer_id": customer["id"], "amount": amount, "tip": tip}))

    # --- khung ---------------------------------------------------------------------------
    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
