"""Test hộp đen luật gather của nhóm (lát 1: oxy/ngạt/Máu/giỏ; lát 2: hái/bắt cá/kho).

Chạy qua headless_cmd như test_smoke_p1.py; số liệu đọc từ game.contract.json.
Các giả định chưa có trong PRD-0 được ghi ở docs/clarify.md.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def g():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run(w, block, inputs=(), ticks=1, every=1, inv=None):
    sc = write_json(w.path("sc.json"), {"gather": block})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv:
        args += ["--inventory-out", inv]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def last(rows):
    return snapshots(rows)[-1]


class Oxygen(unittest.TestCase):
    def test_dive_and_surface_events(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 0], "vel": [0, 0]}, "random_fish": False},
                       [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=90)
            names = [e["name"] for e in events(rows) if e["name"] in ("dive", "surface")]
            self.assertEqual(names, ["dive", "surface"])
            self.assertGreater(events(rows, "dive")[0]["data"]["pos"][1], g()["surface_depth"])

    def test_oxygen_drains_underwater_and_refills_at_surface(self):
        t = g()
        omax = int(t["oxygen_max_s"] * 60)
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 5]}, "random_fish": False}, ticks=60)
            self.assertEqual(last(rows)["player"]["oxygen_ticks"], omax - 60)
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 0], "oxygen_ticks": 10}, "random_fish": False}, ticks=2)
            self.assertEqual(last(rows)["player"]["oxygen_ticks"], min(omax, 10 + 2 * t["oxygen_refill_per_tick"]))

    def test_oxygen_empty_then_choke_every_interval(self):
        t = g()
        n = t["choke_interval_ticks"]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [20, 5], "oxygen_ticks": 1}, "random_fish": False}, ticks=2 * n)
            self.assertEqual([e["tick"] for e in events(rows, "oxygen_empty")], [1])
            self.assertEqual([e["tick"] for e in events(rows, "choke")], [n, 2 * n])
            self.assertEqual(last(rows)["player"]["hp"], t["hp_max"] - 2)

    def test_faint_empties_hold_and_writes_empty_inventory(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            rows = run(w, {"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                           "hold": ["ca_loc", "bong_sung"], "random_fish": False}, ticks=10, inv=inv)
            self.assertEqual([e["name"] for e in events(rows)], ["choke", "faint", "gather_end"])
            end = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end, {"reason": "fainted", "inventory": {"items": {}}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(last(rows)["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Harvest(unittest.TestCase):
    def test_gather_node_then_wait_regrow(self):
        t = g()
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 0]}, "random_fish": False},
                       [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": 2, "interact": True}],
                       ticks=3)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1, "nút chưa mọc lại thì không hái được lần hai")
            self.assertEqual(ev[0]["data"]["node_id"], "N1")
            s = last(rows)
            self.assertEqual(s["hold"], ["bong_dien_dien"] * t["node_yield"])
            n1 = [n for n in s["nodes"] if n["id"] == "N1"][0]
            self.assertFalse(n1["ready"])
            self.assertEqual(n1["regrow_ticks"], int(t["regrow_s"] * 60) - 2)

    def test_node_regrown_event(self):
        with Workdir() as w:
            rows = run(w, {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [40, 0], "regrow_ticks": 3}],
                           "random_fish": False}, ticks=5)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "node_regrown")], [(3, {"node_id": "N1"})])

    def test_no_harvest_underwater(self):
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 1.5]}, "random_fish": False}, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])

    def test_nearest_tie_picks_smaller_id(self):
        with Workdir() as w:
            nodes = [{"id": "N10", "kind": "bong_sung", "pos": [41, 0]}, {"id": "N2", "kind": "bong_sung", "pos": [39, 0]}]
            rows = run(w, {"player": {"pos": [40, 0]}, "nodes": nodes, "random_fish": False}, [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")

    def test_hold_full_on_harvest(self):
        cap = g()["hold_capacity"]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [12, 0]}, "hold": ["ca_loc"] * cap, "random_fish": False},
                       [{"tick": 0, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(len(events(rows, "hold_full")), 1)
            self.assertTrue([n for n in last(rows)["nodes"] if n["id"] == "N1"][0]["ready"])


class Catch(unittest.TestCase):
    def test_catch_school_underwater(self):
        t = g()
        # v1.1: cá đầu ca được sinh ngẫu nhiên (lát 1), nên ghim đàn cá bằng scenario.
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [15, 5]}, "fish": fish}, [{"tick": 0, "catch": True}])
            ev = events(rows, "fish_caught")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"]["fish_id"], "F1")
            s = last(rows)
            self.assertEqual(s["hold"], ["ca_linh"] * t["fish_yield"]["ca_linh"])
            self.assertNotIn("F1", [f["id"] for f in s["fish"]])
            self.assertEqual(s["player"]["catch_cd_ticks"], int(t["catch_cooldown_s"] * 60))

    def test_catch_cooldown_blocks_second_catch(self):
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [20.5, 5]}]
            rows = run(w, {"player": {"pos": [20, 5]}, "fish": fish},
                       [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True}], ticks=3)
            self.assertEqual(len(events(rows, "fish_caught")), 1)

    def test_no_catch_at_surface(self):
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}]
            rows = run(w, {"player": {"pos": [20, 0]}, "fish": fish}, [{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [])

    def test_not_enough_room_for_school_is_hold_full(self):
        """v1.1 (spec gather A1): phải đủ chỗ cho CẢ đàn, thiếu chỗ ⇒ hold_full, không bắt.

        Luật v1.0 (nhặt được phần vừa chỗ) đã bị thay ở lattice 1.
        """
        cap = g()["hold_capacity"]
        # v1.1: ghim đàn cá (mặc định do lát 1 sinh) để kiểm giỏ đầy.
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]
        with Workdir() as w:
            rows = run(w, {"player": {"pos": [15, 5]}, "fish": fish, "hold": ["ca_loc"] * (cap - 1)},
                       [{"tick": 0, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(events(rows, "hold_full")), 1)
            self.assertEqual(last(rows)["hold_count"], cap - 1)

    def test_dock_after_catch_writes_inventory(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            run(w, {"player": {"pos": [2, 1]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [2, 2]}]},
                [{"tick": 0, "catch": True}, {"tick": 1, "interact": True}], ticks=5, inv=inv)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"ca_loc": 1}})


if __name__ == "__main__":
    unittest.main()
