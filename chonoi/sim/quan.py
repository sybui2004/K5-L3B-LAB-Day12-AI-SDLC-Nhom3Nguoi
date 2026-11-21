"""Buổi tối — Mở Quán (Test Contract v1.2, TICKET-03 "Mùa Nước Nổi"; v1.1 TICKET-02 mục 1.3). Chủ: TV2 (lit1numyt).

Thứ tự một bước (TICKET-03 mục 1 "Thứ tự trong tick", spec phase-3/quan-day.md B):
  đồng hồ → hao tươi kho thô, phát hết `spoiled` theo id, rồi xử lý giữ chỗ bị ươn → món chín (theo id bếp)
  → đi lại + tối đa MỘT interact → thanh toán, kiên nhẫn / đóng ca → còn giờ thì khách mới.
  Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ; giao đúng tick hết ca được trả ngay.

Kho `stock` = list cá thể {id, kind, fresh (Fraction)} (chonoi/inventory.py), nhận nguyên id/fresh kể cả hàng ươn,
hao quan_decay_per_s kể cả hàng đang giữ. Ươn (fresh < spoiled_below) vẫn nằm trong kho, không giữ/nấu được.
Khách (snapshot + scenario `customers[]`): id, table_id, dish_id, state ("waiting" | "eating"), patience_ticks_left,
  order_tick, order_status ("reserved" | "unfulfillable" | "cooking" | "ready" | "served"),
  reserved = mảng id cá thể đang giữ (sắp theo kind rồi id) (+ eat_ticks_left, price, tip khi "eating").
Bếp: id, pos, state, dish, order_id, base_price, cook_ticks_left, ready_ticks. Tay: `hand` (id món) + `hand_base_price`.
Giá: bắt đầu nấu tiêu đúng các id đang giữ, base_price = floor(giá × TB fresh / 100); boa floor(base_price × tip_rate).
Giả định ngoài ticket: docs/clarify.md #7–#12, #20–#24, #28–#30.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import IdAllocator, id_key, sort_by_id
from ..inventory import as_items, decay, decay_per_tick, freshness, is_spoiled, item_out, to_fresh
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, ctx=None, item_ids=None):
        """`ctx` (hợp đồng chuyển pha 3.2; None = quán chạy riêng, cả 6 món): `plan_dishes`, `money`, `earned`,
        `reputation`, `day`. `item_ids`: IdAllocator cá thể dùng suốt lượt (day); None = allocator riêng."""
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        fr = freshness(tuning)
        self.decay_tick = decay_per_tick(fr["quan_decay_per_s"])
        self.spoiled_below = fr["spoiled_below"]
        self.tip_rate = to_fresh(t["tip_rate"])
        self.item_ids = item_ids if item_ids is not None else IdAllocator()
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2); day truyền kho bàn giao qua inventory.
        # Nhận cả kho đếm (manifest 1.1) lẫn mảng cá thể (1.2).
        self.stock = as_items(inventory if inventory is not None else scenario.get("stock", []), self.item_ids, tuning)
        self.hand = scenario.get("hand")
        self.hand_base_price = self.menu[self.hand]["price"] if self.hand in self.menu else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        carry = ctx or {}
        dishes = carry.get("plan_dishes")
        self.reputation = carry.get("reputation", scenario.get("reputation", t["reputation_initial"]))
        self.money = carry.get("money", 0)
        self.earned = carry.get("earned", 0)
        self.shift_earned = 0
        self._rep_start = self.reputation
        self._served_by_dish = {}
        self._left = 0
        self._tips = 0
        self.dishes = sorted(dishes) if dishes is not None else sorted(self.menu)
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"), order_id=s.get("order_id"),
                            base_price=s.get("base_price", self.menu[s["dish"]]["price"] if s.get("dish") else None),
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
        self.ticks = 0  # = phase_tick: số bước gameplay của quán (pause không tăng, clarify #13)
        self.done = False
        self.reason = None
        self._served_now = set()

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _customer_from_scenario(self, c):
        """Khách dựng sẵn; suy ra trường thiếu. Schema đã kiểm ở chonoi/scenario.py; `reserved` kiểm trên kho thực
        ở `_check_rules` (mảng id v1.2; map recipe v1.1 hoặc bỏ trống ⇒ tự cấp)."""
        state = c.get("state", "waiting")
        dish = c["dish_id"]
        raw = c.get("reserved")
        out = {"id": c["id"], "table_id": c["table_id"], "dish_id": dish, "state": state,
               "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
               "order_tick": c.get("order_tick", 0), "reserved": [], "_raw_reserved": raw}
        if state == "waiting":
            # reserved rỗng mà không khai order_status => món đã được nấu (clarify #21)
            default_status = "cooking" if raw in ({}, []) else "reserved"
            out["order_status"] = c.get("order_status", default_status)
        else:
            out["order_status"] = "served"
            out["eat_ticks_left"] = c.get("eat_ticks_left", self.eat_max)
            out["price"] = c["price"]
            out["tip"] = c["tip"]
        return out

    def _check_rules(self):
        """Mâu thuẫn cần biết kho thực (có thể từ --inventory / bàn giao của day) -> mã 2 (AC-P3-14, phần TV2)."""
        by_id = {it["id"]: it for it in self.stock}
        if len(by_id) != len(self.stock):
            raise BadInput("kho quán có id cá thể trùng")
        used = set()
        orders = sorted(self.customers, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in orders:
            raw = c.pop("_raw_reserved")
            if c["order_status"] != "reserved":
                if raw:
                    raise BadInput(f"customers.{c['id']}: đơn {c['order_status']} không còn giữ chỗ")
                continue
            if isinstance(raw, list):  # v1.2: mảng id phải trỏ cá thể chưa ươn, đủ công thức, không dùng chung
                need = dict(self.menu[c["dish_id"]]["recipe"])
                for iid in raw:
                    it = by_id.get(iid)
                    if it is None or iid in used:
                        raise BadInput(f"customers.{c['id']}: reserved {iid} không có trong kho hoặc đã bị đơn khác giữ")
                    if is_spoiled(it, self.spoiled_below):
                        raise BadInput(f"customers.{c['id']}: reserved {iid} đã ươn")
                    need[it["kind"]] = need.get(it["kind"], 0) - 1
                    used.add(iid)
                if any(n != 0 for n in need.values()):
                    raise BadInput(f"customers.{c['id']}: reserved không đúng công thức {c['dish_id']}")
                c["reserved"] = self._sorted_ids(raw)
            else:  # bỏ trống (hoặc map v1.1): tự cấp theo order_tick rồi id bàn, tươi nhất rồi id nhỏ
                ids = self._try_reserve(c["dish_id"], exclude=used)
                if ids is None:
                    raise BadInput(f"customers.{c['id']}: kho không đủ cá thể chưa ươn cho {c['dish_id']}")
                used.update(ids)
                c["reserved"] = ids
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
            "stock": [item_out(it) for it in sort_by_id(self.stock)],
            "hand": self.hand,
            "hand_base_price": self.hand_base_price,
            "shift_earned": self.shift_earned,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "order_id", "base_price",
                                              "cook_ticks_left", "ready_ticks")} for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [dict(c, reserved=list(c["reserved"])) for c in sort_by_id(self.customers)],
        }

    def step(self, inp):
        events = []
        self._served_now = set()  # khách vừa được giao bước này: đồng hồ ăn chạy từ bước sau
        self.ticks += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._decay_stock(events)
        self._tick_stoves(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._tick_eating(events)
        self._tick_customers(events)
        if self.time_left_ticks <= 0:
            self._close_shift(events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        else:
            self._spawn_customer(events)
        return events

    def stats(self) -> dict:
        """Cho DayResult/Summary (TV3): phục vụ, bỏ đi (hết kiên nhẫn), tiền ca, boa, đổi uy tín, món bán chạy (hòa: id)."""
        best = max(sorted(self._served_by_dish), key=lambda d: self._served_by_dish[d], default=None)
        return {"served": sum(self._served_by_dish.values()), "left": self._left, "money": self.shift_earned,
                "tips": self._tips, "reputation_delta": round(self.reputation - self._rep_start, 3), "best_dish": best}

    # --- kho cá thể, giữ chỗ -------------------------------------------------------------
    def _item(self, iid):
        return next(it for it in self.stock if it["id"] == iid)

    def _sorted_ids(self, ids):
        """Mảng id sắp theo kind rồi id (AC-P3-10)."""
        kinds = {it["id"]: it["kind"] for it in self.stock}
        return sorted(ids, key=lambda i: (kinds[i], id_key(i)))

    def _available(self, exclude=()):
        """Cá thể khả dụng: trong kho, chưa ươn, chưa bị đơn nào giữ."""
        held = set(exclude)
        for c in self.customers:
            held.update(c["reserved"])
        return [it for it in self.stock if it["id"] not in held and not is_spoiled(it, self.spoiled_below)]

    def _try_reserve(self, dish, exclude=()):
        """Mỗi loại trong công thức: n cá thể khả dụng tươi nhất, hòa theo id. Thiếu ⇒ None."""
        avail = self._available(exclude)
        chosen = []
        for kind in sorted(self.menu[dish]["recipe"]):
            n = self.menu[dish]["recipe"][kind]
            pool = sorted((it for it in avail if it["kind"] == kind), key=lambda it: (-it["fresh"], id_key(it["id"])))
            if len(pool) < n:
                return None
            chosen += [it["id"] for it in pool[:n]]
        return self._sorted_ids(chosen)

    def _decay_stock(self, events):
        """Hao tươi kho thô (kể cả hàng đang giữ), phát hết spoiled theo id, rồi xử lý các đơn có hàng vừa ươn:
        nhả cả phần giữ, thử giữ lại ĐÚNG MỘT LẦN theo order_tick rồi id bàn; thiếu ⇒ unfulfillable (AC-P3-11)."""
        crossed = decay(self.stock, self.decay_tick, self.spoiled_below)
        for it in crossed:
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        if not crossed:
            return
        bad = {it["id"] for it in crossed}
        hit = [c for c in self.customers if c["order_status"] == "reserved" and bad & set(c["reserved"])]
        hit.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in hit:
            c["reserved"] = []
        for c in hit:
            ids = self._try_reserve(c["dish_id"])
            if ids is None:
                c["order_status"] = "unfulfillable"  # khách vẫn chờ tới hết kiên nhẫn
            else:
                c["reserved"] = ids

    # --- tiện ích chung ------------------------------------------------------------------
    def _change_reputation(self, delta):
        """Kẹp [reputation_min, reputation_max], làm tròn 3 chữ số để tránh trôi số thực."""
        r = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta))
        self.reputation = round(r, 3)

    def _stove_of(self, customer_id):
        return next((s for s in self.stoves if s["order_id"] == customer_id), None)

    def _remove_customer(self, c):
        """Khách rời bàn: nhả giữ chỗ; món đang nấu/chín của khách thành món vô chủ (order_id = null)."""
        c["reserved"] = []
        s = self._stove_of(c["id"])
        if s is not None:
            s["order_id"] = None
        self.customers.remove(c)

    # --- khách ---------------------------------------------------------------------------
    def _pick_dish(self):
        """Chọn đều theo seed trong các món (kế hoạch/menu) giữ được cá thể; ứng viên sắp theo id món."""
        candidates = [d for d in self.dishes if self._try_reserve(d) is not None]
        if not candidates:
            return None
        return self.rng.get("customers").choice(candidates)

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
        table_id = free_tables[0]["id"]
        dish = self._pick_dish()
        if dish is None:
            events.append(("no_dish", {"table_id": table_id}))
            return
        c = {"id": self.ids.new("C"), "table_id": table_id, "dish_id": dish, "state": "waiting",
             "patience_ticks_left": self.patience_max, "order_tick": self.ticks, "order_status": "reserved",
             "reserved": self._try_reserve(dish)}
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
                self._left += 1
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
                s["ready_ticks"] += 1  # burn_s null trong lõi: chỉ đếm tuổi món chín (món chín không hao)

    def _customer(self, cid):
        return next((c for c in self.customers if c["id"] == cid), None) if cid else None

    def _oldest_reserved_order(self):
        orders = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        return orders[0] if orders else None

    def _cook(self, s, c, events):
        """Tiêu đúng các id đang giữ, chốt base_price = floor(giá × TB fresh / 100) (AC-P3-12)."""
        used = [self._item(i) for i in c["reserved"]]
        used_ids = set(c["reserved"])
        self.stock = [it for it in self.stock if it["id"] not in used_ids]
        mean = sum((it["fresh"] for it in used), Fraction(0)) / len(used)
        base_price = math.floor(Fraction(self.menu[c["dish_id"]]["price"]) * mean / 100)
        items = sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))
        c["reserved"] = []
        c["order_status"] = "cooking"
        s.update(state="cooking", dish=c["dish_id"], order_id=c["id"], ready_ticks=0, base_price=base_price,
                 cook_ticks_left=int(round(self.menu[c["dish_id"]]["cook_s"] * TICK)))
        events.append(("cook_started", {"stove_id": s["id"], "order_id": c["id"], "dish_id": c["dish_id"],
                                        "items": [item_out(it) for it in items], "base_price": base_price}))

    def _pick_up(self, s, events):
        self.hand = s["dish"]
        self.hand_base_price = s["base_price"]
        events.append(("dish_picked", {"stove_id": s["id"], "order_id": s["order_id"], "dish_id": s["dish"],
                                       "base_price": s["base_price"]}))
        s.update(state="idle", dish=None, order_id=None, base_price=None, cook_ticks_left=0, ready_ticks=0)

    # --- bàn, phục vụ, trả tiền ------------------------------------------------------------
    def _serve(self, c, events):
        price = self.hand_base_price if self.hand_base_price is not None else self.menu[c["dish_id"]]["price"]
        tip = 0
        if c["patience_ticks_left"] >= self.t["tip_min_patience_ratio"] * self.patience_max:
            tip = math.floor(Fraction(price) * self.tip_rate)
        # món giao có thể không phải món nấu cho chính đơn này: nhả giữ chỗ / gỡ đơn khỏi bếp
        c["reserved"] = []
        s = self._stove_of(c["id"])
        if s is not None:
            s["order_id"] = None
        self.hand = None
        self.hand_base_price = None
        self._served_by_dish[c["dish_id"]] = self._served_by_dish.get(c["dish_id"], 0) + 1
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_max, price=price, tip=tip)
        self._served_now.add(c["id"])
        events.append(("served", {"customer_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "price": price, "tip": tip}))

    def _tick_eating(self, events):
        for c in sort_by_id(self.customers):
            if c["state"] == "eating" and c["id"] not in self._served_now:
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] == 0:
                    self._pay(c, events)

    def _pay(self, c, events):
        amount = c["price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        self._tips += c["tip"]
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
            s.update(state="idle", dish=None, order_id=None, base_price=None, cook_ticks_left=0, ready_ticks=0)
        self.hand = None
        self.hand_base_price = None

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
