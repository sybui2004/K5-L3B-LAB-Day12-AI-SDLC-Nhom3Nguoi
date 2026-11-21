"""Test cửa sổ chơi chế độ `day` (AC-P2-24, 25): màn chờ, pause, Shop, dữ liệu cho client.

Bước sim bằng `_tick_once` để tất định; một test chạy qua HTTP thật.
"""

import json
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer, main

TUNING = load_contract()["tuning"]
FAST = {"gather": {"hold": ["ca_loc"], "random_fish": False}, "quan": {"time_left_ticks": 5}}


def state(game):
    return json.loads(game.state_json())


def ticks(game, n=1):
    for _ in range(n):
        game._tick_once()


def press(game, button):
    game.set_input({button: True})
    game._tick_once()
    game.set_input({button: False})


def new_game(scenario=None, days=2):
    return LiveGame("day", TUNING, FAST if scenario is None else scenario, 1, days=days)


def to_play(game):
    game.advance_gate("menu")
    game.advance_gate("day_intro")


def to_quan(game):
    to_play(game)
    press(game, "interact")


def to_day_result(game):
    to_quan(game)
    game.advance_gate("evening_intro")
    for _ in range(20):
        if game.gate:
            return
        game._tick_once()
    raise AssertionError("ca quán không kết thúc")


def to_shop(game):
    to_day_result(game)
    game.advance_gate("day_result")


class Gates(unittest.TestCase):
    def test_starts_at_menu_and_sim_is_held(self):
        g = new_game()
        ticks(g, 5)
        s = state(g)
        self.assertEqual(s["gate"], "menu")
        self.assertEqual((s["tick"], s["day"], s["phase"]), (0, 1, "gather"))

    def test_menu_then_day_intro_then_play(self):
        g = new_game()
        g.advance_gate("menu")
        self.assertEqual(g.gate, "day_intro")
        ticks(g, 3)
        self.assertEqual(state(g)["tick"], 0)
        g.advance_gate("day_intro")
        self.assertIsNone(g.gate)
        ticks(g, 3)
        self.assertEqual(state(g)["tick"], 3)

    def test_stale_gate_is_ignored_and_unknown_gate_rejected(self):
        g = new_game()
        g.advance_gate("day_result")
        self.assertEqual(g.gate, "menu")
        with self.assertRaises(ValueError):
            g.advance_gate("khong_co")

    def test_evening_intro_holds_sim_after_gather(self):
        g = new_game()
        to_quan(g)
        s = state(g)
        self.assertEqual((s["gate"], s["phase"], s["phase_tick"]), ("evening_intro", "quan", 0))
        self.assertEqual(s["stock"], {"ca_loc": 1})
        before = s["tick"]
        ticks(g, 10)
        self.assertEqual(state(g)["tick"], before)

    def test_day_result_after_quan_has_stats(self):
        g = new_game()
        to_day_result(g)
        s = state(g)
        self.assertEqual((s["gate"], s["phase"]), ("day_result", "shop"))
        self.assertEqual(set(s["day_result"]), {"served", "left", "money", "tips", "reputation_delta", "best_dish"})
        left = s["time_left_ticks"]
        ticks(g, 10)
        self.assertEqual(state(g)["time_left_ticks"], left, "timer Shop chưa được chạy khi còn ở DayResult")

    def test_next_day_intro_after_shop(self):
        g = new_game()
        to_shop(g)
        self.assertIsNone(g.gate)
        press(g, "shop_done")
        s = state(g)
        self.assertEqual((s["gate"], s["day"], s["phase"], s["days_completed"]), ("day_intro", 2, "gather", 1))

    def test_summary_after_last_day_and_restart_returns_to_menu(self):
        g = new_game(days=1)
        to_shop(g)
        press(g, "shop_done")
        s = state(g)
        self.assertEqual((s["gate"], s["finished"], s["reason"]), ("summary", True, "days_complete"))
        g.advance_gate("summary")
        self.assertEqual(g.gate, "summary", "Summary chỉ rời bằng Về menu")
        g.restart()
        s = state(g)
        self.assertEqual((s["gate"], s["tick"], s["day"]), ("menu", 0, 1))

    def test_stale_held_input_does_not_leak_through_gate(self):
        g = new_game()
        g.set_input({"pause": True, "move": [1, 0]})
        to_play(g)
        ticks(g, 2)
        s = state(g)
        self.assertEqual(s["state"], "playing")
        self.assertEqual(s["player"]["pos"], [float(c) for c in TUNING["gather"]["start_pos"]])


class ShopAndPause(unittest.TestCase):
    def test_pause_freezes_shop_timer(self):
        g = new_game()
        to_shop(g)
        ticks(g, 5)
        left = state(g)["time_left_ticks"]
        press(g, "pause")
        ticks(g, 10)
        s = state(g)
        self.assertEqual((s["state"], s["time_left_ticks"]), ("paused", left))
        press(g, "pause")
        s = state(g)
        self.assertEqual(s["state"], "playing")
        self.assertLess(s["time_left_ticks"], left)

    def test_buy_over_input(self):
        sc = dict(FAST, day={"money": 300, "earned": 300})
        g = new_game(sc)
        to_shop(g)
        g.set_input({"buy": "oxygen"})
        g._tick_once()
        s = state(g)
        self.assertEqual((s["money"], s["upgrades"]), (100, {"oxygen": 1}))
        self.assertEqual(s["shop_table"], TUNING["shop"]["upgrades"])

    def test_bad_action_inputs_rejected(self):
        g = new_game()
        for body in ({"buy": 5}, {"buy": ""}, {"buy": "x" * 33}, {"pause": 1}, {"shop_done": "yes"}):
            with self.subTest(body=body), self.assertRaises(ValueError):
                g.set_input(body)


class ClientData(unittest.TestCase):
    def test_meta_follows_phase_and_menu_is_sent(self):
        g = new_game()
        s = state(g)
        self.assertIn("dock_pos", s["meta"])
        self.assertEqual(s["menu"], TUNING["menu"])
        to_quan(g)
        self.assertIn("patience_s", state(g)["meta"])
        g2 = new_game()
        to_shop(g2)
        self.assertIn("upgrades", state(g2)["meta"])

    def test_tally_counts_served_dishes_across_shift(self):
        stove, table = TUNING["quan"]["stoves"][0]["id"], TUNING["quan"]["tables"][0]["id"]
        sc = {"gather": {"hold": ["ca_loc"], "random_fish": False},
              "quan": {"player": {"pos": [6.1, 5]}, "time_left_ticks": 1300,
                       "stoves": [{"id": stove, "pos": [5, 5]}], "tables": [{"id": table, "pos": [7.4, 5]}]}}
        g = new_game(sc, days=1)
        to_quan(g)
        g.advance_gate("evening_intro")
        ticks(g, 121)
        press(g, "interact")
        self.assertEqual(state(g)["stoves"][0]["state"], "cooking")
        ticks(g, MENU_COOK_TICKS + 2)
        press(g, "interact")
        self.assertEqual(state(g)["hand"], "ca_loc_nuong_trui")
        g.set_input({"move": [1, 0]})
        ticks(g, 15)
        g.set_input({"move": [0, 0]})
        ticks(g, 8)
        press(g, "interact")
        self.assertEqual(state(g)["customers"][0]["state"], "eating")
        for _ in range(1400):
            if g.gate:
                break
            g._tick_once()
        tally = state(g)["tally"]
        self.assertEqual((tally["served"], tally["dishes"]), (1, {"ca_loc_nuong_trui": 1}))
        paid = [e for e in state(g)["events"] if e["name"] == "paid"]
        self.assertEqual(len(paid), 1)
        self.assertGreater(tally["tips"], 0)
        self.assertEqual(tally["tips"], paid[0]["data"]["tip"], "boa v1.2 phụ thuộc độ tươi nên so với event")
        self.assertEqual(tally["left"], 0)

    def test_standalone_modes_have_no_gate(self):
        g = LiveGame("gather", TUNING, {}, 1)
        ticks(g, 3)
        s = state(g)
        self.assertIsNone(s["gate"])
        self.assertEqual(s["tick"], 3)
        self.assertIn("dock_pos", s["meta"])


MENU_COOK_TICKS = TUNING["menu"]["ca_loc_nuong_trui"]["cook_s"] * 60


class Http(unittest.TestCase):
    def _post(self, url, obj):
        req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status
        except urllib.error.HTTPError as e:
            e.close()
            return e.code

    def test_screens_and_advance_over_http(self):
        server = LiveServer(new_game(), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            with urllib.request.urlopen(base + "/screens.js", timeout=5) as r:
                self.assertIn("javascript", r.headers["Content-Type"])
                self.assertIn(b"window.SCREENS", r.read())
            self.assertEqual(self._post(base + "/advance", {"gate": "menu"}), 200)
            with urllib.request.urlopen(base + "/state", timeout=5) as r:
                self.assertEqual(json.load(r)["gate"], "day_intro")
            self.assertEqual(self._post(base + "/advance", {"gate": "khong_co"}), 400)
            self.assertEqual(self._post(base + "/advance", ["menu"]), 400)
            self.assertEqual(self._post(base + "/input", {"buy": 5}), 400)
        finally:
            server.stop()


class Cli(unittest.TestCase):
    def test_bad_day_arguments_exit_2(self):
        for argv in (["--mode", "day", "--days", "9"], ["--mode", "gather", "--days", "2"],
                     ["--mode", "day", "--inventory", "kho.json"], ["--mode", "day", "--inventory-out", "kho.json"]):
            with self.subTest(argv=argv):
                self.assertEqual(main([*argv, "--port", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
