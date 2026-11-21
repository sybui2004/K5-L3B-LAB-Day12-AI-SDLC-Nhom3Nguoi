"""Buổi tối — Mở Quán (Test Contract v1.1, TICKET-02 mục 1.3). Chủ: TV2 (lit1numyt).

Thứ tự một bước (giữ v1.0): đồng hồ → kiên nhẫn (bỏ đi) → bếp (nấu → chín) → ăn (→ trả tiền) → đi lại
→ tối đa MỘT interact → khách mới theo lịch → hết giờ thì đóng ca (`_close_shift`) rồi `quan_end`.

Khách (snapshot + scenario `customers[]`): id, table_id, dish_id, state ("waiting" | "eating"),
  patience_ticks_left, order_tick, order_status ("reserved" | "cooking" | "ready" | "served"), reserved {kind: n}
  (+ eat_ticks_left, price, tip khi "eating").
`reserved` = nguyên liệu đã GIỮ nhưng CHƯA trừ khỏi kho; bắt đầu nấu thì trừ kho và đặt reserved = {}.
Bếp: id, pos, state ("idle" | "cooking" | "ready"), dish, order_id (id khách của đơn, null nếu khách đã đi),
  cook_ticks_left, ready_ticks. Tay cầm `hand` = id món hoặc null (carry_limit 1).
Giả định ngoài ticket: docs/clarify.md #7–#12, #20–#27.
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, dishes=None, carry=None):
        """`dishes`: danh sách id món của kế hoạch Ngày (mode day); None = cả menu (quán chạy riêng).
        `carry`: {money, earned, reputation} mang từ Ngày trước (mode day)."""
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); day truyền kho bàn giao qua inventory
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        carry = carry or {}
        self.reputation = carry.get("reputation", scenario.get("reputation", t["reputation_initial"]))
        self.money = carry.get("money", 0)
        self.earned = carry.get("earned", 0)
        self.shift_earned = 0
        self.dishes = sorted(dishes) if dishes is not None else sorted(self.menu)
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"), order_id=s.get("order_id"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.patience_max = int(round(t["patience_s"] * TICK))
        self.eat_max = int(round(t["eat_s"] * TICK))
        self.first_customer_tick = int(t["first_customer_tick"])
        self.customer_interval = max(1, int(round(t["customer_interval_s"] * TICK)))
        self.random_customers = scenario.get("random_customers", True)
        self.customers = [self._customer_from_scenario(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._check_rules()
        self.ticks = 0  # số bước đã chạy (= tick của dòng event phát trong bước này)
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
        """Khách dựng sẵn; suy ra trường thiếu. Schema đã kiểm ở chonoi/scenario.py."""
        state = c.get("state", "waiting")
        dish = c["dish_id"]
        out = {"id": c["id"], "table_id": c["table_id"], "dish_id": dish, "state": state,
               "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
               "order_tick": c.get("order_tick", 0)}
        if state == "waiting":
            # reserved: {} mà không khai order_status => món đã được nấu (clarify #21)
            default_status = "cooking" if c.get("reserved") == {} else "reserved"
            out["order_status"] = c.get("order_status", default_status)
            out["reserved"] = dict(c.get("reserved", self.menu[dish]["recipe"] if out["order_status"] == "reserved" else {}))
        else:
            out["order_status"] = "served"
            out["reserved"] = {}
            out["eat_ticks_left"] = c.get("eat_ticks_left", self.eat_max)
            out["price"] = c["price"]
            out["tip"] = c["tip"]
        return out

    def _check_rules(self):
        """Mâu thuẫn mức luật cần biết kho thực (có thể từ --inventory / bàn giao của day) -> mã 2."""
        total = {}
        for c in self.customers:
            for k, n in c["reserved"].items():
                total[k] = total.get(k, 0) + n
        for k in sorted(total):
            if total[k] > self.stock.get(k, 0):
                raise BadInput(f"khách giữ chỗ {total[k]} {k} nhưng kho chỉ có {self.stock.get(k, 0)}")
        allowed = set(self.dishes)
        for c in self.customers:
            if c["dish_id"] not in allowed:
                raise BadInput(f"customers.{c['id']}: món {c['dish_id']} không thuộc kế hoạch Ngày")
        for s in self.stoves:
            if s["dish"] is not None and s["dish"] not in allowed:
                raise BadInput(f"stoves.{s['id']}: món {s['dish']} không thuộc kế hoạch Ngày")
        if self.hand is not None and self.hand not in allowed:
            raise BadInput(f"hand: món {self.hand} không thuộc kế hoạch Ngày")

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "shift_earned": self.shift_earned,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "order_id", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{**c, "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"])}}
                          for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        self.ticks += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_customers(events)
        self._tick_stoves(events)
        self._tick_eating(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._spawn_customer(events)
        if self.time_left_ticks <= 0:
            self._close_shift(events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # --- tiện ích chung ------------------------------------------------------------------
    def _free_stock(self) -> dict:
        """Kho chưa bị giữ chỗ = stock - Σ reserved."""
        free = dict(self.stock)
        for c in self.customers:
            for k, n in c["reserved"].items():
                free[k] = free.get(k, 0) - n
        return free

    def _can_cook(self, dish, stock_free) -> bool:
        return all(stock_free.get(k, 0) >= n for k, n in self.menu[dish]["recipe"].items())

    def _change_reputation(self, delta):
        """Kẹp [reputation_min, reputation_max], làm tròn 3 chữ số để tránh trôi số thực."""
        r = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta))
        self.reputation = round(r, 3)

    def _stove_of(self, customer_id):
        return next((s for s in self.stoves if s["order_id"] == customer_id), None)

    def _remove_customer(self, c):
        """Khách rời bàn: nhả giữ chỗ; món đang nấu/chín của khách thành món vô chủ (order_id = null)."""
        c["reserved"] = {}
        s = self._stove_of(c["id"])
        if s is not None:
            s["order_id"] = None
        self.customers.remove(c)

    # --- khách ---------------------------------------------------------------------------
    def _pick_dish(self):
        """Chọn đều theo seed trong các món (kế hoạch/menu) nấu được từ kho chưa giữ chỗ; ứng viên sắp theo id."""
        free = self._free_stock()
        candidates = [d for d in self.dishes if self._can_cook(d, free)]
        if not candidates:
            return None
        return self.rng.get("customers").choice(candidates)

    def _is_spawn_tick(self) -> bool:
        k, first = self.ticks, self.first_customer_tick
        return k >= first and (k - first) % self.customer_interval == 0

    def _spawn_customer(self, events):
        if not self.random_customers or self.time_left_ticks <= 0 or not self._is_spawn_tick():
            return
        taken = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in self.tables if tb["id"] not in taken]  # self.tables đã sắp theo id
        if not free_tables:
            return  # clarify #9: hết bàn -> bỏ lượt, không phát sự kiện
        table_id = free_tables[0]["id"]
        dish = self._pick_dish()
        if dish is None:
            events.append(("no_dish", {"table_id": table_id}))
            return
        c = {"id": self.ids.new("C"), "table_id": table_id, "dish_id": dish, "state": "waiting",
             "patience_ticks_left": self.patience_max, "order_tick": self.ticks, "order_status": "reserved",
             "reserved": dict(self.menu[dish]["recipe"])}
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": table_id, "dish_id": dish}))

    def _tick_customers(self, events):
        if self.time_left_ticks <= 0:
            return  # bước cuối: đóng ca xử lý mọi khách, không trừ uy tín (TICKET-02 1.3)
        for c in sort_by_id(self.customers):
            if c["state"] != "waiting":
                continue
            c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
            if c["patience_ticks_left"] == 0:
                self._remove_customer(c)
                self._change_reputation(self.t["left_reputation_delta"])
                events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                 "dish_id": c["dish_id"], "reason": "patience"}))

    # --- bếp -----------------------------------------------------------------------------
    def _tick_stoves(self, events):
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"], s["ready_ticks"] = "ready", 0
                    c = self._customer(s["order_id"])
                    if c is not None:
                        c["order_status"] = "ready"
                    events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["order_id"], "dish_id": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] += 1  # burn_s null trong lõi: chỉ đếm tuổi món chín

    def _customer(self, cid):
        return next((c for c in self.customers if c["id"] == cid), None) if cid else None

    def _oldest_reserved_order(self):
        orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        return orders[0] if orders else None

    def _cook(self, s, c, events):
        for k, n in c["reserved"].items():
            self.stock[k] = self.stock.get(k, 0) - n
            if self.stock[k] == 0:
                del self.stock[k]
        c["reserved"] = {}
        c["order_status"] = "cooking"
        s.update(state="cooking", dish=c["dish_id"], order_id=c["id"], ready_ticks=0,
                 cook_ticks_left=int(round(self.menu[c["dish_id"]]["cook_s"] * TICK)))
        events.append(("cook_started", {"stove_id": s["id"], "order_id": c["id"], "dish_id": c["dish_id"]}))

    def _pick_up(self, s, events):
        self.hand = s["dish"]
        events.append(("dish_picked", {"stove_id": s["id"], "order_id": s["order_id"], "dish_id": s["dish"]}))
        s.update(state="idle", dish=None, order_id=None, cook_ticks_left=0, ready_ticks=0)

    # --- bàn, phục vụ, trả tiền ------------------------------------------------------------
    def _serve(self, c, events):
        price = self.menu[c["dish_id"]]["price"]
        tip = 0
        if c["patience_ticks_left"] >= self.t["tip_min_patience_ratio"] * self.patience_max:
            tip = math.floor(price * self.t["tip_rate"] + 1e-9)
        # món giao có thể không phải món nấu cho chính đơn này: nhả giữ chỗ / gỡ đơn khỏi bếp
        c["reserved"] = {}
        s = self._stove_of(c["id"])
        if s is not None:
            s["order_id"] = None
        self.hand = None
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_max, price=price, tip=tip)
        events.append(("served", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "price": price, "tip": tip}))

    def _tick_eating(self, events):
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] == 0:
                    self._pay(c, events)

    def _pay(self, c, events):
        amount = c["price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self._change_reputation(self.t["tip_reputation"])
        self.customers.remove(c)
        events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                "price": c["price"], "tip": c["tip"], "amount": amount}))

    def _interact(self, events):
        """Tối đa MỘT đối tượng: gần nhất trong interact_radius, hòa thì bếp trước bàn rồi id."""
        r = self.t["interact_radius"]
        cands = [(math.dist(self.pos, s["pos"]), 0, id_key(s["id"]), s) for s in self.stoves]
        cands += [(math.dist(self.pos, tb["pos"]), 1, id_key(tb["id"]), tb) for tb in self.tables]
        cands = [x for x in cands if x[0] <= r]
        if not cands:
            return
        _, kind, _, obj = min(cands, key=lambda x: x[:3])
        if kind == 0:
            if obj["state"] == "idle":
                c = self._oldest_reserved_order()
                if c is not None:
                    self._cook(obj, c, events)
            elif obj["state"] == "ready" and self.hand is None:
                self._pick_up(obj, events)
        else:
            c = next((c for c in self.customers if c["table_id"] == obj["id"]), None)
            if c is not None and c["state"] == "waiting" and self.hand == c["dish_id"]:
                self._serve(c, events)

    # --- đóng ca ---------------------------------------------------------------------------
    def _close_shift(self, events):
        """Khách đang ăn trả ngay; khách đang chờ rời, không trừ uy tín; dọn món trên bếp, tay và phần giữ."""
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                self._pay(c, events)
            else:
                self._remove_customer(c)
                events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                 "dish_id": c["dish_id"], "reason": "closing"}))
        for s in self.stoves:
            s.update(state="idle", dish=None, order_id=None, cook_ticks_left=0, ready_ticks=0)
        self.hand = None

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
