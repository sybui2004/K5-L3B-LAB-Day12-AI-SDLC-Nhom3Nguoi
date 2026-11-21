"""Bộ test hộp đen Phase 3 gather (AC-P3-05, AC-P3-06, AC-P3-07 và tính tất định).

Chạy qua headless (--mode gather) theo Test Contract v1.2 (Spec Phase 3).
Dựa trên docs/spec/phase-3/gather.md, docs/spec/phase-3/README.md và docs/adr/0001-kho-ca-the-v1.2.md.
Mọi số liệu đọc từ game.contract.json khi có; fallback sang hằng số Phase 3 (0.5/s, spoiled_below=30)
cho tới khi TV3 thêm khối tuning.freshness vào contract.
"""

import json
import math
import os
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

from helpers import (
    Workdir,
    close,
    dist,
    events,
    frames,
    headless_cmd,
    read_jsonl,
    snapshots,
    write_json,
)


def g():
    """Đọc cấu hình gather từ game.contract.json."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def get_freshness_config():
    """Đọc cấu hình độ tươi từ contract nếu có.

    LƯU Ý: game.contract.json hiện tại chưa có khóa freshness (do TV3 thêm sau trong Lát A/D).
    Test được phép dùng hằng số spec Phase 3:
      - gather_decay_per_s = 0.5 (tương đương 0.5/60 = 1/120 mỗi tick)
      - spoiled_below = 30
      - initial = 100
    theo docs/spec/phase-3/gather.md mục 2 và README.md mục 2 (AC-P3-01).
    """
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        contract = json.load(f)
    freshness = contract.get("tuning", {}).get("freshness", {})
    return {
        "gather_decay_per_s": freshness.get("gather_decay_per_s", 0.5),
        "spoiled_below": freshness.get("spoiled_below", 30),
        "initial": freshness.get("initial", 100),
    }


def headless_cmd_gather():
    cmd = headless_cmd()
    if sys.platform == "win32" and not shutil.which(cmd[0]):
        return [sys.executable, *cmd[1:]]
    return cmd


def run_headless_gather(*args, cwd=ROOT):
    p = subprocess.run([*headless_cmd_gather(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def run(w, block, inputs=(), ticks=1, every=1, inv=None, seed="1"):
    sc = write_json(w.path("sc.json"), {"gather": block})
    args = [
        "--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
        "--snapshot-every", str(every), "--out", w.path("o.jsonl")
    ]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv:
        args += ["--inventory-out", inv]
    code, err = run_headless_gather(*args)
    assert code == 0, f"run_headless_gather thất bại (exit code {code}): {err}"
    return read_jsonl(w.path("o.jsonl"))


class TestP3Gather(unittest.TestCase):
    """Test hộp đen cho Phase 3 Gather: AC-P3-05, AC-P3-06, AC-P3-07 và tính tất định."""

    def test_ac_p3_05_harvest_freshness_and_decay(self):
        """AC-P3-05: Hàng mới fresh=100, hao từ bước sau; giỏ -0.5/s (-1/120 mỗi tick).

        Spec gather.md mục 6:
        Hái ở bước k => snapshot tick k có fresh 100, tick k+1 có 99.992.
        """
        t = g()
        nodes_by_id = {node["id"]: node for node in t["nodes"]}
        n1 = nodes_by_id["N1"]  # bong_dien_dien tại [12, 0]

        with Workdir() as w:
            block = {
                "player": {"pos": list(n1["pos"])},
                "random_fish": False,
                "monsters": [],
            }
            # Hái ở tick 0 (bước 1)
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2, every=1)

            ev_gather = events(rows, "gather")
            self.assertEqual(len(ev_gather), 1, "Phải phát sự kiện gather khi hái nút N1")
            self.assertEqual(ev_gather[0]["data"]["node_id"], "N1")

            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertIn(1, snaps, "Phải có snapshot tại tick 1")
            self.assertIn(2, snaps, "Phải có snapshot tại tick 2")

            # Snapshot tick 1 (vừa hái xong trong bước này, chưa hao): fresh = 100
            s1_hold = snaps[1]["hold"]
            self.assertEqual(len(s1_hold), 1)
            self.assertEqual(s1_hold[0]["kind"], n1["kind"])
            self.assertAlmostEqual(s1_hold[0]["fresh"], 100.0, places=3)

            # Snapshot tick 2 (đã có trước bước 2, hao 1/120 = 0.008333...): fresh = 99.992
            s2_hold = snaps[2]["hold"]
            self.assertEqual(len(s2_hold), 1)
            self.assertEqual(s2_hold[0]["kind"], n1["kind"])
            self.assertAlmostEqual(s2_hold[0]["fresh"], 99.992, places=3)

    def test_ac_p3_05_catch_school_sequential_ids(self):
        """AC-P3-05: Bắt đàn cá linh 3 con => id liên tiếp, tiếp sau id lớn nhất trong scenario.

        Spec gather.md mục 1 & 6:
        - Bắt đàn n con => gọi new_item n lần theo thứ tự, mỗi con fresh = 100, id I<n>.
        - Scenario có id sẵn I5 => bắt đàn 3 con cá linh sinh ra I6, I7, I8 theo thứ tự vào giỏ.
        """
        t = g()
        ca_linh_yield = t["fish_yield"]["ca_linh"]
        self.assertEqual(ca_linh_yield, 3, "fish_yield của ca_linh phải là 3 theo contract")

        with Workdir() as w:
            block = {
                "player": {"pos": [20.0, 5.0]},
                "hold": [{"id": "I5", "kind": "bong_dien_dien", "fresh": 90}],
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20.0, 5.0]}],
                "monsters": [],
            }
            inputs = [{"tick": 0, "catch": True}]
            rows = run(w, block, inputs=inputs, ticks=1, every=1)

            ev_catch = events(rows, "fish_caught")
            self.assertEqual(len(ev_catch), 1, "Phải bắt được đàn cá linh F1")
            self.assertEqual(ev_catch[0]["data"]["fish_id"], "F1")
            self.assertEqual(ev_catch[0]["data"]["count"], ca_linh_yield)

            s_end = snapshots(rows)[-1]
            hold = s_end["hold"]
            # 1 ban đầu + 3 con mới = 4
            self.assertEqual(len(hold), 4)

            # Id phải nối tiếp id lớn nhất có trong scenario (I5) => I6, I7, I8
            item_ids = [item["id"] for item in hold]
            self.assertEqual(item_ids, ["I5", "I6", "I7", "I8"], "Các id phải liên tiếp sau id lớn nhất")

            # 3 con cá mới đều có kind 'ca_linh' và fresh = 100
            for item in hold[1:]:
                self.assertEqual(item["kind"], "ca_linh")
                self.assertAlmostEqual(item["fresh"], 100.0, places=3)

    def test_ac_p3_06_spoiled_sample_scenario_tick_1(self):
        """AC-P3-06: Mẫu đề {"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}

        chạy 1 bước không input => sự kiện spoiled ở tick 1 đúng JSON mẫu:
        {"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}
        """
        with Workdir() as w:
            block = {
                "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                "random_fish": False,
                "monsters": [],
            }
            rows = run(w, block, ticks=1)

            ev_spoiled = events(rows, "spoiled")
            self.assertEqual(len(ev_spoiled), 1, "Phải phát đúng một sự kiện spoiled ở tick 1")

            target_ev = ev_spoiled[0]
            self.assertEqual(target_ev.get("type"), "event")
            self.assertEqual(target_ev.get("tick"), 1)
            self.assertEqual(target_ev.get("phase"), "gather")
            self.assertEqual(target_ev.get("name"), "spoiled")
            self.assertEqual(target_ev.get("data"), {"item_id": "I1", "kind": "ca_linh", "location": "hold"})

    def test_ac_p3_06_spoiled_fresh_30_01_at_tick_2(self):
        """AC-P3-06: fresh 30.01 ươn ở bước thứ 2.

        Spec gather.md mục 6:
        30.01 - 1/120 = 30.00167 >= 30 (bước 1 chưa ươn)
        30.00167 - 1/120 = 29.99333 < 30 (bước 2 ươn => phát spoiled tại tick 2).
        """
        with Workdir() as w:
            block = {
                "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30.01}],
                "random_fish": False,
                "monsters": [],
            }
            rows = run(w, block, ticks=2)

            ev_spoiled = events(rows, "spoiled")
            self.assertEqual(len(ev_spoiled), 1, "Chỉ được phát spoiled đúng một lần khi qua ngưỡng")
            self.assertEqual(ev_spoiled[0]["tick"], 2, "fresh 30.01 phải ươn ở bước thứ 2 (tick 2)")
            self.assertEqual(ev_spoiled[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})

    def test_ac_p3_06_spoiled_multiple_items_sorted_by_id(self):
        """AC-P3-06: Hai cá thể qua ngưỡng cùng bước => hai spoiled theo id; đã ươn không phát lại.

        Spec gather.md mục 2 & 6:
        Mỗi cá thể vừa qua ngưỡng => spoiled theo id, đúng một lần (đã ươn thì không phát lại).
        """
        with Workdir() as w:
            block = {
                "hold": [
                    {"id": "I3", "kind": "ca_linh", "fresh": 30},
                    {"id": "I1", "kind": "bong_sung", "fresh": 30},
                ],
                "random_fish": False,
                "monsters": [],
            }
            rows = run(w, block, ticks=2)

            # Ở tick 1: Cả I3 và I1 đều qua ngưỡng < 30, phát theo thứ tự id: I1 trước, I3 sau
            ev_tick1 = [e for e in events(rows, "spoiled") if e["tick"] == 1]
            self.assertEqual(len(ev_tick1), 2, "Cả hai cá thể phải phát sự kiện spoiled ở tick 1")
            self.assertEqual(ev_tick1[0]["data"]["item_id"], "I1")
            self.assertEqual(ev_tick1[0]["data"]["kind"], "bong_sung")
            self.assertEqual(ev_tick1[0]["data"]["location"], "hold")
            self.assertEqual(ev_tick1[1]["data"]["item_id"], "I3")
            self.assertEqual(ev_tick1[1]["data"]["kind"], "ca_linh")
            self.assertEqual(ev_tick1[1]["data"]["location"], "hold")

            # Ở tick 2: Đã ươn từ tick 1 thì không được phát lại
            ev_tick2 = [e for e in events(rows, "spoiled") if e["tick"] == 2]
            self.assertEqual(len(ev_tick2), 0, "Cá thể đã ươn không được phát lại sự kiện spoiled")

    def test_ac_p3_07_monster_hit_lifo_lost(self):
        """AC-P3-07: Bị chạm với giỏ I1..I5 => lost = [I5, I4] theo LIFO.

        Spec gather.md mục 3 & 6:
        Bị chạm: bỏ floor(len(hold) * loss_ratio) cá thể từ cuối list;
        lost = mảng cá thể theo thứ tự bỏ (mới nhất trước, LIFO).
        Giỏ ban đầu [I1..I5] (len 5, loss_ratio 0.5 => floor(2.5)=2) => lost = [I5, I4].
        """
        initial_hold = [
            {"id": "I1", "kind": "ca_linh", "fresh": 80},
            {"id": "I2", "kind": "ca_loc", "fresh": 80},
            {"id": "I3", "kind": "ca_keo", "fresh": 80},
            {"id": "I4", "kind": "bong_dien_dien", "fresh": 80},
            {"id": "I5", "kind": "bong_sung", "fresh": 80},
        ]

        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 3, "invuln_ticks": 0},
                "hold": list(initial_hold),
                "random_fish": False,
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 20.5],
                    "waypoints": [[60.0, 20.5], [64.0, 20.5]],
                    "target_idx": 1,
                    "state": "patrol",
                }],
            }
            rows = run(w, block, ticks=1)

            ev_hit = events(rows, "monster_hit")
            self.assertEqual(len(ev_hit), 1, "Phải phát đúng một sự kiện monster_hit")
            hit_data = ev_hit[0]["data"]
            self.assertEqual(hit_data["monster_id"], "M1")
            self.assertEqual(hit_data["hp"], 2)

            lost = hit_data["lost"]
            self.assertEqual(len(lost), 2, "Phải làm rơi 2 món (floor(5 * 0.5))")
            # Thứ tự LIFO: mới nhất (cuối giỏ) trước => I5, rồi I4
            lost_ids = [item["id"] for item in lost]
            self.assertEqual(lost_ids, ["I5", "I4"], "lost phải là mảng cá thể theo thứ tự bỏ LIFO [I5, I4]")
            self.assertEqual(lost[0]["kind"], "bong_sung")
            self.assertEqual(lost[1]["kind"], "bong_dien_dien")

            # Snapshot giỏ còn lại 3 cá thể: [I1, I2, I3]
            s_end = snapshots(rows)[-1]
            remaining_ids = [item["id"] for item in s_end["hold"]]
            self.assertEqual(remaining_ids, ["I1", "I2", "I3"])

    def test_ac_p3_07_faint_lifo_all_lost_empty_inventory(self):
        """AC-P3-07: Ngất giỏ 3 món => faint.lost 3 cá thể LIFO, gather_end.inventory = {"items": []}.

        Spec gather.md mục 3 & 6:
        Ngất: bỏ toàn bộ phần còn lại theo LIFO; faint.lost = mảng đó;
        rồi gather_end(fainted) với inventory: {"items": []}.
        """
        initial_hold = [
            {"id": "I1", "kind": "ca_linh", "fresh": 90},
            {"id": "I2", "kind": "bong_dien_dien", "fresh": 90},
            {"id": "I3", "kind": "ca_loc", "fresh": 90},
        ]

        with Workdir() as w:
            inv_file = w.path("inv.json")
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 1, "invuln_ticks": 0},
                "hold": list(initial_hold),
                "random_fish": False,
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 20.5],
                    "waypoints": [[60.0, 20.5], [64.0, 20.5]],
                    "target_idx": 1,
                    "state": "patrol",
                }],
            }
            rows = run(w, block, ticks=1, inv=inv_file)

            ev_faint = events(rows, "faint")
            self.assertEqual(len(ev_faint), 1, "Phải phát sự kiện faint khi hp về 0")
            faint_data = ev_faint[0]["data"]
            self.assertEqual(faint_data["hp"], 0)
            self.assertEqual(faint_data.get("cause"), "monster")

            # Toàn bộ 3 món bị mất theo LIFO: I3, I2, I1
            lost = faint_data["lost"]
            self.assertEqual(len(lost), 3)
            lost_ids = [item["id"] for item in lost]
            self.assertEqual(lost_ids, ["I3", "I2", "I1"], "faint.lost phải chứa toàn bộ cá thể theo thứ tự LIFO")

            # gather_end(fainted) với kho rỗng schema v1.2: {"items": []}
            ev_end = events(rows, "gather_end")
            self.assertEqual(len(ev_end), 1)
            self.assertEqual(ev_end[0]["data"]["reason"], "fainted")
            self.assertEqual(ev_end[0]["data"]["inventory"], {"items": []})

            # File kho v1.2: AC-P3-03 (TV3, lát A), kiểm riêng khi bật manifest 1.2

    def test_determinism_headless_seed_1(self):
        """Test tất định: headless gather seed 1 chạy 2 lần, so nhị phân file output phải giống từng byte."""
        with Workdir() as w:
            out1 = w.path("out1.jsonl")
            out2 = w.path("out2.jsonl")
            code1, err1 = run_headless_gather("--mode", "gather", "--seed", "1", "--ticks", "120", "--out", out1)
            self.assertEqual(code1, 0, f"Lần chạy 1 thất bại: {err1}")
            code2, err2 = run_headless_gather("--mode", "gather", "--seed", "1", "--ticks", "120", "--out", out2)
            self.assertEqual(code2, 0, f"Lần chạy 2 thất bại: {err2}")

            with open(out1, "rb") as f1, open(out2, "rb") as f2:
                data1 = f1.read()
                data2 = f2.read()
            self.assertEqual(data1, data2, "Hai lần chạy cùng seed 1 phải giống nhau từng byte")


if __name__ == "__main__":
    unittest.main()
