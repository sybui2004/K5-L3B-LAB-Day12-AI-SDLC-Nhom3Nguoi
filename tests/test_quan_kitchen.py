"""Bộ test hộp đen quan lát 4: bếp, bưng, phục vụ, tiền, uy tín (AC-Q-07..12).

Chạy qua headless (--mode quan) theo đúng Test Contract v1.0.
Mọi số liệu (cook_s, eat_s, price, tip_rate, interact_radius...) đọc từ game.contract.json, không hard-code.
Dựa hoàn toàn vào spec docs/spec/phase-1/quan.md (mục 0, B1-B4, bảng AC-Q-07..12),
không dựa vào code cài đặt trong chonoi/sim/quan.py.
"""

import json
import os
import shutil
import subprocess
import sys
import unittest

# Đảm bảo import được helpers dù chạy từ đâu
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

from helpers import (
    Workdir,
    close,
    events,
    frames,
    headless_cmd,
    read_jsonl,
    snapshots,
    write_json,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_contract_data():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def q():
    return load_contract_data()["tuning"]["quan"]


def menu():
    return load_contract_data()["tuning"]["menu"]


def headless_cmd_quan():
    cmd = headless_cmd()
    if sys.platform == "win32" and not shutil.which(cmd[0]):
        # Trên Windows, nếu python3 không có trong PATH thì fallback dùng sys.executable
        return [sys.executable, *cmd[1:]]
    return cmd


def run_headless_quan(*args, cwd=ROOT):
    p = subprocess.run([*headless_cmd_quan(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def run(w, block, inputs=(), ticks=1, every=1, inv=None, seed="1"):
    sc = write_json(w.path("sc.json"), {"quan": block})
    args = [
        "--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
        "--snapshot-every", str(every), "--out", w.path("o.jsonl")
    ]
    if inputs:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv:
        args += ["--inventory", inv]
    code, err = run_headless_quan(*args)
    assert code == 0, f"run_headless_quan thất bại (exit code {code}): {err}"
    return read_jsonl(w.path("o.jsonl"))


class TestQuanKitchen(unittest.TestCase):
    """Test hộp đen cho lát 4: bếp, bưng, phục vụ, tiền, uy tín (AC-Q-07..12)."""

    def test_ac_q_07_cook_started_and_dish_ready(self):
        """AC-Q-07: Đứng cạnh bếp, interact => cook_started; sau cook_s*60 tick => dish_ready.

        [đối chiếu: món nào được nấu]
        Spec B2: Bếp idle + tay không + có khách waiting có món chưa nấu => nấu món của khách
        id nhỏ nhất đang chờ: trừ nguyên liệu đã giữ chỗ khỏi kho, state = cooking,
        cook_ticks_left = cook_s * 60, cook_started {stove_id, dish}.
        _tick_stoves: cooking giảm cook_ticks_left; về 0 => state = ready, dish_ready {stove_id, dish}.
        """
        t = q()
        m = menu()
        dish = "ca_loc_nuong_trui"
        recipe = m[dish]["recipe"]
        cook_ticks = int(m[dish]["cook_s"] * 60)
        other_dish = "goi_bong_sung"
        other_recipe = m[other_dish]["recipe"]
        stove = t["stoves"][0]
        table = t["tables"][0]

        with Workdir() as w:
            block = {
                "player": {"pos": list(stove["pos"])},
                "tables": [
                    {"id": table["id"], "pos": list(table["pos"])},
                ],
                "stock": {
                    "ca_loc": recipe["ca_loc"],
                },
                "random_customers": False,
                "customers": [
                    {
                        "id": "C1",
                        "table_id": table["id"],
                        "dish_id": dish,
                        "state": "waiting",
                        "patience_ticks_left": int(t["patience_s"] * 60),
                        "reserved": dict(recipe),
                    },
                ],
            }
            # Tick 0 nhấn interact đứng cạnh bếp B1
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=cook_ticks + 5)

            # Kiểm tra sự kiện cook_started: bếp bắt đầu nấu món của khách đang chờ
            ev_start = events(rows, "cook_started")
            self.assertEqual(len(ev_start), 1, "Phải phát đúng một sự kiện cook_started")
            self.assertEqual(ev_start[0]["data"]["stove_id"], stove["id"])
            self.assertEqual(
                ev_start[0]["data"]["dish"],
                dish,
                "Bếp phải nấu món của khách đang chờ (C1: ca_loc_nuong_trui)",
            )
            start_tick = ev_start[0]["tick"]

            # Kiểm tra kho bị trừ đúng phần reserved của khách C1 và reserved của C1 về rỗng
            snaps = snapshots(rows)
            s_after_interact = snaps[1]
            self.assertEqual(
                s_after_interact["stock"].get("ca_loc", 0),
                0,
                "Kho phải bị trừ đúng phần reserved của món ca_loc_nuong_trui",
            )
            c1_state = [c for c in s_after_interact.get("customers", []) if c["id"] == "C1"][0]
            self.assertEqual(
                c1_state.get("reserved", {}),
                {},
                "reserved của khách C1 phải rỗng sau khi bếp bắt đầu nấu",
            )

            # Kiểm tra sự kiện dish_ready xuất hiện sau đúng cook_s * 60 ticks
            ev_ready = events(rows, "dish_ready")
            self.assertEqual(len(ev_ready), 1, "Phải phát đúng một sự kiện dish_ready")
            self.assertEqual(ev_ready[0]["data"]["stove_id"], stove["id"])
            self.assertEqual(ev_ready[0]["data"]["dish"], dish)
            self.assertEqual(
                ev_ready[0]["tick"],
                start_tick + cook_ticks,
                f"dish_ready phải phát sau đúng {cook_ticks} tick kể từ cook_started",
            )

            # Snapshot cuối: bếp phải ở trạng thái ready
            s_end = snaps[-1]
            stove_state = [st for st in s_end["stoves"] if st["id"] == stove["id"]][0]
            self.assertEqual(stove_state["state"], "ready")

    def test_ac_q_08_pick_up_ready_dish_and_carry_limit(self):
        """AC-Q-08: interact ở bếp chín => dish_picked, tay cầm món; tay đầy thì không nhặt.

        [đối chiếu PRD-0 mục F/B2]
        Spec B2: Bếp ready + tay trống (carry_limit 1) => hand = dish, bếp idle, dish_picked {stove_id, dish}.
        Khi tay đã cầm món (tay đầy do carry_limit = 1), interact ở bếp ready không nhặt thêm, không phát dish_picked.
        """
        t = q()
        dish = "ca_loc_nuong_trui"
        other_dish = "goi_bong_sung"
        stove = t["stoves"][0]

        # Nhánh 1: Tay trống -> nhặt được món chín
        with Workdir() as w:
            block = {
                "player": {"pos": list(stove["pos"])},
                "hand": None,
                "stoves": [{
                    "id": stove["id"],
                    "pos": list(stove["pos"]),
                    "state": "ready",
                    "dish": dish,
                }],
                "random_customers": False,
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            ev_picked = events(rows, "dish_picked")
            self.assertEqual(len(ev_picked), 1, "Bếp chín + tay trống phải phát dish_picked")
            self.assertEqual(ev_picked[0]["data"]["stove_id"], stove["id"])
            self.assertEqual(ev_picked[0]["data"]["dish"], dish)

            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["hand"], dish, "Tay người chơi phải cầm món vừa nhặt")
            stove_state = [st for st in s_end["stoves"] if st["id"] == stove["id"]][0]
            self.assertEqual(stove_state["state"], "idle", "Bếp sau khi nhặt phải trở lại idle")

        # Nhánh 2: Tay đầy (đang cầm other_dish) -> không nhặt được thêm
        with Workdir() as w:
            block = {
                "player": {"pos": list(stove["pos"])},
                "hand": other_dish,
                "stoves": [{
                    "id": stove["id"],
                    "pos": list(stove["pos"]),
                    "state": "ready",
                    "dish": dish,
                }],
                "random_customers": False,
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            self.assertEqual(events(rows, "dish_picked"), [], "Tay đầy thì không được phát dish_picked")
            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["hand"], other_dish, "Tay người chơi vẫn giữ món cũ")
            stove_state = [st for st in s_end["stoves"] if st["id"] == stove["id"]][0]
            self.assertEqual(stove_state["state"], "ready", "Bếp vẫn phải ở trạng thái ready")

    def test_ac_q_09_serve_dish_and_customer_pays(self):
        """AC-Q-09: Bưng đúng món tới bàn => served; sau eat_s*60 tick => paid, tiền tăng đúng giá + boa.

        [đối chiếu]
        Spec B3: Bàn có khách waiting đúng món đang cầm => hand = None, khách eating, eat_ticks = eat_s * 60,
        chốt price và tip; served {customer_id, table_id, dish}. Cầm sai món => không làm gì.
        [đối chiếu PRD-0: earned vs shift_earned, làm tròn]
        Spec B4: _tick_eating: eat_ticks về 0 => money += price + tip, earned += price + tip,
        khách rời bàn, paid {customer_id, amount, tip}.
        """
        t = q()
        m = menu()
        dish = "ca_loc_nuong_trui"
        price = m[dish]["price"]
        tip_rate = t["tip_rate"]
        # Phục vụ khi kiên nhẫn tối đa (>= 50%) => có boa: round(price * tip_rate)
        expected_tip = int(round(price * tip_rate))
        eat_ticks = int(t["eat_s"] * 60)
        table = t["tables"][0]

        # Nhánh 1: Bưng đúng món tới bàn
        with Workdir() as w:
            block = {
                "player": {"pos": list(table["pos"])},
                "hand": dish,
                "random_customers": False,
                "customers": [{
                    "id": "C1",
                    "table_id": table["id"],
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=eat_ticks + 5)

            # Sự kiện served
            ev_served = events(rows, "served")
            self.assertEqual(len(ev_served), 1, "Phải phát đúng một sự kiện served")
            self.assertEqual(ev_served[0]["data"]["customer_id"], "C1")
            self.assertEqual(ev_served[0]["data"]["table_id"], table["id"])
            self.assertEqual(ev_served[0]["data"]["dish"], dish)
            serve_tick = ev_served[0]["tick"]

            # Sự kiện paid sau đúng eat_s * 60 ticks
            ev_paid = events(rows, "paid")
            self.assertEqual(len(ev_paid), 1, "Ăn xong phải phát đúng một sự kiện paid")
            self.assertEqual(ev_paid[0]["data"]["customer_id"], "C1")
            self.assertEqual(ev_paid[0]["data"]["tip"], expected_tip)
            self.assertEqual(
                ev_paid[0]["data"]["amount"],
                price + expected_tip,
                "paid.amount phải bằng price + tip",
            )
            self.assertEqual(
                ev_paid[0]["tick"],
                serve_tick + eat_ticks,
                f"paid phải phát sau đúng {eat_ticks} tick kể từ served",
            )

            # Tiền và doanh thu tăng đúng giá + boa
            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["money"], price + expected_tip)
            self.assertEqual(s_end["earned"], price + expected_tip)
            self.assertIsNone(s_end["hand"], "Tay người chơi phải rỗng sau khi phục vụ")

        # Nhánh 2: Cầm sai món tới bàn => không làm gì
        with Workdir() as w:
            block = {
                "player": {"pos": list(table["pos"])},
                "hand": "goi_bong_sung",  # Sai món khách muốn
                "random_customers": False,
                "customers": [{
                    "id": "C1",
                    "table_id": table["id"],
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            self.assertEqual(events(rows, "served"), [], "Cầm sai món không được phát served")
            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["hand"], "goi_bong_sung", "Tay vẫn phải giữ nguyên món sai")
            cust = [c for c in s_end.get("customers", []) if c["id"] == "C1"][0]
            self.assertEqual(cust["state"], "waiting", "Khách vẫn phải ở trạng thái waiting")

    def test_ac_q_10_tip_and_reputation_by_patience_ratio(self):
        """AC-Q-10: Phục vụ khi kiên nhẫn >= 50% => có boa và uy tín +0.2; < 50% => không boa.

        [đối chiếu PRD-0: làm tròn boa]
        Spec B3: tip = round(price * tip_rate) nếu patience_ticks / (patience_s * 60) >= tip_min_patience_ratio, ngược lại 0.
        Spec B4: nếu có tip thì reputation += tip_reputation (kẹp [0, 5]).
        """
        t = q()
        m = menu()
        dish = "ca_loc_nuong_trui"
        price = m[dish]["price"]
        expected_tip = int(round(price * t["tip_rate"]))
        patience_max_ticks = int(t["patience_s"] * 60)
        eat_ticks = int(t["eat_s"] * 60)
        table = t["tables"][0]
        rep_initial = t["reputation_initial"]
        tip_rep = t["tip_reputation"]

        # Trường hợp A: Kiên nhẫn >= 50% (đặt 80%) => Có boa và uy tín tăng
        with Workdir() as w:
            patience_high = int(patience_max_ticks * 0.8)
            block = {
                "player": {"pos": list(table["pos"])},
                "hand": dish,
                "random_customers": False,
                "reputation": rep_initial,
                "customers": [{
                    "id": "C1",
                    "table_id": table["id"],
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": patience_high,
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=eat_ticks + 5)

            ev_paid = events(rows, "paid")
            self.assertEqual(len(ev_paid), 1)
            self.assertEqual(ev_paid[0]["data"]["tip"], expected_tip, "Kiên nhẫn >= 50% phải có boa")

            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["money"], price + expected_tip)
            expected_rep = min(float(t["reputation_max"]), rep_initial + tip_rep)
            self.assertTrue(
                close(s_end["reputation"], expected_rep, tol=0.01),
                f"Uy tín phải tăng {tip_rep} lên {expected_rep}, thực tế: {s_end['reputation']}",
            )

        # Trường hợp B: Kiên nhẫn < 50% (đặt 30%) => Không có boa và uy tín không tăng
        with Workdir() as w:
            patience_low = int(patience_max_ticks * 0.3)
            block = {
                "player": {"pos": list(table["pos"])},
                "hand": dish,
                "random_customers": False,
                "reputation": rep_initial,
                "customers": [{
                    "id": "C2",
                    "table_id": table["id"],
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": patience_low,
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=eat_ticks + 5)

            ev_paid = events(rows, "paid")
            self.assertEqual(len(ev_paid), 1)
            self.assertEqual(ev_paid[0]["data"]["tip"], 0, "Kiên nhẫn < 50% không được có boa")

            s_end = snapshots(rows)[-1]
            self.assertEqual(s_end["money"], price, "Tiền chỉ tăng đúng giá món, không có boa")
            self.assertTrue(
                close(s_end["reputation"], rep_initial, tol=0.01),
                f"Không có boa thì uy tín không đổi ({rep_initial}), thực tế: {s_end['reputation']}",
            )

    def test_ac_q_11_single_interact_priority(self):
        """AC-Q-11: Một interact chỉ tác động một đối tượng, ưu tiên (khoảng cách, bếp, id).

        [đối chiếu PRD-0 mục F]
        Spec B1: Tối đa một đối tượng mỗi bước: lọc bếp/bàn trong interact_radius,
        sắp theo (khoảng cách, bếp trước bàn, id), lấy đầu tiên, làm hành động hợp lệ của nó;
        không hợp lệ thì thôi (không thử đối tượng kế).
        """
        t = q()
        m = menu()
        dish = "ca_loc_nuong_trui"

        # Nhánh 1: Hòa khoảng cách giữa bếp và bàn => Bếp được ưu tiên trước bàn (bếp trước bàn)
        # Đặt bếp tại [5, 5], bàn tại [5, 7]. Người chơi đứng tại [5, 6]:
        # Khoảng cách tới bếp = 1.0, khoảng cách tới bàn = 1.0 (đều <= interact_radius 1.5).
        # Bếp đang ready dish, bàn đang có khách waiting dish đó, người chơi tay trống.
        # Nếu ưu tiên bếp: người chơi nhặt món từ bếp (dish_picked). Bàn chưa được phục vụ.
        with Workdir() as w:
            block = {
                "player": {"pos": [5.0, 6.0]},
                "hand": None,
                "random_customers": False,
                "stoves": [{"id": "B1", "pos": [5.0, 5.0], "state": "ready", "dish": dish}],
                "tables": [{"id": "T1", "pos": [5.0, 7.0]}],
                "customers": [{
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            ev_picked = events(rows, "dish_picked")
            ev_served = events(rows, "served")
            self.assertEqual(len(ev_picked), 1, "Hòa khoảng cách: bếp (0) phải thắng bàn (1)")
            self.assertEqual(len(ev_served), 0, "Chỉ được tác động tối đa một đối tượng, không phục vụ bàn")

        # Nhánh 2: Đối tượng gần hơn luôn thắng
        # Người chơi gần bàn hơn (cách 0.7) so với bếp (cách 1.3), cả 2 đều trong interact_radius 1.5.
        # Người chơi cầm dish. Bàn có khách waiting dish. Bếp cũng sẵn sàng nhặt (nhưng tay đầy).
        # Tác động phục vụ bàn (served) phải diễn ra.
        with Workdir() as w:
            block = {
                "player": {"pos": [5.0, 6.3]},
                "hand": dish,
                "random_customers": False,
                "stoves": [{"id": "B1", "pos": [5.0, 5.0], "state": "ready", "dish": dish}],
                "tables": [{"id": "T1", "pos": [5.0, 7.0]}],
                "customers": [{
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            self.assertEqual(len(events(rows, "served")), 1, "Bàn gần hơn thì phải tương tác với bàn")
            self.assertEqual(events(rows, "dish_picked"), [], "Không được tương tác đồng thời với bếp")

        # Nhánh 3: Đối tượng ưu tiên nhất không có hành động hợp lệ => KHÔNG thử đối tượng kế
        # Bếp B1 gần hơn (cách 0.5), nhưng B1 idle và không có khách waiting (hành động không hợp lệ).
        # Bàn T1 xa hơn (cách 1.0, vẫn <= interact_radius 1.5), người chơi cầm dish đúng món của bàn.
        # Kỳ vọng theo spec B1: Bếp được chọn đầu tiên; hành động không hợp lệ => thôi, KHÔNG thử bàn kế tiếp.
        with Workdir() as w:
            block = {
                "player": {"pos": [5.0, 5.5]},
                "hand": dish,
                "random_customers": False,
                "stoves": [{"id": "B1", "pos": [5.0, 5.0], "state": "idle", "dish": None}],
                "tables": [{"id": "T1", "pos": [5.0, 6.5]}],
                "customers": [{
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": dish,
                    "state": "waiting",
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            inputs = [{"tick": 0, "interact": True}]
            rows = run(w, block, inputs=inputs, ticks=2)

            self.assertEqual(
                events(rows, "served"), [],
                "Đối tượng gần nhất không hợp lệ thì dừng, không được fallback sang đối tượng kế",
            )

    def test_ac_q_12_time_out_quan_end_matches_snapshot(self):
        """AC-Q-12: Hết giờ => quan_end với money, earned, shift_earned, reputation khớp snapshot.

        [đối chiếu PRD-0: earned vs shift_earned]
        Spec AC-Q-12 & README 3.2:
        Hết giờ => sự kiện quan_end {reason: 'time', money, earned, shift_earned, reputation}.
        Các giá trị này phải khớp chính xác với snapshot tại tick kết thúc và tổng amount của sự kiện paid.
        """
        t = q()
        m = menu()
        dish = "ca_loc_nuong_trui"
        recipe = m[dish]["recipe"]
        price = m[dish]["price"]
        expected_tip = int(round(price * t["tip_rate"]))
        table = t["tables"][0]

        with Workdir() as w:
            block = {
                "time_left_ticks": 4,
                "random_customers": False,
                "reputation": 4.2,
                "customers": [{
                    "id": "C1",
                    "table_id": table["id"],
                    "dish_id": dish,
                    "state": "eating",
                    "eat_ticks_left": 2,
                    "price": price,
                    "tip": expected_tip,
                    "patience_ticks_left": int(t["patience_s"] * 60),
                    "reserved": {},
                }],
            }
            # Chạy 5 ticks để khách ăn xong (tick 2 paid) và time_left_ticks giảm về 0 (tick 4 quan_end)
            rows = run(w, block, ticks=5)

            # Kiểm tra có sự kiện paid và số tiền thực nhận
            ev_paid = events(rows, "paid")
            self.assertEqual(len(ev_paid), 1, "Khách phải ăn xong và phát sự kiện paid")
            total_paid = sum(p["data"]["amount"] for p in ev_paid)
            self.assertGreater(total_paid, 0, "Kịch bản phải có tiền thật từ khách trả")
            self.assertEqual(total_paid, price + expected_tip)

            # Phải có sự kiện quan_end
            ev_end = events(rows, "quan_end")
            self.assertEqual(len(ev_end), 1, "Phải phát đúng một sự kiện quan_end khi hết giờ")
            end_data = ev_end[0]["data"]
            self.assertEqual(end_data["reason"], "time", "Lý do kết thúc ca phải là 'time'")

            # Kiểm tra quan_end.money / earned khớp với tổng amount của sự kiện paid
            self.assertEqual(end_data["money"], total_paid, "quan_end.money phải bằng tổng amount paid")
            self.assertEqual(end_data["earned"], total_paid, "quan_end.earned phải bằng tổng amount paid")

            # Kiểm tra khớp với snapshot cuối cùng
            s_end = snapshots(rows)[-1]
            self.assertEqual(end_data["money"], s_end["money"], "money trong quan_end phải khớp snapshot")
            self.assertEqual(end_data["earned"], s_end["earned"], "earned trong quan_end phải khớp snapshot")
            self.assertTrue(
                close(end_data["reputation"], s_end["reputation"], tol=0.01),
                "reputation trong quan_end phải khớp snapshot",
            )
            # Ghi chú: Snapshot (chonoi/runner.py _common) hiện không có trường shift_earned theo README 3.2.
            # Nếu snapshot có thì đối chiếu; trong sự kiện quan_end kiểm tra khớp số tiền thu trong ca.
            if "shift_earned" in s_end:
                self.assertEqual(
                    end_data["shift_earned"],
                    s_end["shift_earned"],
                    "shift_earned trong quan_end phải khớp snapshot",
                )
            if "shift_earned" in end_data:
                self.assertEqual(
                    end_data["shift_earned"],
                    total_paid,
                    "shift_earned trong quan_end phải khớp số tiền thu trong ca",
                )

            # Dòng cuối của JSONL là end
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "time")


if __name__ == "__main__":
    unittest.main()
