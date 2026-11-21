"""Test hộp đen Phase 3 — quán có độ tươi + bàn giao trong day (TV2). TICKET-03, AC-P3-08 … 14 (phần quán), 13.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p3_quan -v
Hao quán = 0.25/s = 1/240 mỗi tick. Fixture chọn để mỗi ca rơi rõ một phía của ngưỡng 30 / phép floor.
"""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    T = json.load(_f)["tuning"]
Q, MENU = T["quan"], T["menu"]
NEAR_B1 = [2, 7]
NEAR_T1 = [9, 3]
TICK_DECAY = 0.25 / 60


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def run(w, block, ticks, press=(), every=1, extra=(), mode="quan"):
    block = {"random_customers": False, **block}
    sc = write_json(w.path("sc.json"), {mode: block})
    fr = []
    for t in press:
        fr += [{"tick": t, "interact": True}, {"tick": t + 1, "interact": False}]
    args = ["--mode", mode, "--seed", "1", "--ticks", str(ticks), "--scenario", sc, "--out", w.path("o.jsonl"),
            "--snapshot-every", str(every), *extra]
    if fr:
        args += ["--inputs", write_json(w.path("in.json"), frames(*fr))]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path("o.jsonl")) if code == 0 else None)


def snap_at(rows, tick):
    return [s for s in snapshots(rows) if s["tick"] == tick][-1]


class Decay(unittest.TestCase):
    def test_ac_p3_08_stock_keeps_ids_and_decays_quarter_per_second(self):
        stock = [item("I3", "ca_loc", 100), item("I9", "bong_sung", 20)]  # nhận cả hàng ươn
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock}, 60)
            self.assertEqual(code, 0, err)
            s0, s60 = snap_at(rows, 0), snap_at(rows, 60)
            self.assertEqual(s0["stock"], stock)
            self.assertEqual([it["id"] for it in s60["stock"]], ["I3", "I9"])
            self.assertTrue(close(s60["stock"][0]["fresh"], 99.75, 0.01))
            self.assertTrue(close(s60["stock"][1]["fresh"], 19.75, 0.01))

    def test_ac_p3_09_spoiled_threshold_exact_tick(self):
        cases = [(30.004, 1), (30.005, 2), (30, 1)]  # 30.004 - 1/240 < 30; 30.005 - 1/240 >= 30
        with Workdir() as w:
            for fresh, tick in cases:
                code, err, rows = run(w, {"stock": [item("I1", "ca_linh", fresh)]}, 5)
                self.assertEqual(code, 0, err)
                sp = events(rows, "spoiled")
                self.assertEqual([(e["tick"], e["data"]) for e in sp],
                                 [(tick, {"item_id": "I1", "kind": "ca_linh", "location": "stock"})], fresh)

    def test_spoiled_many_same_tick_by_id_and_only_once(self):
        stock = [item("I10", "ca_loc", 30), item("I2", "ca_loc", 30), item("I5", "ca_loc", 31)]
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock}, 300)
            self.assertEqual(code, 0, err)
            self.assertEqual([(e["tick"], e["data"]["item_id"]) for e in events(rows, "spoiled")],
                             [(1, "I2"), (1, "I10"), (241, "I5")])  # 31 - 240/240 = 30 chưa < 30

    def test_spoiled_not_reserved_or_cooked(self):
        with Workdir() as w:
            code, err, rows = run(w, {"stock": [item("I1", "ca_loc", 20)], "random_customers": True},
                                  Q["first_customer_tick"])
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(len(events(rows, "no_dish")), 1)

    def test_pause_stops_decay(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"random_customers": False, "stock": [item("I1", "ca_loc", 90)]}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "pause": True}, {"tick": 1, "pause": False}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "100", "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(w.path("o.jsonl")))
            self.assertEqual(snap_at(snaps, 100)["stock"][0]["fresh"], snap_at(snaps, 0)["stock"][0]["fresh"])


class Reserve(unittest.TestCase):
    def test_ac_p3_10_freshest_first_tie_by_id(self):
        stock = [item("I1", "ca_loc", 60), item("I4", "ca_loc", 90), item("I2", "ca_loc", 90)]
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock, "random_customers": True}, Q["first_customer_tick"])
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[-1]["customers"][0]["reserved"], ["I2"])

    def test_reserved_sorted_by_kind_then_id(self):
        stock = [item("I9", "ca_linh", 90), item("I3", "ca_linh", 90), item("I5", "ca_linh", 90),
                 item("I1", "bong_dien_dien", 90)]
        block = {"stock": stock, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}]}
        with Workdir() as w:
            code, err, rows = run(w, block, 0)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["I1", "I3", "I5", "I9"])

    def test_ac_p3_11_rereserve_once_when_held_item_spoils(self):
        stock = [item("I1", "ca_loc", 30.004), item("I2", "ca_loc", 80)]
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock, "customers": [c]}, 2)
            self.assertEqual(code, 0, err)
            self.assertEqual(snap_at(rows, 0)["customers"][0]["reserved"], ["I1"])
            c1 = snap_at(rows, 1)["customers"][0]
            self.assertEqual((c1["reserved"], c1["order_status"]), (["I2"], "reserved"))

    def test_unfulfillable_when_no_replacement_customer_keeps_waiting(self):
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"], "patience_ticks_left": 10}
        with Workdir() as w:
            code, err, rows = run(w, {"stock": [item("I1", "ca_loc", 30.004)], "customers": [c]}, 12)
            self.assertEqual(code, 0, err)
            c1 = snap_at(rows, 1)["customers"][0]
            self.assertEqual((c1["reserved"], c1["order_status"], c1["state"]), ([], "unfulfillable", "waiting"))
            self.assertEqual(events(rows, "customer_left")[0]["tick"], 10)  # chờ tới hết kiên nhẫn

    def test_unfulfillable_not_cooked(self):
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        with Workdir() as w:
            code, err, rows = run(w, {"player": {"pos": NEAR_B1}, "stock": [item("I1", "ca_loc", 30.004)],
                                      "customers": [c]}, 3, press=(1,))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "cook_started"), [])

    def test_rereserve_order_by_order_tick_then_table(self):
        stock = [item("I1", "ca_loc", 30.004), item("I2", "ca_loc", 30.004), item("I3", "ca_loc", 70)]
        cs = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"], "order_tick": 5},
              {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"], "order_tick": 3}]
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock, "customers": cs}, 1)
            self.assertEqual(code, 0, err)
            by_id = {c["id"]: c for c in snap_at(rows, 1)["customers"]}
            self.assertEqual((by_id["C2"]["reserved"], by_id["C2"]["order_status"]), (["I3"], "reserved"))
            self.assertEqual((by_id["C1"]["reserved"], by_id["C1"]["order_status"]), ([], "unfulfillable"))


class Price(unittest.TestCase):
    def cook(self, w, stock, dish, extra_customers=()):
        c = {"id": "C1", "table_id": "T1", "dish_id": dish}
        return run(w, {"player": {"pos": NEAR_B1}, "stock": stock, "customers": [c, *extra_customers]}, 2, press=(0,))

    def test_ac_p3_12_base_price_floor_mean_fresh(self):
        # cá lóc 50.5 -> sau hao bước nấu ≈ 50.4958 -> floor(60 × 0.504958) = 30
        with Workdir() as w:
            code, err, rows = self.cook(w, [item("I1", "ca_loc", 50.5)], "ca_loc_nuong_trui")
            self.assertEqual(code, 0, err)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["base_price"], 30)
            self.assertEqual([it["id"] for it in cs["items"]], ["I1"])
            self.assertTrue(close(cs["items"][0]["fresh"], 50.5 - TICK_DECAY, 0.01))
            self.assertEqual(snapshots(rows)[-1]["stoves"][0]["base_price"], 30)

    def test_lau_mean_and_items_sorted_kind_then_id(self):
        # TB sau hao ≈ 85.0033 -> floor(120 × 0.850033) = 102
        stock = [item("I4", "ca_linh", 100), item("I2", "ca_linh", 90.01), item("I3", "ca_linh", 80.01),
                 item("I9", "bong_dien_dien", 70.01)]
        with Workdir() as w:
            code, err, rows = self.cook(w, stock, "lau_ca_linh_dien_dien")
            self.assertEqual(code, 0, err)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["base_price"], 102)
            self.assertEqual([(it["kind"], it["id"]) for it in cs["items"]],
                             [("bong_dien_dien", "I9"), ("ca_linh", "I2"), ("ca_linh", "I3"), ("ca_linh", "I4")])
            self.assertEqual(snapshots(rows)[-1]["stock"], [])  # tiêu đúng các id đang giữ

    def test_tip_on_fresh_price(self):
        """Món chốt 30 trên bếp -> nhặt -> giao: giá 30, boa floor(30 × 0.2) = 6 (test đơn vị gọi thẳng QuanSim)."""
        from chonoi.ids import IdAllocator
        from chonoi.inputs import InputState
        from chonoi.rng import Streams
        from chonoi.sim.quan import QuanSim
        sc = {"player": {"pos": NEAR_B1}, "random_customers": False,
              "stoves": [{"id": "B1", "state": "ready", "dish": "ca_loc_nuong_trui", "base_price": 30}],
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": []}]}
        sim = QuanSim(T, sc, Streams(1), IdAllocator())
        press, idle = InputState((0.0, 0.0), {}, {"interact"}), InputState((0.0, 0.0), {}, set())
        sim.step(press)
        sim.pos = [float(c) for c in NEAR_T1]
        sim.step(idle)
        ev = sim.step(press)
        served = [d for n, d in ev if n == "served"][0]
        self.assertEqual((served["price"], served["tip"]), (30, 6))


class Serve(unittest.TestCase):
    def test_served_price_is_locked_base_price_and_tip_floor(self):
        """Dựng món đã chốt trên bếp (ready, base_price 30) -> nhặt -> giao ngay cạnh bàn (scenario đặt người chơi)."""
        stoves = [{"id": "B1", "state": "ready", "dish": "ca_loc_nuong_trui", "base_price": 30}]
        with Workdir() as w:
            code, err, rows = run(w, {"player": {"pos": NEAR_B1}, "stoves": stoves}, 2, press=(0,))
            self.assertEqual(code, 0, err)
            last = snapshots(rows)[-1]
            self.assertEqual((last["hand"], last["hand_base_price"]), ("ca_loc_nuong_trui", 30))

    def test_serve_uses_hand_base_price(self):
        block = {"player": {"pos": NEAR_T1}, "hand": "ca_loc_nuong_trui",
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": []}]}
        with Workdir() as w:
            code, err, rows = run(w, block, 2, press=(0,))
            self.assertEqual(code, 0, err)
            price = MENU["ca_loc_nuong_trui"]["price"]  # món dựng sẵn trên tay không có fresh -> giá niêm yết
            self.assertEqual(events(rows, "served")[0]["data"]["price"], price)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], math.floor(price * Q["tip_rate"]))

    def test_serve_on_patience_zero_tick_is_valid(self):
        block = {"player": {"pos": NEAR_T1}, "hand": "ca_loc_nuong_trui",
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": [],
                                "patience_ticks_left": 1}]}
        with Workdir() as w:
            code, err, rows = run(w, block, 2, press=(0,))
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "served")), 1)
            self.assertEqual(events(rows, "customer_left"), [])


class Scenario(unittest.TestCase):
    def test_ac_p3_14_bad_reserved_exit_2(self):
        stock = [item("I1", "ca_loc", 80), item("I2", "ca_loc", 20), item("I3", "bong_sung", 80)]
        bad = [
            [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I9"]}],   # không có trong kho
            [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]}],   # đã ươn
            [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I3"]}],   # sai công thức
            [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
             {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],  # dùng chung
            [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}],                            # tự cấp không đủ
            [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "cooking",
              "reserved": ["I1"]}],
        ]
        with Workdir() as w:
            for cs in bad:
                code, _, _ = run(w, {"stock": stock, "customers": cs}, 0)
                self.assertEqual(code, 2, cs)
            for st in ([item("I1", "ca_loc", 80), item("I1", "ca_loc", 70)], [item("I1", "ca_loc", 101)],
                       [item("I1", "pho", 50)], [{"id": "", "kind": "ca_loc", "fresh": 5}]):
                code, _, _ = run(w, {"stock": st}, 0)
                self.assertEqual(code, 2, st)

    def test_auto_reserve_by_order_tick_freshest(self):
        stock = [item("I1", "ca_loc", 60), item("I2", "ca_loc", 95)]
        cs = [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 9},
              {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 2}]
        with Workdir() as w:
            code, err, rows = run(w, {"stock": stock, "customers": cs}, 0)
            self.assertEqual(code, 0, err)
            by_id = {c["id"]: c["reserved"] for c in snapshots(rows)[0]["customers"]}
            self.assertEqual(by_id, {"C1": ["I1"], "C2": ["I2"]})


class Day(unittest.TestCase):
    SC = {"day": {}, "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
    G = int(T["gather"]["duration_s"] * 60)
    Q_TICKS = int(Q["duration_s"] * 60)

    def run_day(self, w, days, ticks, fr):
        sc = write_json(w.path("d.json"), self.SC)
        inp = write_json(w.path("di.json"), frames(*fr))
        code, err = run_headless("--mode", "day", "--days", str(days), "--seed", "1", "--ticks", str(ticks), "--scenario",
                                 sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("d.jsonl"))
        self.assertEqual(code, 0, err)
        return read_jsonl(w.path("d.jsonl"))

    def test_ac_p3_13_handoff_same_tick_ids_continue_across_days_shop_no_decay(self):
        shop_open = 1 + self.Q_TICKS
        day2_dock = shop_open + T["shop"]["max_ticks"]
        fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
              {"tick": day2_dock, "interact": True}, {"tick": day2_dock + 1, "interact": False}]
        with Workdir() as w:
            rows = self.run_day(w, 2, day2_dock + 1, fr)
            q1 = snap_at(rows, 1)
            self.assertEqual(q1["phase"], "quan")
            self.assertEqual([it["id"] for it in q1["stock"]], ["I1", "I2", "I3"])
            self.assertTrue(all(it["fresh"] == 100 for it in q1["stock"]))  # bàn giao cùng tick, chưa hao
            shop0, shop_end = snap_at(rows, shop_open), snap_at(rows, day2_dock)
            self.assertEqual(shop0["phase"], "shop")
            shop_last = [s for s in snapshots(rows) if s["phase"] == "shop"][-1]
            self.assertEqual(shop0["stock"], shop_last["stock"])  # Shop không hao
            q2 = snap_at(rows, day2_dock + 1)
            self.assertEqual((q2["day"], q2["phase"]), (2, "quan"))
            ids2 = [it["id"] for it in q2["stock"]]
            self.assertEqual(len(ids2), 3)
            self.assertTrue(all(int(i[1:]) > 3 for i in ids2), ids2)  # id tăng xuyên Ngày, không cấp lại
            self.assertNotEqual(shop_end["phase"], None)


if __name__ == "__main__":
    unittest.main()
