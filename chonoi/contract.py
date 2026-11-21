"""Đọc game.contract.json và kiểm dải hợp lệ của tuning P1 (PRD mục 13.2, Test Contract)."""

import json
import os

from .errors import BadInput

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    validate_tuning(c.get("tuning"))
    if c.get("contract_version") != "1.1" and "freshness" not in c["tuning"]:
        raise BadInput("contract từ v1.2 phải có tuning.freshness")
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or not {"ca_linh", "ca_loc", "ca_keo"} <= set(fy):
        raise BadInput("tuning.gather.fish_yield phải có ca_linh, ca_loc và ca_keo")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in ("bong_dien_dien", "bong_sung", "keo_neo"):
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải là bong_dien_dien, bong_sung hoặc keo_neo")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != {"bong_dien_dien", "bong_sung", "keo_neo"}:
        raise BadInput("tuning.gather.nodes phải có ít nhất một nút mỗi loại (3 loại)")
    fish = g.get("fish_initial")
    if isinstance(fish, bool) or not isinstance(fish, int) or fish < 0:
        raise BadInput("tuning.gather.fish_initial phải là số nguyên không âm")


def _validate_day_plan(t, menu):
    """Mỗi Ngày: ingredients == tổng recipe × suất của các món trong dishes."""
    plan = t.get("day_plan")
    if not isinstance(plan, list) or not plan:
        raise BadInput("tuning.day_plan phải là mảng không rỗng")
    seen = set()
    for e in plan:
        if not isinstance(e, dict) or set(e) != {"day", "dishes", "ingredients"}:
            raise BadInput("tuning.day_plan: mỗi Ngày cần đúng day, dishes, ingredients")
        day = e["day"]
        if isinstance(day, bool) or not isinstance(day, int) or day < 1 or day in seen:
            raise BadInput("tuning.day_plan: day phải là số nguyên dương duy nhất")
        seen.add(day)
        dishes, ing = e["dishes"], e["ingredients"]
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan.ngày {day}: dishes phải là object không rỗng")
        if not isinstance(ing, dict):
            raise BadInput(f"tuning.day_plan.ngày {day}: ingredients phải là object")
        want = {}
        for dish, n in dishes.items():
            if dish not in menu:
                raise BadInput(f"tuning.day_plan.ngày {day}: món lạ {dish}")
            if isinstance(n, bool) or not isinstance(n, int) or n < 1:
                raise BadInput(f"tuning.day_plan.ngày {day}: suất của {dish} phải là số nguyên dương")
            for kind, q in menu[dish]["recipe"].items():
                want[kind] = want.get(kind, 0) + q * n
        got = {}
        for kind, n in ing.items():
            if isinstance(n, bool) or not isinstance(n, int) or n < 1:
                raise BadInput(f"tuning.day_plan.ngày {day}: số lượng {kind} phải là số nguyên dương")
            got[kind] = n
        if got != want:
            raise BadInput(f"tuning.day_plan.ngày {day}: ingredients phải bằng tổng recipe × suất ({want})")


def _validate_shop(t):
    shop = t.get("shop")
    if not isinstance(shop, dict) or set(shop) != {"max_ticks", "upgrades"}:
        raise BadInput("tuning.shop phải có đúng max_ticks và upgrades")
    if isinstance(shop["max_ticks"], bool) or not isinstance(shop["max_ticks"], int) or shop["max_ticks"] < 1:
        raise BadInput("tuning.shop.max_ticks phải là số nguyên dương")
    ups = shop["upgrades"]
    if not isinstance(ups, dict) or set(ups) != {"oxygen", "hp"}:
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for key, stat in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        arr = ups[key]
        if not isinstance(arr, list) or not arr:
            raise BadInput(f"tuning.shop.upgrades.{key} phải là mảng không rỗng")
        levels = set()
        for u in arr:
            if not isinstance(u, dict) or set(u) != {"level", "price", stat}:
                raise BadInput(f"tuning.shop.upgrades.{key}: mỗi bậc cần level, price, {stat}")
            lvl, price, val = u["level"], u["price"], u[stat]
            if isinstance(lvl, bool) or not isinstance(lvl, int) or lvl < 1 or lvl in levels:
                raise BadInput(f"tuning.shop.upgrades.{key}: level phải là số nguyên dương duy nhất")
            levels.add(lvl)
            if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
                raise BadInput(f"tuning.shop.upgrades.{key}.level {lvl}: price phải là số nguyên dương")
            if isinstance(val, bool) or not isinstance(val, int) or val < 1:
                raise BadInput(f"tuning.shop.upgrades.{key}.level {lvl}: {stat} phải là số nguyên dương")


def _validate_freshness(t):
    f = t.get("freshness")
    if f is None:
        return
    if not isinstance(f, dict):
        raise BadInput("tuning.freshness phải là object")
    for key in ("initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"):
        if not _num(f.get(key)) or f[key] <= 0:
            raise BadInput(f"tuning.freshness.{key} phải là số dương")
    if not f["spoiled_below"] < f["initial"] <= 100:
        raise BadInput("tuning.freshness cần 0 < spoiled_below < initial <= 100")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    # TODO(nhóm): bổ sung kiểm các khóa còn lại nếu muốn chặt hơn (bếp/bàn, uy tín, ...).
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    _validate_day_plan(t, menu)
    _validate_shop(t)
    _validate_freshness(t)
