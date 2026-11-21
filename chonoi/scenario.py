"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P1, validate_items

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
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
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
        if not isinstance(h, list) or any(k not in KINDS_P1 for k in h):
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
                      "eat_ticks_left", "price", "tip"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}


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
        if state == "cooking":
            cook_max = int(round(menu[dish]["cook_s"] * 60))
            if not (1 <= s.get("cook_ticks_left", 0) <= cook_max):
                raise BadInput(f"stoves.{sid}: cook_ticks_left phải trong [1, {cook_max}]")
