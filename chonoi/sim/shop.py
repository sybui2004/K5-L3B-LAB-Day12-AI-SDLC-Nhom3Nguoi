"""Shop cuối Ngày (TICKET-02 mục 2 "Shop và nâng cấp", 4.2, 4.5). Chủ: TV2 (lit1numyt).

Một bước (spec phase-2/quan-shop.md C2): 1) một lệnh `buy` của frame (nếu có) → 2) cạnh `shop_done` ⇒ shop_end(done)
→ 3) giảm `time_left_ticks`, về 0 ⇒ shop_end(time). Bước cuối có cả buy và shop_done: mua trước rồi đóng.
`buy`: oxygen / hp ⇒ bought hoặc buy_failed(max_level | funds); lệnh của mở rộng chưa bật (weapon, net, buy:<kind>,
sell:<kind>) ⇒ bỏ qua, không event (clarify #18); chuỗi khác ⇒ buy_failed(unknown).
Mua trừ `money`, giữ `earned`/điểm; cấp mới hiện ngay ở `upgrades`, DaySim chỉ sao sang active_upgrades khi dựng Ngày mới.
"""

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
EXTENSION_ACTIONS = ("weapon", "net")
EXTENSION_PREFIXES = ("buy:", "sell:")


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, streams, ids, ctx):
        self.tuning = tuning
        self.table = tuning["shop"]["upgrades"]
        self.money = ctx.get("money", 0)
        self.earned = ctx.get("earned", 0)
        self.reputation = ctx.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(ctx.get("upgrades", {}))
        self.stock = dict(ctx.get("stock", {}))
        self.time_left_ticks = int(tuning["shop"]["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
                "upgrades": {k: self.upgrades[k] for k in sorted(self.upgrades)}}

    def step(self, inp):
        events = []
        if inp.buy:
            self._buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._end("done", events)
            return events
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if self.time_left_ticks == 0:
            self._end("time", events)
        return events

    def _end(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("shop_end", {"reason": reason}))

    def _buy(self, action, events):
        if action in EXTENSION_ACTIONS or action.startswith(EXTENSION_PREFIXES):
            return  # mở rộng chưa bật: bỏ qua
        if action not in UPGRADE_FIELD or action not in self.table:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        level = self.upgrades.get(action, 0) + 1
        if level > len(self.table[action]):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = self.table[action][level - 1]["price"]
        if price > self.money:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = level
        events.append(("bought", {"upgrade": action, "level": level, "price": price, "money": self.money}))
