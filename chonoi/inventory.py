"""File kho (Contract G). v1.1: {"items": {kind: số nguyên >= 0}}. v1.2: {"items": [{"id", "kind", "fresh"}]}.

Đọc: từ chối sai schema / kind lạ / số âm; v1.2 từ chối thêm kho đếm, id trùng hoặc rỗng, fresh ngoài [0, 100] (mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế, byte-ổn-định. v1.2 sắp theo id, `fresh` là float đầy đủ (clarify #31).
"""

import json
import os
import tempfile

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
# v1.1 (TICKET-02): thêm cá kèo và kèo nèo. Sửa file khung vì kho/scenario phải nhận đủ 6 nguyên liệu.
KINDS = KINDS_P1 + ("ca_keo", "keo_neo")


def validate_items(items, kinds=KINDS):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def read_inventory(path: str, version="1.1", kinds=KINDS):
    """v1.1 trả map đếm; từ v1.2 trả list cá thể (`fresh` là Fraction)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if version == "1.1":
        return validate_items(data["items"], kinds)
    return validate_item_list(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, version="1.1"):
    """v1.1: `items` là map đếm. Từ v1.2: `items` là list cá thể chưa làm tròn."""
    if version == "1.1":
        payload = {k: items[k] for k in sorted(items) if items[k] > 0}
    else:
        payload = [{"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh"])} for it in sort_by_id(items)]
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --- v1.2 (TICKET-03): cá thể có độ tươi — hàm dùng chung theo spec phase-3/README.md 4.2 / ADR 0001 ----------
import math
from fractions import Fraction

FRESHNESS_DEFAULT = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}


def freshness(tuning) -> dict:
    """Khối tuning.freshness (v1.2); thiếu thì dùng giá trị chuẩn của đề."""
    return {**FRESHNESS_DEFAULT, **tuning.get("freshness", {})}


def to_fresh(x) -> Fraction:
    """Số JSON -> Fraction chính xác (đọc qua chuỗi để giữ đúng số thập phân trong file)."""
    if isinstance(x, Fraction):
        return x
    return Fraction(x) if isinstance(x, int) else Fraction(str(x))


def decay_per_tick(per_s, tick_hz=60) -> Fraction:
    return to_fresh(per_s) / tick_hz


def new_item(item_ids, kind, tuning) -> dict:
    return {"id": item_ids.new("I"), "kind": kind, "fresh": to_fresh(freshness(tuning)["initial"])}


def is_spoiled(item, spoiled_below) -> bool:
    return item["fresh"] < to_fresh(spoiled_below)


def decay(items, per_tick, spoiled_below) -> list:
    """Trừ `per_tick` (kẹp 0); trả các cá thể VỪA đi từ >= ngưỡng xuống < ngưỡng, sắp theo id."""
    below = to_fresh(spoiled_below)
    crossed = []
    for it in items:
        was_ok = it["fresh"] >= below
        it["fresh"] = max(Fraction(0), it["fresh"] - per_tick)
        if was_ok and it["fresh"] < below:
            crossed.append(it)
    return sort_by_id(crossed)


def item_out(item) -> dict:
    """Dạng JSONL (fresh làm tròn 3 chữ số khi xuất)."""
    return {"id": item["id"], "kind": item["kind"], "fresh": round(float(item["fresh"]), 3)}


def validate_item_list(raw, kinds=KINDS) -> list:
    """Kiểm mảng cá thể {id, kind, fresh}; trả list cá thể (fresh là Fraction). Sai -> BadInput (mã 2)."""
    if not isinstance(raw, list):
        raise BadInput("kho cá thể phải là mảng {id, kind, fresh}")
    out, seen = [], set()
    for i, it in enumerate(raw):
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"cá thể #{i} phải có đúng khóa id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"] or it["id"] in seen:
            raise BadInput(f"cá thể #{i}: id phải là chuỗi khác rỗng, duy nhất")
        if it["kind"] not in kinds:
            raise BadInput(f"cá thể {it['id']}: kind lạ {it['kind']!r}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(f) or not (0 <= f <= 100):
            raise BadInput(f"cá thể {it['id']}: fresh phải là số hữu hạn trong [0, 100]")
        seen.add(it["id"])
        out.append({"id": it["id"], "kind": it["kind"], "fresh": to_fresh(f)})
    return out


def items_from_counts(counts, item_ids, tuning) -> list:
    """Cầu nối khi manifest còn 1.1: kho đếm {kind: n} -> cá thể mới (fresh = initial), theo kind tăng dần."""
    return [new_item(item_ids, k, tuning) for k in sorted(counts) for _ in range(counts[k])]


def as_items(inv, item_ids, tuning) -> list:
    """Nhận kho dạng đếm (v1.1) hoặc mảng cá thể (v1.2) -> list cá thể; reserve id có sẵn để id mới nối tiếp."""
    if inv is None:
        return []
    if isinstance(inv, dict):
        return items_from_counts(inv, item_ids, tuning)
    items = validate_item_list(inv) if inv and not isinstance(inv[0].get("fresh"), Fraction) else \
        [dict(it) for it in inv]
    for it in items:
        item_ids.reserve(it["id"])
    return items
