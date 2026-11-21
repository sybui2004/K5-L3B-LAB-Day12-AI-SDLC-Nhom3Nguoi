"""Bộ test hộp đen Phase 2 gather (AC-P2-02..09 và tính tất định).

Chạy qua headless (--mode gather) theo Test Contract v1.1.
Mọi số liệu (fish_yield, nodes, fish_speed, monsters...) đọc từ game.contract.json, không hard-code.
Dựa trên docs/spec/phase-2/gather.md (mục 0, A, B, C) và docs/spec/phase-2/contract-v1.1.md.
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
from helpers import hold_items, stock_counts, stock_items


def g():
    """Đọc cấu hình gather từ game.contract.json v1.1."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


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


class TestP2Gather(unittest.TestCase):
    """Test hộp đen cho Phase 2 Gather: AC-P2-02..09 và tính tất định."""

    def test_ac_p2_02_gather_standard_numbers(self):
        """AC-P2-02: Gather số chuẩn: N1–N6, fish_yield 3 loài (cá kèo 2), oxy/ngạt/hái như v1.0.

        Spec C: N5/N6 hái ra keo_neo; cá kèo cho 2.
        Kho/scenario nhận 6 loại. Cần đủ chỗ cho cả đàn (cá kèo 2 ô).
        """
        t = g()
        nodes_by_id = {node["id"]: node for node in t["nodes"]}
        n5 = nodes_by_id["N5"]
        n6 = nodes_by_id["N6"]
        self.assertEqual(n5["kind"], "keo_neo")
        self.assertEqual(n6["kind"], "keo_neo")

        ca_keo_yield = t["fish_yield"]["ca_keo"]
        self.assertEqual(ca_keo_yield, 2)
        node_yield = t["node_yield"]

        # Nhánh 1: Hái nút N5 tại vị trí [76, 0] ra keo_neo
        with Workdir() as w:
            block = {
                "player": {"pos": list(n5["pos"])},
                "random_fish": False,
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            ev_gather = events(rows, "gather")
            self.assertEqual(len(ev_gather), 1, "Phải phát sự kiện gather khi hái nút N5")
            self.assertEqual(ev_gather[0]["data"]["node_id"], "N5")

            s_end = snapshots(rows)[-1]
            # Đổi test (P3 lát B): hold là mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ.
            self.assertEqual([it["kind"] for it in s_end["hold"]], ["keo_neo"] * node_yield)

        # Nhánh 2: Bắt cá kèo cho đúng 2 cá
        with Workdir() as w:
            block = {
                "player": {"pos": [20.0, 5.0]},
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_keo", "pos": [20.0, 5.0]}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            inputs = [{"tick": 0, "catch": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            ev_catch = events(rows, "fish_caught")
            self.assertEqual(len(ev_catch), 1, "Phải bắt được cá kèo F1")
            self.assertEqual(ev_catch[0]["data"]["fish_id"], "F1")
            self.assertEqual(ev_catch[0]["data"]["count"], ca_keo_yield)

            s_end = snapshots(rows)[-1]
            # Đổi test (P3 lát B): hold là mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ.
            self.assertEqual([it["kind"] for it in s_end["hold"]], ["ca_keo"] * ca_keo_yield)

        # Nhánh 3: Thiếu chỗ cho cả đàn (còn 1 chỗ trống mà cá kèo cần 2) => hold_full, không bắt
        cap = t["hold_capacity"]
        with Workdir() as w:
            block = {
                "player": {"pos": [20.0, 5.0]},
                "hold": hold_items(["ca_loc"] * (cap - 1)),
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_keo", "pos": [20.0, 5.0]}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            inputs = [{"tick": 0, "catch": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            self.assertEqual(events(rows, "fish_caught"), [], "Thiếu chỗ cho cả đàn không được bắt")
            self.assertEqual(len(events(rows, "hold_full")), 1)

    def test_ac_p2_03_fish_swimming_and_bounds(self):
        """AC-P2-03: Cá bơi 1.5 m/s, miền x [4,96], dải d theo loài, đổi hướng theo seed, phản xạ mép.

        Spec A2 & C: 1 đàn bơi 120 bước => quãng = 120 * 1.5 / 60 = 3 m; phản xạ ở x = 96.
        """
        t = g()
        fish_speed = t["fish_speed"]
        turn_ticks = t["fish_turn_ticks"]
        fish_x_bounds = t["fish_x"]
        fish_depths = t["fish_depths"]

        # Nhánh 1: Cá bơi trong 120 bước không chạm mép đi đúng 120 * fish_speed / 60 = 3.0 m
        expected_dist = turn_ticks * (fish_speed / 60.0)
        with Workdir() as w:
            start_pos = [50.0, 15.0]
            block = {
                "random_fish": True,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": list(start_pos), "heading_deg": 0.0, "age_ticks": 0}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            rows = run(w, block, ticks=turn_ticks)

            s_end = snapshots(rows)[-1]
            fish_f1 = [f for f in s_end["fish"] if f["id"] == "F1"][0]
            self.assertEqual(fish_f1["age_ticks"], turn_ticks)

            traveled = dist(start_pos, fish_f1["pos"])
            self.assertTrue(
                close(traveled, expected_dist, tol=0.05),
                f"Quãng đường bơi trong {turn_ticks} bước phải là ~{expected_dist} m, thực tế {traveled}",
            )

        # Nhánh 2: Phản xạ mép phải x = 96 (không vượt quá bounds)
        with Workdir() as w:
            near_edge_pos = [fish_x_bounds[1] - 0.5, 15.0]
            block = {
                "random_fish": True,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": list(near_edge_pos), "heading_deg": 0.0, "age_ticks": 0}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            rows = run(w, block, ticks=60)

            for s in snapshots(rows):
                for f in s["fish"]:
                    if f["id"] == "F1":
                        self.assertGreaterEqual(f["pos"][0], fish_x_bounds[0] - 1e-4)
                        self.assertLessEqual(f["pos"][0], fish_x_bounds[1] + 1e-4)
                        self.assertGreaterEqual(f["pos"][1], fish_depths[f["kind"]][0] - 1e-4)
                        self.assertLessEqual(f["pos"][1], fish_depths[f["kind"]][1] + 1e-4)

    def test_ac_p2_04_fish_initial_and_spawning(self):
        """AC-P2-04: Đầu ca 8 đàn ở 8 điểm khác nhau; sinh tối đa 1 đàn ở phase_tick = 360k; fish_spawned.

        Spec A3 & C: seed 1 có 8 đàn ở tick 0, các vị trí khác nhau; fish_spawned chỉ ở phase_tick chia hết 360; <= 12.
        """
        t = g()
        fish_initial = t["fish_initial"]
        spawn_ticks = t["fish_spawn_ticks"]
        fish_max = t["fish_max"]

        with Workdir() as w:
            # Chạy seed 1 tự nhiên (random_fish mặc định bật, không ghi đè đàn cá)
            block = {
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            rows = run(w, block, ticks=spawn_ticks + 10, seed="1")

            snaps = snapshots(rows)
            s0 = snaps[0]

            # Kiểm tra đầu ca có đúng fish_initial đàn ở các vị trí hình học khác nhau
            self.assertEqual(len(s0["fish"]), fish_initial)
            positions = [tuple(f["pos"]) for f in s0["fish"]]
            self.assertEqual(len(set(positions)), fish_initial, "8 đàn đầu ca phải ở 8 vị trí khác nhau")

            # Sự kiện fish_spawned chỉ phát ở phase_tick chia hết cho spawn_ticks (360)
            ev_spawn = events(rows, "fish_spawned")
            for ev in ev_spawn:
                self.assertEqual(ev["tick"] % spawn_ticks, 0, f"fish_spawned ở tick {ev['tick']} không chia hết cho {spawn_ticks}")
                self.assertIn("id", ev["data"])
                self.assertIn("kind", ev["data"])
                self.assertIn("pos", ev["data"])

            # Số đàn cá ở mọi thời điểm không vượt quá fish_max (12)
            for s in snaps:
                self.assertLessEqual(len(s["fish"]), fish_max)

    def test_ac_p2_05_catch_before_fish_moves(self):
        """AC-P2-05: Bắt cá xét theo vị trí cá TRƯỚC khi bơi; cá mới tham gia từ bước sau.

        Spec 0 & C: cá cạnh người chơi, bước đó cá bơi ra xa => vẫn bắt được.
        """
        t = g()
        catch_radius = t["catch_radius"]
        fish_speed = t["fish_speed"]

        with Workdir() as w:
            # Đặt cá ở khoảng cách vừa vặn <= catch_radius (ví dụ catch_radius - 0.05).
            # Trong bước này cá bơi ra xa khỏi người chơi theo hướng 0 độ (tăng x).
            # Nếu xét vị trí sau khi bơi thì cá đã vượt quá catch_radius,
            # nhưng theo spec thứ tự bước 5 xét trước khi bơi ở bước 7 nên vẫn bắt được.
            player_pos = [20.0, 10.0]
            fish_pos = [player_pos[0] + catch_radius - 0.01, player_pos[1]]
            block = {
                "player": {"pos": list(player_pos)},
                "random_fish": True,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": list(fish_pos), "heading_deg": 0.0, "age_ticks": 0}],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            inputs = [{"tick": 0, "catch": True}]
            rows = run(w, block, inputs=inputs, ticks=1)

            ev_caught = events(rows, "fish_caught")
            self.assertEqual(len(ev_caught), 1, "Cá trong tầm trước khi bơi phải bắt được")
            self.assertEqual(ev_caught[0]["data"]["fish_id"], "F1")

    def test_ac_p2_06_monster_patrol_and_chase(self):
        """AC-P2-06: Cá Sấu patrol <-> chase (<= 10 m, d >= 10) <-> patrol (> 16 m hoặc d < 10), chặn d in [10,30].

        Spec B1, B2 & C: d = 5 cách 3 m => quái vẫn patrol; d = 15 => chase.
        M2 chỉ từ Ngày 3 (standalone gather Ngày 1 chỉ có M1).
        """
        t = g()
        m_cfg = t["monsters"]
        species = m_cfg["species"]["ca_sau"]
        detect_r = species["detect_radius"]
        exit_r = species["exit_radius"]
        depth_min, depth_max = species["depths"]

        # Nhánh 1: Người chơi d = 5 (< 10) dù khoảng cách 3 m (<= detect_r) => quái vẫn patrol
        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 5.0]},
                "random_fish": False,
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 8.0],
                    "waypoints": [[60.0, 12.0], [64.0, 12.0]],
                    "target_idx": 1,
                    "state": "patrol",
                }],
            }
            rows = run(w, block, ticks=2)
            m_state = snapshots(rows)[-1]["monsters"][0]
            self.assertEqual(m_state["state"], "patrol", "d < 10 thì quái không được chuyển sang chase")

        # Nhánh 2: Người chơi d = 15 (>= 10) cách <= 10 m => quái chuyển sang chase
        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 15.0]},
                "random_fish": False,
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 20.0],
                    "waypoints": [[60.0, 20.0], [64.0, 20.0]],
                    "target_idx": 1,
                    "state": "patrol",
                }],
            }
            rows = run(w, block, ticks=2)
            m_state = snapshots(rows)[-1]["monsters"][0]
            self.assertEqual(m_state["state"], "chase", "d >= 10 và khoảng cách <= 10 m thì quái phải chase")

        # Nhánh 3: Đang chase mà người chơi d < 10 (rút lên mặt nước) => quái trở lại patrol
        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 8.0]},
                "random_fish": False,
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 18.0],
                    "waypoints": [[60.0, 18.0], [64.0, 18.0]],
                    "target_idx": 1,
                    "state": "chase",
                }],
            }
            rows = run(w, block, ticks=2)
            m_state = snapshots(rows)[-1]["monsters"][0]
            self.assertEqual(m_state["state"], "patrol", "Người chơi về d < 10 thì quái phải chuyển lại patrol")

        # Nhánh 4: Standalone gather Ngày 1 mặc định chỉ có M1, không có M2
        with Workdir() as w:
            block = {"random_fish": False}
            rows = run(w, block, ticks=1)
            monster_ids = [m["id"] for m in snapshots(rows)[0]["monsters"]]
            self.assertIn("M1", monster_ids)
            self.assertNotIn("M2", monster_ids, "M2 chỉ xuất hiện từ Ngày 3")

    def test_ac_p2_07_monster_hit_and_recoil(self):
        """AC-P2-07: Chạm: -1 Máu, rơi floor(n/2) LIFO, bất tử 90, recoil 60 bước x 2/60 m; monster_hit.

        Spec B3 & C: giỏ 5 món => mất 2 món cuối; 90 tick sau mới hit lại được.
        """
        t = g()
        m_cfg = t["monsters"]
        loss_ratio = m_cfg["loss_ratio"]
        invuln_ticks = m_cfg["invuln_ticks"]

        initial_hold = ["ca_loc", "bong_dien_dien", "ca_linh", "ca_keo", "bong_sung"]
        drop_count = math.floor(len(initial_hold) * loss_ratio)  # floor(5 * 0.5) = 2
        expected_remaining = initial_hold[:-drop_count]  # ["ca_loc", "bong_dien_dien", "ca_linh"]

        with Workdir() as w:
            # Người chơi ở d >= 10, quái ở khoảng cách <= hit_radius (1.5)
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 3, "invuln_ticks": 0},
                "hold": hold_items(initial_hold),
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
            rows = run(w, block, ticks=2)

            ev_hit = events(rows, "monster_hit")
            self.assertEqual(len(ev_hit), 1, "Phải phát đúng một sự kiện monster_hit")
            hit_data = ev_hit[0]["data"]
            self.assertEqual(hit_data["monster_id"], "M1")
            self.assertEqual(hit_data["hp"], 2)

            # 2 món rơi theo LIFO là 2 món cuối cùng trong giỏ
            # Đổi test (P3 lát B): lost là mảng cá thể theo đúng thứ tự bỏ (mới nhất trước).
            self.assertEqual(len(hit_data["lost"]), drop_count)
            self.assertEqual([it["kind"] for it in hit_data["lost"]],
                             list(reversed(initial_hold[-drop_count:])))

            # Snapshot sau khi hit
            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["player"]["hp"], 2)
            # Đổi test (P3 lát B): hold là mảng cá thể {id, kind, fresh}.
            self.assertEqual([it["kind"] for it in s_end["hold"]], expected_remaining)
            self.assertGreater(s_end["player"]["invuln_ticks"], 0, "Người chơi phải có thời gian bất tử")

            # Quái M1 vào trạng thái recoil
            m1 = [m for m in s_end["monsters"] if m["id"] == "M1"][0]
            self.assertEqual(m1["state"], "recoil")

    def test_ac_p2_08_monster_faint_and_choke(self):
        """AC-P2-08: Ngất do quái: faint{cause:"monster"}, mất giỏ, gather_end(fainted) ngay; ngạt xuyên bất tử.

        Spec B4 & C: Máu 1 + chạm => faint{cause:"monster"} rồi gather_end(fainted) cùng tick, kho {}.
        """
        t = g()
        m_cfg = t["monsters"]
        with Workdir() as w:
            inv_file = w.path("inv.json")
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 1, "invuln_ticks": 0},
                "hold": hold_items(["ca_loc", "ca_keo"]),
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
            rows = run(w, block, ticks=2, inv=inv_file)

            ev_faint = events(rows, "faint")
            self.assertEqual(len(ev_faint), 1, "Phải phát sự kiện faint khi hp về 0")
            faint_data = ev_faint[0]["data"]
            self.assertEqual(faint_data.get("cause"), "monster")
            self.assertEqual(faint_data["hp"], 0)
            # Đổi test (P3 lát B): lost là mảng cá thể (đọc kind), không còn mảng kind.
            self.assertEqual({it["kind"] for it in faint_data["lost"]}, {"ca_loc", "ca_keo"})

            ev_end = events(rows, "gather_end")
            self.assertEqual(len(ev_end), 1)
            self.assertEqual(ev_end[0]["data"]["reason"], "fainted")
            # Đổi test (P3 lát B): gather_end.inventory là mảng cá thể v1.2 (ngất => rỗng).
            self.assertEqual(ev_end[0]["data"]["inventory"], {"items": []})

            with open(inv_file, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

        # Nhánh 2: Ngạt xuyên bất tử (đang bất tử do quái nhưng hết oxy vẫn bị choke)
        with Workdir() as w:
            block = {
                "player": {"pos": [20.0, 5.0], "hp": 2, "invuln_ticks": 60, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                "hold": hold_items(["ca_loc"]),
                "random_fish": False,
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            rows = run(w, block, ticks=2)
            self.assertEqual(len(events(rows, "choke")), 1, "Ngạt phải xuyên bất tử")
            # Ngạt không làm rơi giỏ trước khi ngất
            # Đổi test (P3 lát B): hold là mảng cá thể {id, kind, fresh}.
            self.assertEqual([it["kind"] for it in snapshots(rows)[-1]["hold"]], ["ca_loc"])

    def test_ac_p2_09_step_order(self):
        """AC-P2-09: Thứ tự một bước gather v1.1 (mục 0 spec).

        Quy tắc ưu tiên:
        1. Cập bến (bước 4) thắng hết giờ (bước 6).
        2. Ngạt ngất ở bước 2 dừng bước ngay, không xét quái hit ở bước 3.
        3. Quái hit gây ngất ở bước 3 dừng bước ngay, không xét bắt cá ở bước 5.
        """
        t = g()
        m_cfg = t["monsters"]
        # Quy tắc 1: Cập bến trước khi hết giờ cùng tick
        with Workdir() as w:
            block = {
                "player": {"pos": [2.0, 0.0]},
                "time_left_ticks": 1,
                "random_fish": False,
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            ev_end = events(rows, "gather_end")
            self.assertEqual(len(ev_end), 1)
            self.assertEqual(ev_end[0]["data"]["reason"], "docked", "Cập bến bước 4 phải thắng hết giờ bước 6")

        # Quy tắc 2: Choke gây ngất ở bước 2 dừng bước, không phát monster_hit ở bước 3
        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59},
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

            ev_choke = events(rows, "choke")
            self.assertEqual(len(ev_choke), 1)
            self.assertEqual(events(rows, "monster_hit"), [], "Bước 2 ngất thì dừng, không phát monster_hit")
            ev_faint = events(rows, "faint")
            self.assertEqual(len(ev_faint), 1)
            self.assertNotEqual(ev_faint[0]["data"].get("cause"), "monster")

        # Quy tắc 3: Quái hit gây ngất ở bước 3 dừng bước, không bắt cá ở bước 5
        with Workdir() as w:
            block = {
                "player": {"pos": [60.0, 20.0], "hp": 1, "invuln_ticks": 0},
                "random_fish": False,
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [60.0, 20.0]}],
                "monsters": [{
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 20.5],
                    "waypoints": [[60.0, 20.5], [64.0, 20.5]],
                    "target_idx": 1,
                    "state": "patrol",
                }],
            }
            inputs = [{"tick": 0, "catch": True}]
            rows = run(w, block, inputs=inputs, ticks=1)

            self.assertEqual(len(events(rows, "monster_hit")), 1)
            self.assertEqual(events(rows, "fish_caught"), [], "Quái hit ngất dừng bước, không thực hiện bắt cá")

    def test_determinism_seed_1(self):
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
