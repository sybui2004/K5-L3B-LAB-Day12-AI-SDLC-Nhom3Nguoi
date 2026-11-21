"""Test lát A (Ticket-03): file kho v1.2, contract `freshness`, scenario cá thể, bàn giao không làm tròn."""

import copy
import json
import os
import unittest
from fractions import Fraction

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.inventory import read_inventory, write_inventory
from helpers import Workdir, events, frames, hold_items, read_jsonl, run_headless, snapshots, stock_items, write_json

CONTRACT = load_contract()
TUNING = CONTRACT["tuning"]
DOCK = frames({"tick": 0, "interact": True})


def item(iid="I1", kind="ca_linh", fresh=100):
    return {"id": iid, "kind": kind, "fresh": fresh}


class FileFormat(unittest.TestCase):
    def test_round_trip_keeps_id_kind_and_fresh(self):
        items = [item("I2", "ca_loc", 29.999), item("I1", "bong_sung", 30), item("I3", "keo_neo", Fraction(1199, 12))]
        with Workdir() as w:
            p = w.path("kho.json")
            write_inventory(p, items, "1.2")
            back = {it["id"]: it for it in read_inventory(p, "1.2")}
        self.assertEqual({k: v["kind"] for k, v in back.items()}, {"I1": "bong_sung", "I2": "ca_loc", "I3": "keo_neo"})
        self.assertEqual(float(back["I2"]["fresh"]), 29.999)
        self.assertEqual(float(back["I1"]["fresh"]), 30.0)
        self.assertEqual(float(back["I3"]["fresh"]), float(Fraction(1199, 12)))

    def test_written_sorted_by_id_and_empty_shape(self):
        with Workdir() as w:
            p = w.path("kho.json")
            write_inventory(p, [item("I10"), item("I2")], "1.2")
            with open(p, encoding="utf-8") as f:
                self.assertEqual([it["id"] for it in json.load(f)["items"]], ["I2", "I10"])
            write_inventory(p, [], "1.2")
            with open(p, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_v11_count_format_still_supported_by_adapter(self):
        with Workdir() as w:
            p = w.path("kho.json")
            write_inventory(p, {"ca_loc": 2, "bong_sung": 0}, "1.1")
            self.assertEqual(read_inventory(p, "1.1"), {"ca_loc": 2})

    def test_bad_files_exit_2_before_output(self):
        bad = [{"items": {"ca_loc": 2}}, {}, {"items": [item()], "x": 1}, {"items": [item(kind="ca_map")]},
               {"items": [item("I1"), item("I1")]}, {"items": [item("")]}, {"items": [item(fresh=-1)]},
               {"items": [item(fresh=100.5)]}, {"items": [item(fresh=float("nan"))]}, {"items": [item(fresh=True)]},
               {"items": [{"id": "I1", "kind": "ca_loc"}]}]
        for body in bad:
            with self.subTest(body=body), Workdir() as w:
                inv, out = write_json(w.path("kho.json"), body), w.path("q.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))


class WriteOnGatherEnd(unittest.TestCase):
    def _gather(self, w, block, ticks, inv, inputs=DOCK):
        sc = write_json(w.path("sc.json"), {"gather": block})
        fr = write_json(w.path("in.json"), inputs)
        code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc, "--inputs", fr,
                                 "--inventory-out", inv, "--out", w.path("g.jsonl"))
        self.assertEqual(code, 0, err)

    def test_tick_limit_leaves_target_untouched(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            self._gather(w, {"player": {"pos": [20, 0]}, "random_fish": False}, 3, inv, frames({"tick": 0}))
            self.assertFalse(os.path.exists(inv))
            with open(inv, "w", encoding="utf-8") as f:
                f.write("giu nguyen")
            self._gather(w, {"player": {"pos": [20, 0]}, "random_fish": False}, 3, inv, frames({"tick": 0}))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(f.read(), "giu nguyen")

    def test_faint_writes_empty_inventory(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            block = {"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                     "hold": hold_items(["ca_loc"]), "random_fish": False}
            self._gather(w, block, 5, inv, frames({"tick": 0}))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_handoff_keeps_id_kind_fresh(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            self._gather(w, {"hold": [item()], "random_fish": False, "monsters": []}, 600, inv)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)["items"]
            self.assertEqual((saved[0]["id"], saved[0]["kind"]), ("I1", "ca_linh"))
            self.assertAlmostEqual(saved[0]["fresh"], 100 - 1 / 120, places=9)
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", out)
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(out))[0]["stock"]
            self.assertEqual(stock, [{"id": "I1", "kind": "ca_linh", "fresh": round(100 - 1 / 120, 3)}])


class ContractV12(unittest.TestCase):
    def test_manifest(self):
        self.assertIn(CONTRACT["contract_version"], ("1.2", "1.3"))
        self.assertEqual(TUNING["freshness"],
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})

    def test_bad_freshness_rejected(self):
        for patch in ({"initial": 101}, {"spoiled_below": 0}, {"spoiled_below": 100}, {"gather_decay_per_s": 0},
                      {"quan_decay_per_s": "x"}, {"initial": True}):
            with self.subTest(patch=patch):
                t = copy.deepcopy(TUNING)
                t["freshness"].update(patch)
                with self.assertRaises(BadInput):
                    validate_tuning(t)


class ScenarioV12(unittest.TestCase):
    def _code(self, mode, block):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {mode: block})
            return run_headless("--mode", mode, "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", w.path("o.jsonl"))[0]

    def test_count_forms_rejected(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        cases = [("gather", {"hold": ["ca_loc"]}), ("gather", {"hold": {"ca_loc": 1}}), ("quan", {"stock": {"ca_loc": 1}}),
                 ("quan", {"stock": stock_items({"ca_loc": 1}), "customers": [dict(customer, reserved={"ca_loc": 1})]})]
        for mode, block in cases:
            with self.subTest(block=block):
                self.assertEqual(self._code(mode, block), 2)

    def test_bad_items_rejected(self):
        for raw in ([item("I1"), item("I1")], [item("")], [item(kind="ca_map")], [item(fresh=120)]):
            for mode, key in (("gather", "hold"), ("quan", "stock")):
                with self.subTest(raw=raw, key=key):
                    self.assertEqual(self._code(mode, {key: raw}), 2)

    def test_valid_items_accepted(self):
        self.assertEqual(self._code("gather", {"hold": [item(fresh=29.5)]}), 0)
        self.assertEqual(self._code("quan", {"stock": stock_items({"ca_loc": 1})}), 0)


class DayHandoff(unittest.TestCase):
    def test_handoff_does_not_round_item_back_above_threshold(self):
        """Hàng vừa ươn ở giỏ (29.9997) không được làm tròn thành 30 rồi "ươn lần nữa" trong kho quán."""
        block = {"gather": {"hold": [item("I1", "ca_loc", 30.008)], "random_fish": False, "monsters": []}}
        with Workdir() as w:
            sc, fr = write_json(w.path("sc.json"), block), write_json(w.path("in.json"), DOCK)
            out = w.path("d.jsonl")
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "8", "--scenario", sc,
                                     "--inputs", fr, "--out", out)
            self.assertEqual(code, 0, err)
            spoiled = [e["data"]["location"] for e in events(read_jsonl(out), "spoiled")]
        self.assertEqual(spoiled, ["hold"])


if __name__ == "__main__":
    unittest.main()
