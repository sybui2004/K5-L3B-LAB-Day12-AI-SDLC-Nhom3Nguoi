"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        return _load_day(data, tuning)
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _check_block(data, mode, tuning)


def _check_block(data, mode, tuning):
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _load_day(data, tuning):
    """Mode day (v1.1, TICKET-02 4.3): khối gather/quan là mẫu khởi tạo mỗi Ngày, khối day là trạng thái xuyên Ngày.
    Trả {"gather": ..., "quan": ..., "day": ...}."""
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario day chỉ được có khối 'gather', 'quan', 'day'")
    out = {}
    if "gather" in data:
        out["gather"] = _check_block(data, "gather", tuning)
    if "quan" in data:
        q = data["quan"]
        if isinstance(q, dict) and ({"stock", "reputation"} & set(q)):
            raise BadInput("chạy day cấm quan.stock và quan.reputation (dùng gather.hold / day.reputation)")
        out["quan"] = _check_block(data, "quan", tuning)
    d = data.get("day", {})
    if not isinstance(d, dict):
        raise BadInput("khối day phải là object")
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong day: {sorted(extra)}")
    for key in ("money", "earned"):
        if key in d:
            _nonneg_int(f"day.{key}", d[key])
    money, earned = d.get("money", 0), d.get("earned", 0)
    if money > 0 and "earned" not in d:
        raise BadInput("có tiền đầu kỳ thì phải khai cả money và earned")
    if money > earned:
        raise BadInput("cần 0 <= money <= earned")
    q = tuning["quan"]
    if "reputation" in d and (not _num(d["reputation"]) or not (q["reputation_min"] <= d["reputation"] <= q["reputation_max"])):
        raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    ups = d.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    table = tuning["shop"]["upgrades"]
    for k, lv in ups.items():
        if k not in table:
            raise BadInput(f"day.upgrades: nâng cấp lạ {k}")
        if isinstance(lv, bool) or not isinstance(lv, int) or not (0 <= lv <= len(table[k])):
            raise BadInput(f"day.upgrades.{k} phải là cấp trong [0, {len(table[k])}]")
    plans = d.get("day_plan", [])
    if not isinstance(plans, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for p in plans:
        if not isinstance(p, dict) or set(p) - {"day", "dishes", "ingredients"} or "dishes" not in p:
            raise BadInput("day.day_plan: mỗi mục là {day, dishes[, ingredients]}")
        n = p.get("day")
        if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= 5) or n in seen:
            raise BadInput("day.day_plan: day phải là số Ngày 1..5, không trùng")
        seen.add(n)
        dishes = p["dishes"]
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day.day_plan[{n}].dishes phải là object khác rỗng")
        for dish, cnt in dishes.items():
            if dish not in tuning["menu"]:
                raise BadInput(f"day.day_plan[{n}]: món lạ {dish}")
            if isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                raise BadInput(f"day.day_plan[{n}].dishes.{dish} phải là số nguyên dương")
        if "ingredients" in p:
            want = {}
            for dish, cnt in dishes.items():
                for k, m in tuning["menu"][dish]["recipe"].items():
                    want[k] = want.get(k, 0) + m * cnt
            if p["ingredients"] != want:
                raise BadInput(f"day.day_plan[{n}].ingredients không khớp tổng công thức × số suất")
    out["day"] = d
    return out


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    _validate_quan_rules(b, tuning)


QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "state", "patience_ticks_left", "reserved",
                      "eat_ticks_left", "price", "tip", "order_tick", "order_status"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "order_id", "cook_ticks_left", "ready_ticks"}
ORDER_STATUSES = ("reserved", "cooking", "ready", "served")


def _validate_quan_rules(b, tuning):
    """Mâu thuẫn mức luật của quan (TV2, spec quan.md mục A4). Tổng giữ chỗ > kho kiểm ở QuanSim
    (vì kho có thể đến từ --inventory)."""
    q, menu = tuning["quan"], tuning["menu"]
    patience_max = int(round(q["patience_s"] * 60))
    eat_max = int(round(q["eat_s"] * 60))
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải là số trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "hand" in b and b["hand"] is not None and b["hand"] not in menu:
        raise BadInput("hand phải là null hoặc id món trong menu")
    for c in b.get("customers", []):
        cid = c["id"]
        extra = set(c) - QUAN_CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        dish = c.get("dish_id")
        if dish not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món trong menu")
        state = c.get("state", "waiting")
        if state not in ("waiting", "eating"):
            raise BadInput(f"customers.{cid}: state phải là waiting hoặc eating")
        if "patience_ticks_left" in c:
            _nonneg_int(f"customers.{cid}.patience_ticks_left", c["patience_ticks_left"])
            lo = 1 if state == "waiting" else 0
            if not (lo <= c["patience_ticks_left"] <= patience_max):
                raise BadInput(f"customers.{cid}: patience_ticks_left phải trong [{lo}, {patience_max}]")
        if "reserved" in c:
            res = c["reserved"]
            if not isinstance(res, dict):
                raise BadInput(f"customers.{cid}: reserved phải là object")
            res = validate_items(res)
            if state == "eating" and res:
                raise BadInput(f"customers.{cid}: khách eating không còn giữ chỗ")
            if state == "waiting" and res and res != menu[dish]["recipe"]:
                raise BadInput(f"customers.{cid}: reserved phải đúng recipe của {dish} (hoặc rỗng nếu đã nấu)")
        status = c.get("order_status")
        if status is not None:
            if status not in ORDER_STATUSES:
                raise BadInput(f"customers.{cid}: order_status phải là một trong {ORDER_STATUSES}")
            if (state == "eating") != (status == "served"):
                raise BadInput(f"customers.{cid}: order_status served khi và chỉ khi state eating")
            res = c.get("reserved")
            if status == "reserved" and res is not None and validate_items(res) != menu[dish]["recipe"]:
                raise BadInput(f"customers.{cid}: đơn reserved phải giữ đúng recipe")
            if status in ("cooking", "ready") and res:
                raise BadInput(f"customers.{cid}: đơn {status} đã trừ kho, reserved phải rỗng")
        if "order_tick" in c:
            _nonneg_int(f"customers.{cid}.order_tick", c["order_tick"])
        if state == "eating":
            for key in ("price", "tip"):
                if key not in c:
                    raise BadInput(f"customers.{cid}: khách eating thiếu {key}")
                _nonneg_int(f"customers.{cid}.{key}", c[key])
            if "eat_ticks_left" in c:
                _nonneg_int(f"customers.{cid}.eat_ticks_left", c["eat_ticks_left"])
                if not (1 <= c["eat_ticks_left"] <= eat_max):
                    raise BadInput(f"customers.{cid}: eat_ticks_left phải trong [1, {eat_max}]")
        else:
            for key in ("price", "tip", "eat_ticks_left"):
                if key in c:
                    raise BadInput(f"customers.{cid}: khách waiting không có {key}")
    for s in b.get("stoves", []):
        sid = s["id"]
        extra = set(s) - QUAN_STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{sid}: trường lạ/chưa hỗ trợ {sorted(extra)}")
        state = s.get("state", "idle")
        if state not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{sid}: state phải là idle, cooking hoặc ready")
        dish = s.get("dish")
        if state == "idle" and dish is not None:
            raise BadInput(f"stoves.{sid}: bếp idle không có món")
        if state != "idle" and dish not in menu:
            raise BadInput(f"stoves.{sid}: bếp {state} phải có dish trong menu")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in s:
                _nonneg_int(f"stoves.{sid}.{key}", s[key])
        if "order_id" in s and s["order_id"] is not None and (state == "idle" or not isinstance(s["order_id"], str)):
            raise BadInput(f"stoves.{sid}: order_id chỉ là id khách khi bếp đang nấu/chín")
        if state == "cooking":
            cook_max = int(round(menu[dish]["cook_s"] * 60))
            if not (1 <= s.get("cook_ticks_left", 0) <= cook_max):
                raise BadInput(f"stoves.{sid}: cook_ticks_left phải trong [1, {cook_max}]")
