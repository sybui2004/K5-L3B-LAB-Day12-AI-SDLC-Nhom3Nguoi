"""Test hộp đen mode `day`, Shop, pause (Test Contract v1.1, TICKET-02 mục 2 + 4). Chủ: TV2.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_day -v
"""

import json
import os
import unittest

from helpers import ROOT, Workdir, stock_counts, events, frames, read_jsonl, run_headless, snapshots, write_json

with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as _f:
    T = json.load(_f)["tuning"]
G_TICKS = int(T["gather"]["duration_s"] * 60)
Q_TICKS = int(T["quan"]["duration_s"] * 60)
SHOP = T["shop"]["max_ticks"]
DAY_TICKS = G_TICKS + Q_TICKS + SHOP  # 22.200
UP = T["shop"]["upgrades"]

# Ví dụ trong ticket 4.3: mở một Ngày đã có tiền và kho mang về; interact ở bến đóng ca sáng ngay (bước 0 -> tick 1).
DOCKED = {"day": {"money": 200, "earned": 200},
          "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
SHOP_OPEN = 1 + Q_TICKS  # tick quán đóng và Shop mở khi cập bến ở tick 1


def run_day(w, scenario=None, fr=(), ticks=None, days=None, seed=1, name="o", every=None):
    args = ["--mode", "day", "--seed", str(seed), "--ticks", str(ticks or DAY_TICKS * (days or 1)),
            "--out", w.path(f"{name}.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path(f"{name}.sc.json"), scenario)]
    if fr:
        args += ["--inputs", write_json(w.path(f"{name}.in.json"), frames(*fr))]
    if days is not None:
        args += ["--days", str(days)]
    if every is not None:
        args += ["--snapshot-every", str(every)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(f"{name}.jsonl")) if code == 0 else None)


def names(rows):
    return [(r["tick"], r["phase"], r["name"]) for r in rows if r["type"] == "event"]


class DayLoop(unittest.TestCase):
    def test_one_day_phase_order_and_end(self):
        with Workdir() as w:
            code, err, rows = run_day(w)
            self.assertEqual(code, 0, err)
            ev = [e for e in names(rows) if e[2] not in ("no_dish",)]
            self.assertEqual(ev, [
                (0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start"),
                (G_TICKS, "gather", "gather_end"), (G_TICKS, "quan", "phase_start"),
                (G_TICKS + Q_TICKS, "quan", "quan_end"), (G_TICKS + Q_TICKS, "shop", "phase_start"),
                (DAY_TICKS, "shop", "shop_end")])
            self.assertEqual((rows[0]["type"], rows[0]["tick"]), ("snapshot", 0))  # snapshot tick 0 trước (clarify #19)
            self.assertEqual([r["name"] for r in rows[1:4]], ["day_start", "day_plan", "phase_start"])
            plan = events(rows, "day_plan")[0]
            self.assertEqual(plan["day"], 1)
            self.assertEqual(plan["data"], {"dishes": T["day_plan"][0]["dishes"],
                                            "ingredients": T["day_plan"][0]["ingredients"]})
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "time"})
            end = rows[-1]
            self.assertEqual((end["type"], end["reason"], end["days_completed"], end["ticks"]),
                             ("end", "days_complete", 1, DAY_TICKS))

    def test_snapshot_fields_and_phase_change_snapshot(self):
        with Workdir() as w:
            code, err, rows = run_day(w)
            self.assertEqual(code, 0, err)
            snaps = snapshots(rows)
            for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                self.assertIn(key, snaps[0])
            at_quan = [s for s in snaps if s["tick"] == G_TICKS][0]
            self.assertEqual((at_quan["phase"], at_quan["phase_tick"]), ("quan", 0))
            at_shop = [s for s in snaps if s["tick"] == G_TICKS + Q_TICKS][0]
            self.assertEqual((at_shop["phase"], at_shop["phase_tick"], at_shop["time_left_ticks"]), ("shop", 0, SHOP))
            self.assertIn("stock", at_shop)

    def test_handoff_inventory_to_quan_and_plan_filter(self):
        """Kho bàn giao từ giỏ; khách Ngày 1 chỉ gọi món trong kế hoạch D1."""
        with Workdir() as w:
            code, err, rows = run_day(w, DOCKED, [{"tick": 0, "interact": True}], ticks=SHOP_OPEN)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            first_q = [s for s in snapshots(rows) if s["phase"] == "quan"][0]
            self.assertEqual(stock_counts(first_q["stock"]), {"bong_sung": 2, "ca_loc": 1})  # Đổi test (TICKET-03): kho/giữ chỗ là cá thể
            plan = set(T["day_plan"][0]["dishes"])
            self.assertTrue(events(rows, "customer_arrived"))
            for e in events(rows, "customer_arrived"):
                self.assertIn(e["data"]["dish_id"], plan)

    def test_money_carries_and_deterministic_two_days(self):
        with Workdir() as w:
            for i in (1, 2):
                code, err, _ = run_day(w, DOCKED, [{"tick": 0, "interact": True}], days=2, seed=5, name=f"o{i}")
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            rows = read_jsonl(w.path("o1.jsonl"))
            self.assertEqual([e["day"] for e in events(rows, "day_start")], [1, 2])
            self.assertEqual(rows[-1]["days_completed"], 2)
            self.assertEqual(rows[-1]["money"], 200)  # không ai phục vụ -> giữ nguyên tiền đầu kỳ


class Shop(unittest.TestCase):
    def test_buy_upgrade_applies_from_next_day(self):
        fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
              {"tick": SHOP_OPEN, "buy": "oxygen"}, {"tick": SHOP_OPEN + 1, "shop_done": True}]
        with Workdir() as w:
            code, err, rows = run_day(w, DOCKED, fr, days=2, ticks=SHOP_OPEN + 3, every=1)
            self.assertEqual(code, 0, err)
            price = UP["oxygen"][0]["price"]
            b = events(rows, "bought")
            self.assertEqual([(e["tick"], e["data"]) for e in b],
                             [(SHOP_OPEN + 1, {"upgrade": "oxygen", "level": 1, "price": price, "money": 200 - price})])
            shop_snap = [s for s in snapshots(rows) if s["tick"] == SHOP_OPEN + 1][0]
            self.assertEqual((shop_snap["upgrades"], shop_snap["active_upgrades"]), ({"oxygen": 1}, {}))
            self.assertEqual(shop_snap["earned"], 200)  # mua không trừ earned
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            self.assertEqual(events(rows, "shop_end")[0]["tick"], SHOP_OPEN + 2)
            day2 = [s for s in snapshots(rows) if s.get("day") == 2][0]
            self.assertEqual((day2["phase"], day2["phase_tick"]), ("gather", 0))
            self.assertEqual(day2["active_upgrades"], {"oxygen": 1})
            self.assertEqual(day2["player"]["oxygen_max_ticks"], int(UP["oxygen"][0]["oxygen_max_s"] * 60))

    def test_buy_failed_reasons(self):
        cases = [({"money": 0}, "hp", "funds"),
                 ({"money": 999, "earned": 999, "upgrades": {"hp": len(UP["hp"])}}, "hp", "max_level"),
                 ({"money": 999, "earned": 999}, "xyz", "unknown")]
        with Workdir() as w:
            for day, action, reason in cases:
                sc = {"day": day, "gather": {"random_fish": False}}
                fr = [{"tick": 0, "interact": True}, {"tick": SHOP_OPEN, "buy": action}]
                code, err, rows = run_day(w, sc, fr, ticks=SHOP_OPEN + 1)
                self.assertEqual(code, 0, err)
                self.assertEqual([e["data"] for e in events(rows, "buy_failed")],
                                 [{"action": action, "reason": reason}], reason)
                self.assertEqual(snapshots(rows)[-1]["money"], day["money"])

    def test_exact_price_can_buy(self):
        price = UP["hp"][0]["price"]
        sc = {"day": {"money": price, "earned": price}, "gather": {"random_fish": False}}
        fr = [{"tick": 0, "interact": True}, {"tick": SHOP_OPEN, "buy": "hp"}]
        with Workdir() as w:
            code, err, rows = run_day(w, sc, fr, ticks=SHOP_OPEN + 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "bought")[0]["data"]["money"], 0)

    def test_extension_buys_ignored_when_not_enabled(self):
        """Clarify #18: weapon/net/buy:<kind>/sell:<kind> khi chưa bật mở rộng -> bỏ qua, không event."""
        sc = {"day": {"money": 999, "earned": 999}, "gather": {"random_fish": False}}
        with Workdir() as w:
            for i, action in enumerate(("weapon", "net", "buy:ca_loc", "sell:ca_loc")):
                fr = [{"tick": 0, "interact": True}, {"tick": SHOP_OPEN, "buy": action}]
                code, err, rows = run_day(w, sc, fr, ticks=SHOP_OPEN + 1, name=f"e{i}")
                self.assertEqual(code, 0, err)
                self.assertEqual(events(rows, "bought") + events(rows, "buy_failed"), [], action)

    def test_buy_and_shop_done_same_frame(self):
        fr = [{"tick": 0, "interact": True}, {"tick": SHOP_OPEN, "buy": "oxygen", "shop_done": True}]
        with Workdir() as w:
            code, err, rows = run_day(w, DOCKED, fr, ticks=SHOP_OPEN + 1)
            self.assertEqual(code, 0, err)
            shop = [(e["tick"], e["name"]) for e in events(rows) if e["phase"] == "shop"]
            self.assertEqual(shop, [(SHOP_OPEN, "phase_start"), (SHOP_OPEN + 1, "bought"), (SHOP_OPEN + 1, "shop_end")])
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})

    def test_shop_snapshot_upgrades_and_day_result(self):
        with Workdir() as w:
            code, err, rows = run_day(w, DOCKED, [{"tick": 0, "interact": True}], ticks=SHOP_OPEN)
            self.assertEqual(code, 0, err)
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["phase"], "shop")
            self.assertEqual(snap["upgrades"], {})
            self.assertEqual(set(snap["day_result"]), {"served", "left", "money", "tips", "reputation_delta", "best_dish"})

    def test_buy_outside_shop_ignored(self):
        fr = [{"tick": 3, "buy": "hp"}]
        with Workdir() as w:
            code, err, rows = run_day(w, {"day": {"money": 999, "earned": 999}}, fr, ticks=10)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "bought") + events(rows, "buy_failed"), [])


class Pause(unittest.TestCase):
    def test_pause_freezes_timers_quan(self):
        fr = [{"tick": 5, "pause": True}, {"tick": 6, "pause": False}, {"tick": 10, "pause": True}]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"random_customers": False}})
            inp = write_json(w.path("in.json"), frames(*fr))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(Q_TICKS + 100), "--scenario", sc,
                                     "--inputs", inp, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows) if e["name"] in ("paused", "resumed")],
                             [(6, "paused"), (11, "resumed")])
            paused = [s for s in snapshots(rows) if 6 <= s["tick"] <= 10]
            self.assertTrue(all(s["state"] == "paused" for s in paused))
            self.assertEqual(len({s["time_left_ticks"] for s in paused}), 1)   # đồng hồ đứng yên
            self.assertEqual(len({s["sim_tick"] for s in paused}), 1)
            end = events(rows, "quan_end")[0]
            self.assertEqual(end["tick"], Q_TICKS + 5)  # bước 5 vào pause + bước 6..9 đứng yên; bước 10 resume và chạy luôn
            self.assertEqual(rows[-1]["sim_tick"], Q_TICKS)

    def test_actions_ignored_while_paused(self):
        sc = {"day": {}, "gather": {"random_fish": False}}
        fr = [{"tick": 0, "pause": True}, {"tick": 1, "pause": False, "interact": True}, {"tick": 2, "interact": False}]
        with Workdir() as w:
            code, err, rows = run_day(w, sc, fr, ticks=5)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "gather_end"), [])  # interact trong lúc pause bị bỏ qua


class BadInput(unittest.TestCase):
    def test_days_flag(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for args in (["--mode", "day", "--days", "0"], ["--mode", "day", "--days", "6"],
                         ["--mode", "gather", "--days", "1"]):
                self.assertEqual(run_headless(*args, "--seed", "1", "--ticks", "0", "--out", out)[0], 2, args)

    def test_day_scenario_conflicts(self):
        bad = [
            {"quan": {"stock": {"ca_loc": 1}}},
            {"quan": {"reputation": 3}},
            {"day": {"money": 10}},                                   # có tiền mà không khai earned
            {"day": {"money": 10, "earned": 5}},                      # money > earned
            {"day": {"upgrades": {"oxygen": 3}}},
            {"day": {"upgrades": {"jetpack": 1}}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 1}}]}},
            {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
            {"day": {"lives": 3}},
        ]
        with Workdir() as w:
            for sc in bad:
                code, _, _ = run_day(w, sc, ticks=0)
                self.assertEqual(code, 2, sc)

    def test_day_plan_override(self):
        sc = {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 2}}]}}
        with Workdir() as w:
            code, err, rows = run_day(w, sc, ticks=0)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "day_plan")[0]["data"],
                             {"dishes": {"goi_bong_sung": 2}, "ingredients": {"bong_sung": 4}})


if __name__ == "__main__":
    unittest.main()
