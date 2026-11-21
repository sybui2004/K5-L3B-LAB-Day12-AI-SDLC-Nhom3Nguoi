"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  ĐÃ LÀM lát 1 + lát 2 (giả định chỗ PRD chưa rõ: docs/clarify.md #1-5; test: tests/test_gather_rules.py).
  lát 1: bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  lát 2: hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import IdAllocator, sort_by_id
from ..inventory import (as_items, decay, decay_per_tick, freshness, item_out,
                         new_item)
from .monsters import (apply_hit, drop_lifo, load_monsters, pick_hit,
                       snapshot_monsters, step_monsters)
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _r3(v):
    """Làm tròn 3 chữ số cho snapshot."""
    return round(float(v), 3)


def _load_hold(raw, item_ids, tuning) -> list:
    """Nạp giỏ scenario: mảng cá thể v1.2 hoặc mảng kind v1.1 (cầu nối clarify #34).

    Mảng kind v1.1 giữ NGUYÊN thứ tự nhặt: mỗi kind -> cá thể mới `fresh = initial`, id cấp theo
    thứ tự vào giỏ. Dạng dict đếm / mảng cá thể do `as_items` (adapter) xử lý.
    """
    if isinstance(raw, list) and raw and all(isinstance(k, str) for k in raw):
        items = []
        for k in raw:
            items.extend(as_items({k: 1}, item_ids, tuning))
        return items
    return as_items(raw, item_ids, tuning)


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, ctx=None, item_ids=None):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning  # khối tuning đầy đủ (freshness ở cấp tuning, không phải tuning.gather)
        self.rng = streams
        self.ids = ids
        # IdAllocator RIÊNG cho cá thể (họ I), sống suốt lượt; day truyền allocator chung (AC-P3-13).
        self.item_ids = item_ids if item_ids is not None else IdAllocator()
        fr = freshness(tuning)
        # tick_hz là SỐ NGUYÊN để Fraction / int giữ nguyên Fraction (ADR 0001 §2); TICK float chỉ dùng cho vận tốc.
        self.decay_per_tick = decay_per_tick(fr["gather_decay_per_s"], int(TICK))
        self.spoiled_below = fr["spoiled_below"]
        self.ctx = ctx or {}
        self.day = int(self.ctx.get("day", 1))  # gather độc lập = Ngày 1 (spec B1)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(float(self.ctx.get("oxygen_max_s", t["oxygen_max_s"])) * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp_max = int(self.ctx.get("hp_max", t["hp_max"]))
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = _load_hold(scenario.get("hold"), self.item_ids, tuning)  # cá thể, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0  # bước gameplay trong pha (lịch sinh cá đếm theo đây)
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.fish_active = bool(scenario.get("random_fish", True))
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        # Phase 2: đàn fixture trong scenario thay đàn đầu ca; random_fish=false tắt bơi/sinh.
        self.fish = []
        if "fish" in scenario:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0)),
                          "age_ticks": int(f.get("age_ticks", 0))} for f in scenario["fish"]]
            for e in self.fish:
                ids.reserve(e["id"])
        elif self.fish_active:
            for _ in range(int(t["fish_initial"])):
                self._spawn_fish(None)
        for e in self.nodes:
            ids.reserve(e["id"])
        # Lát 2: quái của Ngày (gather.monsters[] trong scenario THAY danh sách mặc định).
        self.monsters = load_monsters(t, self.day, scenario.get("monsters"))
        for m in self.monsters:
            ids.reserve(m["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        """Bàn giao: mảng cá thể (item_out) sắp theo id (spec gather.md mục 4)."""
        return [item_out(i) for i in sort_by_id(self.hold)]

    def hold_counts(self) -> dict:
        """Đếm theo loại cho HUD/kế hoạch và cầu nối file kho khi manifest còn 1.1."""
        counts = {}
        for it in self.hold:
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        return {k: counts[k] for k in sorted(counts)}

    def snapshot(self) -> dict:
        return {
            "player": {"pos": [_r3(c) for c in self.pos], "vel": [_r3(c) for c in self.vel],
                       "heading_deg": _r3(self.heading),
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [item_out(i) for i in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": [_r3(c) for c in n["pos"]], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": [_r3(c) for c in f["pos"]], "kind": f["kind"],
                      "heading_deg": _r3(f["heading_deg"]), "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": snapshot_monsters(self.monsters),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        self.phase_tick += 1
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 1b. hao tươi hàng ĐÃ CÓ trước bước này (hàng nhặt trong bước bắt đầu hao từ bước sau, AC-P3-05);
        #     mỗi cá thể vừa qua ngưỡng phát spoiled đúng một lần, theo id (AC-P3-06).
        for it in decay(self.hold, self.decay_per_tick, self.spoiled_below):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))
        # 2. bơi + chặn mép; so phân vùng đầu/cuối bước -> dive / surface
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        # 2b. oxy theo d CUỐI bước, ngạt, Máu
        if self._oxygen(now_surface, events):
            return events
        # 3. Cập nhật quái theo id và xét tối đa một hit.
        recoiling = step_monsters(self.monsters, self.pos, self.t, TICK)
        hit = pick_hit(self.monsters, self.pos, self.invuln_ticks, self.t, recoiling)
        if hit is not None:
            basket = list(self.hold)  # giỏ lúc chạm (dùng cho lost của faint nếu ngất)
            self.hp = max(0, self.hp - 1)
            self.hold, lost = drop_lifo(basket, len(basket), self.t["monsters"]["loss_ratio"])
            self.invuln_ticks = int(self.t["monsters"]["invuln_ticks"])
            apply_hit(hit, self.pos, self.t)
            events.append(("monster_hit", {"monster_id": hit["id"], "hp": self.hp,
                                           "lost": [item_out(i) for i in lost], "pos": list(self.pos)}))
            if self.hp <= 0:
                # Ngất do chạm: faint {cause:"monster"} rồi gather_end(fainted) cùng tick, giỏ rỗng.
                # Mất TẤT CẢ theo LIFO (mới nhất trước), gồm cả phần vừa rơi vì chạm (AC-P3-07).
                self.hold = []
                events.append(("faint", {"pos": list(self.pos),
                                         "lost": [item_out(i) for i in reversed(basket)], "hp": 0,
                                         "cause": "monster"}))
                self._finish("fainted", events)
                return events
        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._harvest(events)
        # 5. bắt cá theo vị trí cá TRƯỚC khi bơi ở bước này
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            self._catch(events)
        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 7. cá bơi -> sinh cá theo lịch
        if self.fish_active:
            self._swim_fish()
            self._spawn_scheduled(events)
        return events

    # --- luật ------------------------------------------------------------------
    def _oxygen(self, at_surface, events) -> bool:
        """Oxy / ngạt / Máu. Trả True nếu vừa ngất (buổi đã kết thúc)."""
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"pos": list(self.pos)}))
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return False
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self.t["choke_interval_ticks"]:
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        # Ngất: bỏ TOÀN BỘ giỏ theo LIFO (mới nhất trước), rồi gather_end(fainted) với kho rỗng.
        lost = [item_out(i) for i in reversed(self.hold)]
        self.hold = []
        events.append(("faint", {"pos": list(self.pos), "lost": lost, "hp": 0}))
        self._finish("fainted", events)
        return True

    def _room(self) -> int:
        return self.t["hold_capacity"] - len(self.hold)

    def _nearest(self, items, radius):
        """Gần nhất trong bán kính; bằng khoảng cách thì id nhỏ hơn (sort_by_id ổn định)."""
        best, best_d = None, None
        for e in sort_by_id(items):
            d = math.dist(self.pos, e["pos"])
            if d <= radius and (best is None or d < best_d):
                best, best_d = e, d
        return best

    def _harvest(self, events):
        ready = [n for n in self.nodes if n["regrow_ticks"] == 0]
        node = self._nearest(ready, self.t["interact_radius"])
        if node is None:
            return
        n = min(self.t["node_yield"], self._room())
        if n <= 0:
            events.append(("hold_full", {"source": node["id"], "kind": node["kind"]}))
            return
        # Mỗi con hái được là một cá thể mới fresh = initial, id cấp theo thứ tự vào giỏ (AC-P3-05).
        self.hold.extend(new_item(self.item_ids, node["kind"], self.tuning) for _ in range(n))
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "count": n}))
        if n < self.t["node_yield"]:
            events.append(("hold_full", {"source": node["id"], "kind": node["kind"]}))

    def _catch(self, events):
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        want = self.t["fish_yield"][fish["kind"]]
        if self._room() < want:
            events.append(("hold_full", {"source": fish["id"], "kind": fish["kind"]}))
            return
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        # Bắt đàn n con = n cá thể mới (new_item n lần), id liên tiếp theo thứ tự vào giỏ (AC-P3-05).
        self.hold.extend(new_item(self.item_ids, fish["kind"], self.tuning) for _ in range(want))
        self.fish = [f for f in self.fish if f["id"] != fish["id"]]
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "count": want}))

    def _swim_fish(self):
        """Cá bơi mỗi bước; đổi hướng theo lịch TRƯỚC khi di chuyển, phản xạ ở mép."""
        rng = self.rng.get("fish")
        turn = int(self.t["fish_turn_ticks"])
        dist = self.t["fish_speed"] / TICK
        xlo, xhi = self.t["fish_x"]
        for f in sort_by_id(self.fish):
            if turn > 0 and (f["age_ticks"] + 1) % turn == 0:
                f["heading_deg"] = rng.random() * 360.0
            th = math.radians(f["heading_deg"])
            cx, cy = math.cos(th), math.sin(th)
            x = f["pos"][0] + cx * dist
            d = f["pos"][1] + cy * dist
            dlo, dhi = self.t["fish_depths"][f["kind"]]
            while x < xlo or x > xhi:
                x = 2 * xlo - x if x < xlo else 2 * xhi - x
                cx = -cx
            while d < dlo or d > dhi:
                d = 2 * dlo - d if d < dlo else 2 * dhi - d
                cy = -cy
            f["pos"] = [x, d]
            f["heading_deg"] = math.degrees(math.atan2(cy, cx)) % 360
            f["age_ticks"] += 1

    def _valid_spawn_points(self):
        """Điểm sinh cách mọi đàn đang sống > fish_spawn_clearance, thứ tự tất định."""
        clearance = self.t["fish_spawn_clearance"]
        live = [f["pos"] for f in self.fish]
        pts = []
        for kind in sorted(self.t["fish_spawn_depths"]):
            for x in self.t["fish_spawn_x"]:
                for d in self.t["fish_spawn_depths"][kind]:
                    pos = (float(x), float(d))
                    if all(math.dist(pos, p) > clearance for p in live):
                        pts.append((kind, pos))
        return pts

    def _spawn_fish(self, events):
        """Chọn loài theo trọng số đã chuẩn hóa rồi đều một điểm hợp lệ; None nếu hết điểm."""
        pts = self._valid_spawn_points()
        if not pts:
            return None
        rng = self.rng.get("fish")
        kinds = sorted({k for k, _ in pts})
        weights = [self.t["fish_weights"][k] for k in kinds]
        total = sum(weights)
        if total <= 0:
            kind = kinds[rng.randrange(len(kinds))]
        else:
            r = rng.random() * total
            acc, kind = 0.0, kinds[-1]
            for k, w in zip(kinds, weights):
                acc += w
                if r < acc:
                    kind = k
                    break
        cand = [p for k, p in pts if k == kind]
        pos = cand[rng.randrange(len(cand))]
        f = {"id": self.ids.new("F"), "kind": kind, "pos": [pos[0], pos[1]],
             "heading_deg": rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        if events is not None:
            events.append(("fish_spawned", {"id": f["id"], "kind": kind, "pos": list(f["pos"])}))
        return f

    def _spawn_scheduled(self, events):
        """Sinh theo phase_tick = fish_spawn_ticks·k, sau khi cá bơi; trần fish_max."""
        period = int(self.t["fish_spawn_ticks"])
        if period <= 0 or self.phase_tick % period != 0:
            return
        if len(self.fish) >= self.t["fish_max"]:
            return
        self._spawn_fish(events)

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
