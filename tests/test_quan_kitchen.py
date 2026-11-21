"""Test hộp đen quán v1.1 — bếp, bưng, phục vụ, tiền, đóng ca (TV2). TICKET-02 mục 1.3.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_kitchen -v
Dựng trạng thái bằng scenario (vị trí người chơi, khách, bếp, tay) để không phải đi bộ.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, stock_counts, events, frames, read_jsonl, run_headless, snapshots, write_json
from helpers import hold_items, stock_counts, stock_items

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    T = json.load(_f)["tuning"]
Q, MENU = T["quan"], T["menu"]
PATIENCE = int(round(Q["patience_s"] * 60))
EAT = int(round(Q["eat_s"] * 60))
NEAR_B1 = [2, 7]     # cách B1 [2,8] 1 m, cách B2 [5,8] > 1.5 m
NEAR_T1 = [9, 3]     # cách T1 [9,2] 1 m, cách T3 [9,6] 3 m


def cook_ticks(dish):
    return int(round(MENU[dish]["cook_s"] * 60))


def run(w, block, ticks, press=(0,), extra=()):
    block = {"random_customers": False, **block}
    sc = write_json(w.path("sc.json"), {"quan": block})
    fr = []
    for t in press:
        fr += [{"tick": t, "interact": True}, {"tick": t + 1, "interact": False}]
    inp = write_json(w.path("in.json"), frames(*fr))
    code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--out", w.path("o.jsonl"), *extra)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else None)


def waiting(cid, table, dish, **kw):
    return {"id": cid, "table_id": table, "dish_id": dish, **kw}


class Data(unittest.TestCase):
    def test_contract_v11_standard_data(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            c = json.load(f)
        self.assertIn(c["contract_version"], ("1.2", "1.3"))
        self.assertEqual([s["id"] for s in Q["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in Q["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(MENU), 6)
        for plan in T["day_plan"]:  # ingredients = Σ recipe × số suất
            want = {}
            for dish, n in plan["dishes"].items():
                for k, m in MENU[dish]["recipe"].items():
                    want[k] = want.get(k, 0) + m * n
            self.assertEqual(plan["ingredients"], want, plan["day"])

    def test_new_ingredients_accepted_and_new_dish_chosen(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": stock_items({"ca_keo": 2, "keo_neo": 1})})
            sc = write_json(w.path("sc.json"), {"quan": {}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(Q["first_customer_tick"]),
                                     "--inventory", inv, "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            arr = events(read_jsonl(w.path("o.jsonl")), "customer_arrived")
            self.assertEqual(arr[0]["data"]["dish_id"], "ca_keo_nuong")


class Stove(unittest.TestCase):
    def test_ac_q_07_cook_then_ready(self):
        block = {"player": {"pos": NEAR_B1}, "stock": stock_items({"bong_sung": 2}),
                 "customers": [waiting("C1", "T1", "goi_bong_sung")]}
        n = cook_ticks("goi_bong_sung")
        with Workdir() as w:
            code, err, rows = run(w, block, n + 2)
            self.assertEqual(code, 0, err)
            cs = events(rows, "cook_started")
            self.assertEqual([(e["tick"], {k: e["data"][k] for k in ("stove_id", "order_id", "dish_id")}) for e in cs],
                             [(1, {"stove_id": "B1", "order_id": "C1", "dish_id": "goi_bong_sung"})])
            self.assertEqual([it["kind"] for it in cs[0]["data"]["items"]], ["bong_sung", "bong_sung"])  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể
            self.assertEqual(events(rows, "dish_ready")[0]["tick"], 1 + n)
            last = snapshots(rows)[-1]
            self.assertEqual(last["stock"], [])                       # đã tiêu đúng các cá thể giữ chỗ
            self.assertEqual(last["customers"][0]["reserved"], [])
            self.assertEqual(last["customers"][0]["order_status"], "ready")
            self.assertEqual(last["stoves"][0]["state"], "ready")

    def test_stove_takes_oldest_reserved_order_then_table_id(self):
        stock = stock_items({"bong_sung": 2, "ca_loc": 2})
        block = {"player": {"pos": NEAR_B1}, "stock": stock, "customers": [
            waiting("C1", "T2", "goi_bong_sung", order_tick=5),
            waiting("C2", "T1", "ca_loc_nuong_trui", order_tick=5),
            waiting("C3", "T4", "ca_loc_nuong_trui", order_tick=9)]}
        with Workdir() as w:
            code, err, rows = run(w, block, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started")[0]["data"]["order_id"], "C2")  # cùng order_tick -> T1 trước

    def test_idle_stove_without_reserved_order_does_nothing(self):
        with Workdir() as w:
            code, err, rows = run(w, {"player": {"pos": NEAR_B1}}, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started"), [])

    def test_ac_q_08_pick_up_ready_dish_and_hand_limit(self):
        ready = {"id": "B1", "state": "ready", "dish": "goi_bong_sung"}
        with Workdir() as w:
            code, err, rows = run(w, {"player": {"pos": NEAR_B1}, "stoves": [ready]}, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "dish_picked")[0]["data"],
                             {"stove_id": "B1", "order_id": None, "dish_id": "goi_bong_sung",
                              "base_price": MENU["goi_bong_sung"]["price"]})  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể (dish_picked thêm base_price)
            last = snapshots(rows)[-1]
            self.assertEqual(last["hand"], "goi_bong_sung")
            self.assertEqual(last["stoves"][0]["state"], "idle")
            # tay đã cầm món -> không nhặt thêm
            code, err, rows = run(w, {"player": {"pos": NEAR_B1}, "stoves": [ready], "hand": "ca_loc_nuong_trui"}, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "dish_picked"), [])
            self.assertEqual(snapshots(rows)[-1]["hand"], "ca_loc_nuong_trui")

    def test_ac_q_11_tie_picks_stove_by_id(self):
        # [3.5, 8] cách B1 và B2 đúng 1.5 m (bằng bán kính) -> chọn B1 (id nhỏ)
        block = {"player": {"pos": [3.5, 8]}, "stock": stock_items({"bong_sung": 2}),
                 "customers": [waiting("C1", "T1", "goi_bong_sung")]}
        with Workdir() as w:
            code, err, rows = run(w, block, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started")[0]["data"]["stove_id"], "B1")


class Serve(unittest.TestCase):
    def serve(self, w, patience, dish="goi_bong_sung", hand="goi_bong_sung", ticks=None):
        block = {"player": {"pos": NEAR_T1}, "hand": hand,
                 "customers": [waiting("C1", "T1", dish, reserved=[], patience_ticks_left=patience)]}
        return run(w, block, ticks or EAT + 2)

    def test_ac_q_09_serve_then_pay(self):
        price = MENU["goi_bong_sung"]["price"]
        tip = math.floor(price * Q["tip_rate"])
        with Workdir() as w:
            code, err, rows = self.serve(w, PATIENCE)
            self.assertEqual(code, 0, err)
            sv = events(rows, "served")
            self.assertEqual([(e["tick"], e["data"]) for e in sv], [(1, {"customer_id": "C1", "table_id": "T1",
                              "dish_id": "goi_bong_sung", "price": price, "tip": tip})])
            pd = events(rows, "paid")
            self.assertEqual(pd[0]["tick"], 1 + EAT)
            self.assertEqual(pd[0]["data"]["amount"], price + tip)
            last = snapshots(rows)[-1]
            self.assertEqual((last["money"], last["earned"], last["shift_earned"]), (price + tip,) * 3)
            self.assertEqual(last["hand"], None)
            self.assertEqual(last["customers"], [])
            self.assertAlmostEqual(last["reputation"], Q["reputation_initial"] + Q["tip_reputation"])
            self.assertEqual(last["score"], last["earned"] + T["score"]["reputation_multiplier"] * math.floor(last["reputation"]))

    def test_ac_q_10_tip_threshold_half_patience(self):
        half = int(Q["tip_min_patience_ratio"] * PATIENCE)
        with Workdir() as w:
            # Đổi test (TICKET-03 thứ tự tick): giao TRƯỚC khi trừ kiên nhẫn của bước -> đúng half lúc giao vẫn boa
            code, err, rows = self.serve(w, half, ticks=2)
            self.assertEqual(code, 0, err)
            self.assertGreater(events(rows, "served")[0]["data"]["tip"], 0)
            code, err, rows = self.serve(w, half - 1, ticks=EAT + 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)
            self.assertEqual(snapshots(rows)[-1]["reputation"], Q["reputation_initial"])  # không boa -> không +uy tín

    def test_wrong_dish_does_nothing(self):
        with Workdir() as w:
            code, err, rows = self.serve(w, PATIENCE, hand="ca_loc_nuong_trui", ticks=2)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "served"), [])
            self.assertEqual(snapshots(rows)[-1]["hand"], "ca_loc_nuong_trui")

    def test_serving_reserved_order_releases_reservation(self):
        block = {"player": {"pos": NEAR_T1}, "hand": "goi_bong_sung", "stock": stock_items({"bong_sung": 2}),
                 "customers": [waiting("C1", "T1", "goi_bong_sung")]}
        with Workdir() as w:
            code, err, rows = run(w, block, 2)
            self.assertEqual(code, 0, err)
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"][0]["reserved"], [])
            self.assertEqual(stock_counts(last["stock"]), {"bong_sung": 2})  # chưa nấu thì không trừ kho  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể


class CloseShift(unittest.TestCase):
    def test_ac_q_12_close_pays_eating_and_waiting_leave_without_penalty(self):
        block = {"time_left_ticks": 3, "hand": "goi_bong_sung", "stock": stock_items({"ca_loc": 1}),
                 "stoves": [{"id": "B1", "state": "cooking", "dish": "goi_bong_sung", "order_id": "C2",
                             "cook_ticks_left": 100}],
                 "customers": [
                     {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                      "price": 40, "tip": 8, "eat_ticks_left": 100},
                     waiting("C2", "T2", "goi_bong_sung", reserved=[]),
                     waiting("C3", "T3", "ca_loc_nuong_trui", patience_ticks_left=3)]}  # hết kiên nhẫn đúng bước cuối
        with Workdir() as w:
            code, err, rows = run(w, block, 10, press=())
            self.assertEqual(code, 0, err)
            self.assertEqual([e["data"]["amount"] for e in events(rows, "paid")], [48])
            left = events(rows, "customer_left")
            self.assertEqual([(e["data"]["customer_id"], e["data"]["reason"]) for e in left],
                             [("C2", "closing"), ("C3", "closing")])
            end = events(rows, "quan_end")[0]
            self.assertEqual(end["tick"], 3)
            self.assertEqual(end["data"]["money"], 48)
            self.assertEqual(end["data"]["shift_earned"], 48)
            self.assertAlmostEqual(end["data"]["reputation"], Q["reputation_initial"] + Q["tip_reputation"])
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"], [])
            self.assertEqual(last["hand"], None)
            self.assertTrue(all(s["state"] == "idle" and s["dish"] is None for s in last["stoves"]))
            self.assertEqual(stock_counts(last["stock"]), {"ca_loc": 1})  # phần giữ được nhả, không mất  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể
            self.assertEqual(end["data"]["money"], last["money"])


class Scenario(unittest.TestCase):
    def test_bad_order_fields_exit_2(self):
        bad = [
            {"customers": [waiting("C1", "T1", "goi_bong_sung", order_status="served")]},
            {"customers": [waiting("C1", "T1", "goi_bong_sung", order_status="cooking", reserved=["I1", "I2"])],
             "stock": stock_items({"bong_sung": 2})},
            {"customers": [waiting("C1", "T1", "goi_bong_sung", order_status="lost")]},
            {"customers": [waiting("C1", "T1", "goi_bong_sung", order_tick=-1)]},
            {"stoves": [{"id": "B1", "state": "idle", "order_id": "C1"}]},
            {"stoves": [{"id": "B3"}]},
        ]
        with Workdir() as w:
            for block in bad:
                code, _, _ = run(w, block, 0, press=())
                self.assertEqual(code, 2, block)


class Ctx(unittest.TestCase):
    """Giao diện ctx (spec phase-2/README.md 3.2) + stats() cho DayResult — test đơn vị gọi thẳng QuanSim."""

    def make(self, scenario, ctx=None, inventory=None):
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        return QuanSim(T, scenario, Streams(1), IdAllocator(), inventory=inventory, ctx=ctx)

    def test_ctx_plan_dishes_money_reputation(self):
        sim = self.make({}, ctx={"day": 1, "plan_dishes": {"goi_bong_sung": 3}, "money": 50, "earned": 80,
                                 "reputation": 4.0}, inventory={"ca_loc": 5, "bong_sung": 2})
        self.assertEqual((sim.money, sim.earned, sim.reputation, sim.dishes), (50, 80, 4.0, ["goi_bong_sung"]))
        self.assertEqual(sim._pick_dish(), "goi_bong_sung")  # cá lóc đủ nhưng không thuộc kế hoạch

    def test_stats_after_serve_and_pay(self):
        from chonoi.inputs import InputState
        sim = self.make({"player": {"pos": NEAR_T1}, "hand": "goi_bong_sung", "random_customers": False,
                         "customers": [waiting("C1", "T1", "goi_bong_sung", reserved=[])]})
        sim.step(InputState((0.0, 0.0), {}, {"interact"}))
        for _ in range(EAT):
            sim.step(InputState((0.0, 0.0), {}, set()))
        price = MENU["goi_bong_sung"]["price"]
        tip = math.floor(price * Q["tip_rate"])
        self.assertEqual(sim.stats(), {"served": 1, "left": 0, "money": price + tip, "tips": tip,
                                       "reputation_delta": Q["tip_reputation"], "best_dish": "goi_bong_sung"})


if __name__ == "__main__":
    unittest.main()
