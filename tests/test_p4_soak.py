"""Test soak headless (TICKET-04 mục 2, TV2; spec phase-4/bench-soak.md B4). Chạy qua `soak_cmd` (hộp đen).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_p4_soak -v
"""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir, run_headless


def soak_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return shlex.split(json.load(f)["soak_cmd"])


def run_soak(w, *args, name="soak.json"):
    cmd = soak_cmd()
    if cmd[0] == "python":  # máy không có `python` (chỉ python3) vẫn chạy được test
        import sys
        cmd[0] = sys.executable
    p = subprocess.run([*cmd, *args, "--out", w.path(name)], cwd=ROOT, capture_output=True, text=True)
    out = None
    if os.path.exists(w.path(name)):
        with open(w.path(name), encoding="utf-8") as f:
            out = json.load(f)
    return p.returncode, p.stderr, out


class Soak(unittest.TestCase):
    def test_schema_and_pass_condition(self):
        with Workdir() as w:
            code, err, out = run_soak(w, "--seed", "7", "--days", "3")
            self.assertEqual(code, 0, err)
            self.assertEqual(set(out), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((out["days"], out["days_completed"], out["crashes"]), (3, 3, 0))
            self.assertEqual([r["day"] for r in out["results"]], [1, 2, 3])
            for r in out["results"]:
                self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
                self.assertEqual(r["score"], r["earned"] + 100 * int(r["reputation"]))
            earned = [r["earned"] for r in out["results"]]
            self.assertEqual(earned, sorted(earned))  # earned cộng dồn xuyên Ngày

    def test_deterministic_ignoring_wall_time(self):
        with Workdir() as w:
            a = run_soak(w, "--seed", "7", "--days", "2", name="a.json")[2]
            b = run_soak(w, "--seed", "7", "--days", "2", name="b.json")[2]
            a.pop("duration_s"), b.pop("duration_s")
            self.assertEqual(a, b)

    def test_plan_repeats_after_day_5(self):
        """Ngày 6 dùng lại kế hoạch D1 (DaySim, có thể chạy quá 5 Ngày khi soak)."""
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.day import DaySim
        t = load_contract()["tuning"]
        d = DaySim(t, {}, Streams(1), IdAllocator(), days=10)
        d.day = 6
        self.assertEqual(d._plan()["dishes"], t["day_plan"][0]["dishes"])
        d.day = 10
        self.assertEqual(d._plan()["dishes"], t["day_plan"][4]["dishes"])

    def test_ten_days_seed_7(self):
        """B4: --days 10 --seed 7 ⇒ 10/10, 0 crash, results theo Ngày 1..10, earned không giảm (~3 s)."""
        with Workdir() as w:
            code, err, out = run_soak(w, "--seed", "7", "--days", "10")
            self.assertEqual(code, 0, err)
            self.assertEqual((out["days_completed"], out["crashes"], len(out["results"])), (10, 0, 10))
            self.assertEqual([r["day"] for r in out["results"]], list(range(1, 11)))
            earned = [r["earned"] for r in out["results"]]
            self.assertEqual(earned, sorted(earned))

    def test_day6_announces_day1_plan(self):
        """Chạy 6 Ngày trong tiến trình bằng bot: event day_plan của Ngày 6 trùng D1."""
        from chonoi.contract import load_contract
        from chonoi.runner import Session
        from chonoi.sim.bot import Bot
        t = load_contract()["tuning"]
        sess, bot, plans = Session("day", t, {}, 7, None, 6), Bot(t), {}
        for row in sess.initial_events():
            if row["name"] == "day_plan":
                plans[row["day"]] = row["data"]
        while not sess.done:
            for row in sess.step(bot.next(sess.snapshot())):
                if row["name"] == "day_plan":
                    plans[row["day"]] = row["data"]
        self.assertEqual(plans[6], plans[1])
        self.assertEqual(plans[1]["dishes"], t["day_plan"][0]["dishes"])

    def test_headless_day_still_limited_to_5(self):
        with Workdir() as w:
            self.assertEqual(run_headless("--mode", "day", "--days", "6", "--seed", "1", "--ticks", "0",
                                          "--out", w.path("o.jsonl"))[0], 2)

    def test_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(run_soak(w, "--seed", "7", "--days", "0")[0], 2)
            self.assertEqual(run_soak(w, "--seed", "x", "--days", "1")[0], 2)


if __name__ == "__main__":
    unittest.main()
