"""Kiểm danh sách thành viên: chạy trong CI (bước của job `ci / test`) và chạy tay.

    python tools/check_team.py

Điều kiện của bảng thành viên (commit của người không có trong danh sách không được tính; CI chỉ cảnh báo, không chặn):
  - TEAM.md có bảng thành viên với 4-6 người, mỗi người có GitHub handle thật (không để mẫu/…),
    handle không trùng, có module chính.
  - `team_size` trong game.contract.json bằng đúng số thành viên.
  - Người mở PR (GITHUB_ACTOR) phải nằm trong danh sách.
Chỉ dùng thư viện chuẩn.
"""

import json
import os
import re
import sys

HANDLE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_team(text):
    """Trả về list dict {name, handle, module} từ bảng có cột 'GitHub handle'."""
    rows, cols = [], None
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            if cols is not None and rows:
                break
            continue
        cells = _cells(line)
        if cols is None:
            low = [c.lower() for c in cells]
            if any("github handle" in c for c in low):
                cols = {"name": 0, "handle": next(i for i, c in enumerate(low) if "github handle" in c),
                        "module": next((i for i, c in enumerate(low) if "module" in c), None)}
            continue
        if set("".join(cells)) <= set("-: "):
            continue  # dòng phân cách
        get = lambda i: cells[i] if i is not None and i < len(cells) else ""
        rows.append({"name": get(cols["name"]), "handle": get(cols["handle"]).lstrip("@").strip("` "),
                     "module": get(cols["module"])})
    return [r for r in rows if r["name"] or r["handle"] or r["module"]]


def validate(members, team_size, actor=None, event=None):
    errs = []
    if not members:
        return ["TEAM.md chưa có bảng thành viên (cột 'GitHub handle')"]
    handles = []
    for i, m in enumerate(members, 1):
        h = m["handle"]
        if not h or "…" in h or h.lower().startswith("handle") or not HANDLE.match(h):
            errs.append(f"thành viên #{i}: GitHub handle chưa điền hoặc không hợp lệ ({h!r})")
        else:
            handles.append(h.lower())
        if not m["name"] or "…" in m["name"]:
            errs.append(f"thành viên #{i}: thiếu tên")
        if not m["module"] or "…" in m["module"]:
            errs.append(f"thành viên #{i}: thiếu module chính")
    if len(set(handles)) != len(handles):
        errs.append("có GitHub handle bị trùng")
    if not (4 <= len(members) <= 6):
        errs.append(f"số thành viên phải từ 4 đến 6 (đang có {len(members)})")
    if team_size != len(members):
        errs.append(f"team_size trong game.contract.json ({team_size}) khác số thành viên ({len(members)})")
    if event == "pull_request" and actor and not actor.endswith("[bot]") and actor.lower() not in handles:
        errs.append(f"người mở PR '{actor}' không có trong danh sách thành viên (TEAM.md)")
    return errs


def main(root="."):
    try:
        with open(os.path.join(root, "TEAM.md"), encoding="utf-8") as f:
            members = parse_team(f.read())
        with open(os.path.join(root, "game.contract.json"), encoding="utf-8") as f:
            team_size = json.load(f).get("team_size")
    except (OSError, ValueError) as e:
        print(f"không đọc được TEAM.md / game.contract.json: {e}", file=sys.stderr)
        return 1
    errs = validate(members, team_size, os.environ.get("GITHUB_ACTOR"), os.environ.get("GITHUB_EVENT_NAME"))
    if errs:
        print("KIỂM TRA DANH SÁCH THÀNH VIÊN KHÔNG ĐẠT:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: {len(members)} thành viên: " + ", ".join(m["handle"] for m in members))
    return 0


if __name__ == "__main__":
    sys.exit(main())
