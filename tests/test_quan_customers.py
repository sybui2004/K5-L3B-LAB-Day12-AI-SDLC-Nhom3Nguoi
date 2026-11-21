"""Test hộp đen quan lát 3 — khách (TV2). AC-Q-01..06 trong docs/spec/phase-1/quan.md mục A.

Chạy: PYTHONPATH=tests:. python -m unittest tests.test_quan_customers -v
Số liệu đọc từ game.contract.json (không hard-code).
"""

import json
import os
import unittest

from helpers import ROOT, Workdir, reserved_counts, stock_counts, events, read_jsonl, run_headless, snapshots, write_json
from helpers import hold_items, stock_counts, stock_items


def tuning():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]


Q = tuning()["quan"]
MENU = tuning()["menu"]
FIRST = Q["first_customer_tick"]
INTERVAL = int(round(Q["customer_interval_s"] * 60))
PATIENCE = int(round(Q["patience_s"] * 60))


def run_quan(w, block, ticks, seed=1, name="o", extra=()):
    sc = write_json(w.path(f"{name}.json"), {"quan": block})
    code, err = run_headless("--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
                             "--out", w.path(f"{name}.jsonl"), *extra)
    return code, err, (read_jsonl(w.path(f"{name}.jsonl")) if code == 0 else None)


class Arrival(unittest.TestCase):
    def test_ac_q_01_first_customer_at_first_customer_tick(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 5})}, FIRST + 1)
            self.assertEqual(code, 0, err)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], FIRST)
            d = arr[0]["data"]
            self.assertEqual(d["table_id"], "T1")
            self.assertEqual(d["dish_id"], "ca_loc_nuong_trui")
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["tables"][0]["customer_id"], d["customer_id"])
            c = snap["customers"][0]
            self.assertEqual(c["state"], "waiting")
            self.assertEqual(c["patience_ticks_left"], PATIENCE - 1)  # đến ở tick FIRST, đã qua 1 bước

    def test_no_customer_before_first_tick(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 5})}, FIRST - 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_ac_q_02_empty_stock_no_dish(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({})}, FIRST + 1)
            self.assertEqual(code, 0, err)
            nd = events(rows, "no_dish")
            self.assertEqual([e["tick"] for e in nd], [FIRST])
            self.assertEqual(events(rows, "customer_arrived"), [])
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["customers"], [])
            self.assertTrue(all(t["customer_id"] is None for t in snap["tables"]))

    def test_random_customers_false_disables_schedule(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 5}), "random_customers": False}, FIRST + 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])

    def test_full_tables_skip_turn(self):
        """Clarify #9: hết bàn trống -> bỏ lượt, không phát sự kiện. (v1.1: 4 bàn, dựng sẵn khách ở cả 4 bàn.)"""
        full = [{"id": f"C{i}", "table_id": tb["id"], "dish_id": "ca_loc_nuong_trui", "reserved": []}
                for i, tb in enumerate(Q["tables"], 1)]
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 5}), "customers": full}, FIRST + 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])

    def test_customers_fill_tables_in_id_order(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 9})}, FIRST + 2 * INTERVAL)
            self.assertEqual(code, 0, err)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [FIRST, FIRST + INTERVAL, FIRST + 2 * INTERVAL])
            self.assertEqual([e["data"]["table_id"] for e in arr], ["T1", "T2", "T3"])


class Reservation(unittest.TestCase):
    def test_ac_q_03_dish_is_cookable_and_reserves_recipe(self):
        # chỉ đủ cho gỏi bông súng; đủ nhiều seed để chắc chắn không chọn món không nấu được
        stock = {"bong_sung": 2, "ca_linh": 2, "bong_dien_dien": 1}
        with Workdir() as w:
            for seed in range(1, 9):
                code, err, rows = run_quan(w, {"stock": stock_items(stock)}, FIRST, seed=seed)
                self.assertEqual(code, 0, err)
                snap = snapshots(rows)[-1]
                c = snap["customers"][0]
                self.assertEqual(c["dish_id"], "goi_bong_sung", seed)
                self.assertEqual(reserved_counts(snap, c), MENU["goi_bong_sung"]["recipe"])  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể

    def test_reserved_ingredients_are_not_offered_again(self):
        """Khách dựng sẵn giữ chỗ hết cá lóc -> khách mới ở bàn trống kế tiếp không chọn được món nào (no_dish)."""
        block = {"stock": stock_items({"ca_loc": 1}), "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": PATIENCE}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, block, FIRST)
            self.assertEqual(code, 0, err)
            s0 = snapshots(rows)[0]
            self.assertEqual(reserved_counts(s0, s0["customers"][0]), {"ca_loc": 1})  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual([e["data"] for e in events(rows, "no_dish")], [{"table_id": "T2"}])

    def test_new_customer_id_follows_scenario_ids(self):
        block = {"stock": stock_items({"ca_loc": 1}), "customers": [
            {"id": "C7", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 3}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, block, FIRST)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived")[0]["data"]["customer_id"], "C8")


class Patience(unittest.TestCase):
    def test_ac_q_04_customer_leaves_reputation_drops_reservation_released(self):
        block = {"stock": stock_items({"ca_loc": 1}), "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 5}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, block, FIRST)
            self.assertEqual(code, 0, err)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 5)
            self.assertEqual(left[0]["data"], {"customer_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                            "reason": "patience"})
            snap = snapshots(rows)[-1]
            self.assertAlmostEqual(snap["reputation"], Q["reputation_initial"] + Q["left_reputation_delta"])
            # nguyên liệu được nhả -> khách mới ở tick FIRST lại chọn được cá lóc
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["data"]["dish_id"], "ca_loc_nuong_trui")
            self.assertEqual(stock_counts(snap["stock"]), {"ca_loc": 1})  # bỏ đi không trừ kho (v1.2: đếm cá thể)

    def test_reputation_clamped_at_min(self):
        block = {"stock": stock_items({}), "reputation": Q["reputation_min"], "random_customers": False, "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": [], "patience_ticks_left": 1}]}
        with Workdir() as w:
            code, err, rows = run_quan(w, block, 3)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[-1]["reputation"], Q["reputation_min"])

    def test_default_customer_leaves_after_patience(self):
        with Workdir() as w:
            code, err, rows = run_quan(w, {"stock": stock_items({"ca_loc": 1})}, FIRST + PATIENCE)
            self.assertEqual(code, 0, err)
            self.assertEqual([e["tick"] for e in events(rows, "customer_left")], [FIRST + PATIENCE])


class Determinism(unittest.TestCase):
    def test_ac_q_05_same_seed_same_bytes(self):
        stock = {"ca_loc": 3, "bong_sung": 6, "ca_linh": 9, "bong_dien_dien": 3}
        with Workdir() as w:
            for i in (1, 2):
                code, err, _ = run_quan(w, {"stock": stock_items(stock)}, FIRST + 3 * PATIENCE, seed=11, name=f"o{i}")
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class ScenarioConflicts(unittest.TestCase):
    """AC-Q-06: scenario mâu thuẫn -> mã thoát 2."""

    BAD = [
        {"customers": [{"id": "C1", "table_id": "T1"}]},                                  # thiếu dish_id
        {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},                # món lạ
        {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "left"}]},
        {"stock": stock_items({"bong_sung": 2}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                    "reserved": ["I1"]}]},      # reserved ≠ recipe
        {"stock": stock_items({"bong_sung": 1}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},  # giữ > kho
        {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating", "tip": 0}]},
        {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating", "price": 40}]},
        {"stock": stock_items({"bong_sung": 2}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                    "patience_ticks_left": 0}]},
        {"stock": stock_items({"bong_sung": 2}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                    "patience_ticks_left": PATIENCE + 1}]},
        {"stock": stock_items({"bong_sung": 2}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                                    "price": 40}]},                       # waiting có price
        {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "mood": 1}]},  # trường lạ
        {"hand": "pho"},
        {"stoves": [{"id": "B1", "state": "burning"}]},
        {"stoves": [{"id": "B1", "state": "cooking"}]},                                   # cooking thiếu món
        {"stoves": [{"id": "B1", "state": "idle", "dish": "goi_bong_sung"}]},
        {"random_customers": "yes"},
        {"reputation": Q["reputation_max"] + 1},
    ]

    def test_ac_q_06_conflicts_exit_2(self):
        with Workdir() as w:
            for block in self.BAD:
                code, _, _ = run_quan(w, block, 0)
                self.assertEqual(code, 2, block)

    def test_reserved_more_than_inventory_file_exit_2(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": stock_items({"bong_sung": 1})})
            code, _, _ = run_quan(w, {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},
                                  0, extra=("--inventory", inv))
            self.assertEqual(code, 2)

    def test_valid_prebuilt_customers_exit_0(self):
        good = [
            {"stock": stock_items({"bong_sung": 2}), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": []}]},  # đã nấu
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                            "price": 40, "tip": 8, "eat_ticks_left": 10}]},
            {"hand": "goi_bong_sung", "stoves": [{"id": "B1", "state": "cooking", "dish": "goi_bong_sung",
                                                  "cook_ticks_left": 30}]},
        ]
        with Workdir() as w:
            for block in good:
                code, err, _ = run_quan(w, block, 1)
                self.assertEqual(code, 0, (block, err))


if __name__ == "__main__":
    unittest.main()
