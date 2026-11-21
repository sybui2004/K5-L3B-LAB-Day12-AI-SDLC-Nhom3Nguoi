"""Kế hoạch Ngày (TICKET-02 mục 2, AC-P2-14). Chủ: TV2. Hàm thuần, dùng ở contract.py, scenario.py, day.py."""


def plan_ingredients(dishes: dict, menu: dict) -> dict:
    """Tổng nguyên liệu cần = Σ công thức × số suất; khóa sắp theo id nguyên liệu."""
    out = {}
    for dish, n in dishes.items():
        for k, m in menu[dish]["recipe"].items():
            out[k] = out.get(k, 0) + m * n
    return {k: out[k] for k in sorted(out)}
