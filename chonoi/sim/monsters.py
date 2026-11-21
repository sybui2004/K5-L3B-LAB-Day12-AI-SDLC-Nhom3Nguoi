"""Cá Sấu Năm Chèo (`monsters`) — bố trí, tuần tra/đuổi/lùi, chạm, rơi LIFO, snapshot.

Tách khỏi `gather.py` để diff gọn (spec gather.md mục B1–B5). Mọi số liệu đọc từ
`g_tuning["monsters"]` và `g_tuning["bounds"]`; không giữ trạng thái riêng và không phụ thuộc
`GatherSim`. Các hàm nhận danh sách quái (dict) và cập nhật TẠI CHỖ.

Một quái: `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}`.
`pos`, `waypoints`, `recoil_dir` là `[x, d]` như gather (d dương = sâu hơn).
"""

import math
from typing import Optional

from ..ids import sort_by_id


def _species(monster, g_tuning) -> dict:
    return g_tuning["monsters"]["species"][monster["kind"]]


def _floats(pair) -> list:
    return [float(c) for c in pair]


def _recoil_dir_of(monster) -> list:
    return monster.get("recoil_dir") or [0.0, 0.0]


def _normalise(raw) -> dict:
    """Chuẩn hoá một quái scenario (không giữ tham chiếu vào scenario)."""
    wps = [_floats(w) for w in (raw.get("waypoints") or [])]
    if "pos" in raw:
        pos = _floats(raw["pos"])
    elif wps:
        pos = list(wps[0])
    else:
        pos = [0.0, 0.0]
    if not wps:
        wps = [list(pos)]
    return {
        "id": raw["id"],
        "kind": raw["kind"],
        "pos": pos,
        "waypoints": wps,
        "target_idx": int(raw.get("target_idx", 1)),
        "state": raw.get("state", "patrol"),
        "state_ticks_left": int(raw.get("state_ticks_left", 0)),
        "recoil_dir": _floats(_recoil_dir_of(raw)),
    }


def load_monsters(g_tuning, day, scenario_monsters=None) -> list:
    """B1: quái của Ngày `day` (spawns có from_day ≤ day) hoặc danh sách scenario thay thế.

    Mặc định: pos = waypoint 0, target_idx = 1, state = "patrol".
    Scenario: nhận thêm target_idx / state_ticks_left / recoil_dir (mặc định 1 / 0 / [0, 0]).
    """
    if scenario_monsters is not None:
        return sort_by_id([_normalise(m) for m in scenario_monsters])
    out = []
    for s in g_tuning["monsters"].get("spawns", []):
        if s.get("from_day", 1) > day:
            continue
        wps = [_floats(w) for w in (s.get("waypoints") or [])]
        if not wps:
            wps = [_floats(s["pos"])]
        out.append({
            "id": s["id"],
            "kind": s["kind"],
            "pos": list(wps[0]),
            "waypoints": wps,
            "target_idx": 1,
            "state": "patrol",
            "state_ticks_left": 0,
            "recoil_dir": [0.0, 0.0],
        })
    return sort_by_id(out)


def _toward(pos, target, dist):
    """Đi `dist` m về phía target; trả (pos mới, đã tới nơi?)."""
    dx = target[0] - pos[0]
    dd = target[1] - pos[1]
    gap = math.hypot(dx, dd)
    if gap <= dist:
        return [float(target[0]), float(target[1])], True
    return [pos[0] + dx / gap * dist, pos[1] + dd / gap * dist], False


def _clamp(monster, g_tuning, species) -> None:
    """Sau mỗi lần di chuyển: chặn trong biên map và dải độ sâu của loài."""
    b = g_tuning["bounds"]
    depths = species["depths"]
    monster["pos"][0] = min(max(monster["pos"][0], b["x"][0]), b["x"][1])
    lo = max(b["d"][0], depths[0])
    hi = min(b["d"][1], depths[1])
    monster["pos"][1] = min(max(monster["pos"][1], lo), hi)


def _detects(monster, player_pos, species) -> bool:
    """Người chơi d ≥ depths[0] và cách ≤ detect_radius."""
    if player_pos[1] < species["depths"][0]:
        return False
    return math.dist(monster["pos"], player_pos) <= species["detect_radius"]


def _loses(monster, player_pos, species) -> bool:
    """Cách > exit_radius hoặc người chơi d < depths[0]."""
    if player_pos[1] < species["depths"][0]:
        return True
    return math.dist(monster["pos"], player_pos) > species["exit_radius"]


def _patrol_step(monster, species, tick_hz) -> None:
    wps = monster.get("waypoints") or []
    if not wps:
        return
    idx = int(monster.get("target_idx", 0)) % len(wps)
    monster["pos"], reached = _toward(monster["pos"], wps[idx],
                                      species["patrol_speed"] / tick_hz)
    if reached:
        # Đổi đích cho bước sau; bước này vẫn dừng đúng waypoint.
        monster["target_idx"] = (idx + 1) % len(wps)


def _recoil_step(monster, species) -> None:
    ticks = species["recoil_ticks"]
    dist = species["recoil_dist"] / ticks if ticks else 0.0
    d = _recoil_dir_of(monster)
    norm = math.hypot(d[0], d[1])
    if norm > 0 and dist:
        monster["pos"][0] += d[0] / norm * dist
        monster["pos"][1] += d[1] / norm * dist


def step_monsters(monsters, player_pos, g_tuning, tick_hz) -> None:
    """B2: một bước di chuyển cho từng quái, theo thứ tự id, rồi chặn biên.

    patrol: đi tới waypoint đích; chase: bơi về phía người chơi; recoil: lùi theo
    `recoil_dir`. Chuyển trạng thái xét SAU khi di chuyển (dùng vị trí cuối bước).
    """
    for m in sort_by_id(monsters):
        species = _species(m, g_tuning)
        state = m.get("state", "patrol")
        if state == "patrol":
            _patrol_step(m, species, tick_hz)
            _clamp(m, g_tuning, species)
            if _detects(m, player_pos, species):
                m["state"] = "chase"
                m["state_ticks_left"] = 0
        elif state == "chase":
            m["pos"], _ = _toward(m["pos"], player_pos, species["chase_speed"] / tick_hz)
            _clamp(m, g_tuning, species)
            if _loses(m, player_pos, species):
                m["state"] = "patrol"
                m["state_ticks_left"] = 0
        elif state == "recoil":
            left = int(m.get("state_ticks_left", 0))
            if left > 0:
                _recoil_step(m, species)
                _clamp(m, g_tuning, species)
                left -= 1
            m["state_ticks_left"] = left
            if left <= 0:
                # Phát hiện / chạm lại được từ bước kế.
                m["state"] = "patrol"
        else:
            # stunned (hoặc trạng thái khác): đứng yên, đếm ngược rồi về patrol.
            left = max(0, int(m.get("state_ticks_left", 0)) - 1)
            m["state_ticks_left"] = left
            if left == 0:
                m["state"] = "patrol"


def pick_hit(monsters, player_pos, invuln_ticks, g_tuning) -> Optional[dict]:
    """B3: chọn tối đa MỘT quái chạm người chơi — gần nhất, hòa theo id.

    Ứng viên: không ở recoil, người chơi d ≥ depths[0] của loài, cách ≤ hit_radius.
    Trong bất tử (`invuln_ticks != 0`) không có hit.
    """
    if invuln_ticks:
        return None
    best, best_d = None, None
    for m in sort_by_id(monsters):
        if m.get("state") == "recoil":
            continue
        species = _species(m, g_tuning)
        if player_pos[1] < species["depths"][0]:
            continue
        d = math.dist(m["pos"], player_pos)
        if d <= species["hit_radius"] and (best is None or d < best_d):
            best, best_d = m, d
    return best


def apply_hit(monster, player_pos, g_tuning) -> None:
    """B3: quái gây hit vào recoil `recoil_ticks` bước, tính từ bước sau.

    `recoil_dir` = vector đơn vị từ người chơi tới quái lúc chạm; trùng tâm ⇒ [1, 0].
    Máu / giỏ / bất tử do phía gather xử lý.
    """
    species = _species(monster, g_tuning)
    dx = monster["pos"][0] - player_pos[0]
    dd = monster["pos"][1] - player_pos[1]
    norm = math.hypot(dx, dd)
    monster["recoil_dir"] = [1.0, 0.0] if norm == 0 else [dx / norm, dd / norm]
    monster["state"] = "recoil"
    monster["state_ticks_left"] = int(species["recoil_ticks"])


def drop_lifo(hold_list, count_carried, loss_ratio) -> tuple:
    """Rơi `floor(count_carried × loss_ratio)` món CUỐI (nhặt sau mất trước).

    Trả `(kept, lost)` là hai danh sách mới; không sửa `hold_list`.
    """
    n = int(math.floor(count_carried * loss_ratio))
    if n <= 0:
        return list(hold_list), []
    return list(hold_list[:-n]), list(hold_list[-n:])


def _round3(v) -> float:
    r = round(float(v), 3)
    return 0.0 if r == 0 else r


def snapshot_monsters(monsters) -> list:
    """B5: snapshot theo id, số làm tròn 3 chữ số."""
    return [{
        "id": m["id"],
        "kind": m["kind"],
        "pos": [_round3(c) for c in m["pos"]],
        "state": m["state"],
        "target_idx": m["target_idx"],
        "state_ticks_left": m["state_ticks_left"],
        "recoil_dir": [_round3(c) for c in _recoil_dir_of(m)],
    } for m in sort_by_id(monsters)]
