"""Test hộp đen luật Quán (AC-Q-01..12, spec: docs/spec/phase-1/quan.md).

Chỉ chạy `headless_cmd` và đọc JSONL; mọi số liệu lấy từ game.contract.json.
Test đỏ khi lát 3/lát 4 chưa xong là bình thường: báo chủ module (TV2: Q-01..06, TV1: Q-07..12).
Không sửa test cho xanh khi luật sai; nếu PO chốt khác spec thì sửa test và ghi lý do trong commit.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    TUNING = json.load(_f)["tuning"]
Q = TUNING["quan"]
MENU = TUNING["menu"]
DISH = "ca_loc_nuong_trui"
STOVE = Q["stoves"][0]
TABLE = Q["tables"][0]
PATIENCE_MAX = Q["patience_s"] * 60
EAT_TICKS = Q["eat_s"] * 60
NEAR_STOVE = [STOVE["pos"][0], STOVE["pos"][1] - 1]
NEAR_TABLE = [TABLE["pos"][0], TABLE["pos"][1] + 1]


def customer(cid="C1", dish=DISH, patience=PATIENCE_MAX, **extra):
    c = {"id": cid, "table_id": TABLE["id"], "dish_id": dish, "state": "waiting",
         "patience_ticks_left": patience, "reserved": dict(MENU[dish]["recipe"]) if dish in MENU else {}}
    c.update(extra)
    return c


def run_quan(w, block, inputs=None, ticks=10, seed=1, name="o"):
    """Chạy quan với snapshot mỗi tick; trả (rows, {tick: snapshot})."""
    sc = write_json(w.path(f"{name}_sc.json"), {"quan": block})
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", "1", "--out", w.path(f"{name}.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path(f"{name}_in.json"), inputs)]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(f"headless thoát mã {code}: {err}")
    rows = read_jsonl(w.path(f"{name}.jsonl"))
    return rows, {r["tick"]: r for r in snapshots(rows)}


def press(tick):
    return [{"tick": tick, "interact": True}, {"tick": tick + 1, "interact": False}]


def serve_flow(patience):
    """Kịch bản chuẩn: nấu ở bếp, đợi chín, nhặt, đi tới bàn, phục vụ. Trả (block, inputs, serve_tick)."""
    cook_ticks = MENU[DISH]["cook_s"] * 60
    pick_at = cook_ticks + 5
    walk_from = pick_at + 1
    dx, dz = NEAR_TABLE[0] - NEAR_STOVE[0], NEAR_TABLE[1] - NEAR_STOVE[1]
    length = math.hypot(dx, dz)
    walk = math.ceil(length / Q["walk_speed"] * 60) + Q["ramp_max_ticks"]
    serve_at = walk_from + walk + 10
    fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
          {"tick": pick_at, "interact": True},
          {"tick": walk_from, "interact": False, "move": [dx / length, dz / length]},
          {"tick": walk_from + walk, "move": [0, 0]},
          *press(serve_at)]
    if callable(patience):
        patience = patience(serve_at)
    block = {"player": {"pos": NEAR_STOVE}, "stock": dict(MENU[DISH]["recipe"]), "random_customers": False,
             "customers": [customer(patience=patience)]}
    return block, frames(*fr), serve_at


class Customers(unittest.TestCase):
    """Lát 3 (TV2)."""

    def test_ac_q_01_first_customer_on_schedule(self):
        with Workdir() as w:
            rows, snaps = run_quan(w, {"stock": {"ca_loc": 1}}, ticks=Q["first_customer_tick"] + 5)
            arrived = events(rows, "customer_arrived")
            self.assertEqual(len(arrived), 1, arrived)
            self.assertEqual(arrived[0]["tick"], Q["first_customer_tick"])
            self.assertEqual(arrived[0]["data"]["table_id"], TABLE["id"])
            self.assertEqual(snaps[Q["first_customer_tick"] - 1]["customers"], [])
            self.assertEqual(snaps[Q["first_customer_tick"]]["tables"][0]["customer_id"],
                             arrived[0]["data"]["customer_id"])

    def test_ac_q_02_empty_stock_no_dish(self):
        with Workdir() as w:
            rows, snaps = run_quan(w, {"stock": {}}, ticks=Q["first_customer_tick"] + 5)
            self.assertEqual(len(events(rows, "no_dish")), 1)
            self.assertEqual(events(rows, "customer_arrived"), [])
            last = snaps[max(snaps)]
            self.assertEqual(last["customers"], [])
            self.assertTrue(all(t["customer_id"] is None for t in last["tables"]))

    def test_ac_q_03_dish_is_cookable_and_reserves_recipe(self):
        cases = [({"ca_loc": 1}, {"ca_loc_nuong_trui"}),
                 ({"ca_linh": 3, "bong_sung": 2}, {"goi_bong_sung"}),
                 ({"ca_loc": 1, "bong_sung": 2, "ca_linh": 3, "bong_dien_dien": 1}, set(MENU))]
        for stock, allowed in cases:
            for seed in range(1, 6):
                with self.subTest(stock=stock, seed=seed), Workdir() as w:
                    _, snaps = run_quan(w, {"stock": stock}, ticks=Q["first_customer_tick"], seed=seed)
                    c = snaps[Q["first_customer_tick"]]["customers"][0]
                    self.assertIn(c["dish_id"], allowed)
                    self.assertEqual(c["reserved"], MENU[c["dish_id"]]["recipe"])
                    self.assertEqual(c["state"], "waiting")
                    self.assertEqual(c["patience_ticks_left"], PATIENCE_MAX)

    def test_ac_q_04_patience_out_customer_left(self):
        with Workdir() as w:
            block = {"stock": {"ca_loc": 1}, "random_customers": False, "customers": [customer(patience=5)]}
            rows, snaps = run_quan(w, block, ticks=8)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 5)
            self.assertEqual(left[0]["data"]["customer_id"], "C1")
            self.assertTrue(close(snaps[5]["reputation"], Q["reputation_initial"] + Q["left_reputation_delta"], 1e-6))
            self.assertEqual(snaps[5]["customers"], [])
            self.assertIsNone(snaps[5]["tables"][0]["customer_id"])
            self.assertEqual(snaps[5]["stock"], {"ca_loc": 1}, "bỏ đi không được trừ kho")

    def test_ac_q_04_reservation_released_for_next_customer(self):
        with Workdir() as w:
            block = {"stock": {"ca_loc": 1}, "customers": [customer(patience=5)]}
            rows, _ = run_quan(w, block, ticks=Q["first_customer_tick"] + 1)
            self.assertEqual(len(events(rows, "customer_arrived")), 1, "nguyên liệu phải được nhả cho khách sau")
            self.assertEqual(events(rows, "no_dish"), [])

    def test_ac_q_04_reputation_clamped_at_min(self):
        with Workdir() as w:
            block = {"stock": {"ca_loc": 1}, "random_customers": False, "reputation": Q["reputation_min"],
                     "customers": [customer(patience=1)]}
            _, snaps = run_quan(w, block, ticks=2)
            self.assertEqual(snaps[1]["reputation"], Q["reputation_min"])

    def test_random_customers_false_disables_schedule(self):
        with Workdir() as w:
            rows, _ = run_quan(w, {"stock": {"ca_loc": 1}, "random_customers": False},
                               ticks=Q["first_customer_tick"] + 5)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    def test_ac_q_05_same_seed_same_bytes(self):
        stock = {"ca_loc": 3, "bong_sung": 4, "ca_linh": 3, "bong_dien_dien": 1}
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": stock}})
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "7", "--ticks", "4000", "--scenario", sc,
                                         "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            self.assertTrue(events(read_jsonl(w.path("o1.jsonl")), "customer_arrived"), "phải có khách để so chuỗi món")


class ScenarioConflicts(unittest.TestCase):
    """AC-Q-06: scenario mâu thuẫn -> mã thoát 2 (quan.md mục A4)."""

    def assert_exit_2(self, block):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": block})
            out = w.path("o.jsonl")
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
            self.assertEqual(code, 2, block)
            self.assertFalse(os.path.exists(out), "lỗi đầu vào phải thoát trước khi ghi đầu ra")

    def test_valid_fixture_is_accepted(self):
        eating = customer(state="eating", eat_ticks_left=10, price=MENU[DISH]["price"], tip=0, reserved={})
        for c in (customer(), eating):
            with self.subTest(state=c["state"]), Workdir() as w:
                run_quan(w, {"stock": {"ca_loc": 1}, "customers": [c]}, ticks=0)

    def test_ac_q_06_reserved_exceeds_stock(self):
        self.assert_exit_2({"stock": {"bong_sung": 2}, "customers": [customer()]})

    def test_ac_q_06_dish_not_on_menu(self):
        self.assert_exit_2({"stock": {"ca_loc": 1}, "customers": [customer(dish="pho_bo", reserved={"ca_loc": 1})]})

    def test_ac_q_06_reserved_differs_from_recipe(self):
        self.assert_exit_2({"stock": {"ca_loc": 1, "bong_sung": 2},
                            "customers": [customer(reserved={"bong_sung": 2})]})

    def test_ac_q_06_eating_missing_price_or_tip(self):
        for missing in ("price", "tip"):
            with self.subTest(missing=missing):
                c = customer(state="eating", eat_ticks_left=10, price=MENU[DISH]["price"], tip=0, reserved={})
                del c[missing]
                self.assert_exit_2({"stock": {"ca_loc": 1}, "customers": [c]})

    def test_ac_q_06_waiting_patience_out_of_range(self):
        for patience in (0, PATIENCE_MAX + 1):
            with self.subTest(patience=patience):
                self.assert_exit_2({"stock": {"ca_loc": 1}, "customers": [customer(patience=patience)]})

    def test_ac_q_06_hand_not_on_menu(self):
        self.assert_exit_2({"hand": "pho_bo"})

    def test_ac_q_06_stove_state_invalid(self):
        self.assert_exit_2({"stoves": [{"id": STOVE["id"], "state": "burning"}]})


class Kitchen(unittest.TestCase):
    """Lát 4 (TV1): bếp và bưng món."""

    def test_ac_q_07_cook_then_ready(self):
        cook_ticks = MENU[DISH]["cook_s"] * 60
        with Workdir() as w:
            block = {"player": {"pos": NEAR_STOVE}, "stock": {"ca_loc": 1}, "random_customers": False,
                     "customers": [customer()]}
            rows, snaps = run_quan(w, block, frames(*press(0)), ticks=cook_ticks + 3)
            started = events(rows, "cook_started")
            ready = events(rows, "dish_ready")
            self.assertEqual(len(started), 1)
            self.assertEqual(started[0]["data"], {"stove_id": STOVE["id"], "dish": DISH})
            self.assertEqual(snaps[started[0]["tick"]]["stoves"][0]["state"], "cooking")
            self.assertEqual(snaps[started[0]["tick"]]["stock"], {}, "nấu phải trừ nguyên liệu")
            self.assertEqual(len(ready), 1)
            self.assertEqual(ready[0]["tick"] - started[0]["tick"], cook_ticks)
            self.assertEqual(ready[0]["data"], {"stove_id": STOVE["id"], "dish": DISH})
            self.assertEqual(snaps[ready[0]["tick"]]["stoves"][0]["state"], "ready")

    def test_ac_q_08_pick_up_ready_dish(self):
        with Workdir() as w:
            block = {"player": {"pos": NEAR_STOVE}, "random_customers": False,
                     "stoves": [{"id": STOVE["id"], "state": "ready", "dish": DISH}]}
            rows, snaps = run_quan(w, block, frames(*press(0)), ticks=3)
            picked = events(rows, "dish_picked")
            self.assertEqual(len(picked), 1)
            self.assertEqual(picked[0]["data"], {"stove_id": STOVE["id"], "dish": DISH})
            self.assertEqual(snaps[1]["hand"], DISH)
            self.assertEqual(snaps[1]["stoves"][0]["state"], "idle")

    def test_ac_q_08_full_hand_cannot_pick_up(self):
        with Workdir() as w:
            block = {"player": {"pos": NEAR_STOVE}, "random_customers": False, "hand": "goi_bong_sung",
                     "stoves": [{"id": STOVE["id"], "state": "ready", "dish": DISH}]}
            rows, snaps = run_quan(w, block, frames(*press(0)), ticks=3)
            self.assertEqual(events(rows, "dish_picked"), [])
            self.assertEqual(snaps[3]["hand"], "goi_bong_sung")
            self.assertEqual(snaps[3]["stoves"][0]["state"], "ready")


class ServiceAndMoney(unittest.TestCase):
    """Lát 4 (TV1): phục vụ, trả tiền, boa, uy tín."""

    def test_ac_q_09_serve_then_paid_with_price_and_tip(self):
        price = MENU[DISH]["price"]
        tip = round(price * Q["tip_rate"])
        with Workdir() as w:
            block, inputs, serve_at = serve_flow(PATIENCE_MAX)
            rows, snaps = run_quan(w, block, inputs, ticks=serve_at + EAT_TICKS + 5)
            served = events(rows, "served")
            paid = events(rows, "paid")
            self.assertEqual(len(served), 1, events(rows))
            self.assertEqual(served[0]["data"], {"customer_id": "C1", "table_id": TABLE["id"], "dish": DISH})
            self.assertIsNone(snaps[served[0]["tick"]]["hand"])
            self.assertEqual(snaps[served[0]["tick"]]["customers"][0]["state"], "eating")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["tick"] - served[0]["tick"], EAT_TICKS)
            self.assertEqual(paid[0]["data"], {"customer_id": "C1", "amount": price + tip, "tip": tip})
            last = snaps[max(snaps)]
            self.assertEqual(last["money"], price + tip)
            self.assertEqual(last["earned"], price + tip)
            self.assertEqual(last["customers"], [])
            self.assertIsNone(last["tables"][0]["customer_id"])

    def test_ac_q_09_wrong_dish_is_not_served(self):
        with Workdir() as w:
            block = {"player": {"pos": NEAR_TABLE}, "hand": "goi_bong_sung", "stock": {"ca_loc": 1},
                     "random_customers": False, "customers": [customer()]}
            rows, snaps = run_quan(w, block, frames(*press(0)), ticks=3)
            self.assertEqual(events(rows, "served"), [])
            self.assertEqual(snaps[3]["hand"], "goi_bong_sung")
            self.assertEqual(snaps[3]["customers"][0]["state"], "waiting")

    def test_ac_q_10_high_patience_gets_tip_and_reputation(self):
        with Workdir() as w:
            block, inputs, serve_at = serve_flow(PATIENCE_MAX)
            rows, snaps = run_quan(w, block, inputs, ticks=serve_at + EAT_TICKS + 5)
            self.assertGreater(events(rows, "paid")[0]["data"]["tip"], 0)
            self.assertTrue(close(snaps[max(snaps)]["reputation"], Q["reputation_initial"] + Q["tip_reputation"], 1e-6))

    def test_ac_q_10_low_patience_no_tip(self):
        price = MENU[DISH]["price"]
        with Workdir() as w:
            block, inputs, serve_at = serve_flow(lambda at: at + PATIENCE_MAX // 4)
            rows, snaps = run_quan(w, block, inputs, ticks=serve_at + EAT_TICKS + 5)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1, events(rows))
            self.assertEqual(paid[0]["data"]["tip"], 0)
            self.assertEqual(paid[0]["data"]["amount"], price)
            self.assertTrue(close(snaps[max(snaps)]["reputation"], Q["reputation_initial"], 1e-6))

    def _overlap_block(self, player_x):
        """Bếp và bàn cùng trong bán kính; tay cầm đúng món khách đang chờ."""
        return {"player": {"pos": [player_x, 5]}, "hand": DISH, "random_customers": False,
                "stoves": [{"id": STOVE["id"], "pos": [5, 5]}], "tables": [{"id": TABLE["id"], "pos": [6, 5]}],
                "customers": [customer(reserved={})]}

    def test_ac_q_11_tie_prefers_stove_and_does_not_fall_through(self):
        with Workdir() as w:
            rows, snaps = run_quan(w, self._overlap_block(5.5), frames(*press(0)), ticks=2)
            self.assertEqual(events(rows, "served"), [], "bếp được chọn nhưng không hợp lệ thì không thử bàn")
            self.assertEqual(snaps[2]["hand"], DISH)

    def test_ac_q_11_nearest_object_wins(self):
        with Workdir() as w:
            rows, _ = run_quan(w, self._overlap_block(5.9), frames(*press(0)), ticks=2)
            self.assertEqual(len(events(rows, "served")), 1)
            self.assertEqual(events(rows, "cook_started"), [])

    def test_ac_q_11_holding_interact_acts_once(self):
        with Workdir() as w:
            block = {"player": {"pos": NEAR_STOVE}, "stock": {"ca_loc": 2}, "random_customers": False,
                     "customers": [customer()]}
            rows, _ = run_quan(w, block, frames({"tick": 0, "interact": True}), ticks=5)
            self.assertEqual(len(events(rows, "cook_started")), 1)

    def test_ac_q_12_quan_end_matches_snapshot(self):
        with Workdir() as w:
            block, inputs, serve_at = serve_flow(PATIENCE_MAX)
            end_tick = serve_at + EAT_TICKS + 20
            block["time_left_ticks"] = end_tick
            rows, snaps = run_quan(w, block, inputs, ticks=end_tick + 10)
            ended = events(rows, "quan_end")
            self.assertEqual(len(ended), 1)
            self.assertEqual(ended[0]["tick"], end_tick)
            data, last = ended[0]["data"], snaps[end_tick]
            self.assertEqual(data["reason"], "time")
            for key in ("money", "earned", "reputation"):
                self.assertEqual(data[key], last[key], key)
            self.assertGreater(data["earned"], 0, "kịch bản phải có doanh thu")
            self.assertEqual(data["shift_earned"], data["earned"], "lượt chỉ có một ca")
            self.assertEqual(rows[-1]["reason"], "time")


if __name__ == "__main__":
    unittest.main()
