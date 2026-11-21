"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

v1.1 (TV2, TICKET-02 4.2/4.4): pause chung cho mọi mode (tick tăng, sim_tick/phase_tick đứng yên), mode `day`
(DaySim trả sự kiện kèm pha + Ngày), sự kiện tick 0, snapshot khi đổi pha, `days_completed` ở dòng end.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.day import DaySim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1, contract_version="1.2"):
        self.mode = mode
        self.contract_version = contract_version
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0       # tick ngoài: tăng cả khi pause
        self.sim_tick = 0   # bước gameplay thật
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _state(self):
        return "finished" if self.sim.done else ("paused" if self.paused else "playing")

    def _row(self, ev):
        name, data = ev[0], ev[1]
        phase = ev[2] if len(ev) > 2 else self.sim.phase
        row = {"type": "event", "tick": self.tick, "phase": phase}
        if self.mode == "day":
            row["day"] = ev[3] if len(ev) > 3 else self.sim.day
        row.update(name=name, data=data)
        return row

    def initial_events(self) -> list:
        """Sự kiện tick 0 (mode day: day_start, day_plan, phase_start) — ghi SAU snapshot tick 0 (clarify #19)."""
        pending, self.sim.pending = getattr(self.sim, "pending", []), []
        return [self._row(ev) for ev in pending]

    def snapshot(self) -> dict:
        phase_tick = getattr(self.sim, "phase_tick", self.sim_tick)
        s = _common(self.sim, self.tick, self.sim_tick, phase_tick, self.tuning, self._state())
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        rows = []
        if hasattr(self.sim, "phase_changed"):
            self.sim.phase_changed = False
        if inp.pressed("pause"):  # xét cạnh pause TRƯỚC (TICKET-02 4.2)
            if not self.paused:
                self.paused = True
                return [self._row(("paused", {}))]
            self.paused = False
            rows.append(self._row(("resumed", {})))  # chạy gameplay ngay trong bước này
        elif self.paused:
            return []  # bỏ qua cạnh hành động và buy; mọi timer đứng yên
        events = self.sim.step(inp)
        self.sim_tick += 1
        return rows + [self._row(ev) for ev in events]

    @property
    def phase_changed(self) -> bool:
        return bool(getattr(self.sim, "phase_changed", False))

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, self.sim_tick, self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": self._state(),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            items = self.sim.hold_counts() if self.contract_version == "1.1" else self.sim.hold
            write_inventory(inventory_out, items, self.contract_version)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1, contract_version="1.2"):
    sess = Session(mode, tuning, scenario, seed, inventory, days, contract_version)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        for row in sess.initial_events():  # day: day_start, day_plan, phase_start (tick 0) SAU snapshot (clarify #19)
            w.write(row)
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done or sess.phase_changed:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
