# Spec Phase 2 (Ticket-02 — Một ngày ở chợ nổi) — phần chung

> Nguồn: lab board tab **Phase 2 — Ticket-02** (55 phút, 1:00–1:55, Test Contract v1.1). Spec này trích và sắp xếp lại đề; chỗ đề chưa rõ ghi **[clarify #n]** và nằm trong [`docs/clarify.md`](../../clarify.md).
> Kế hoạch giờ + phụ thuộc: [`docs/plan/phase-2.md`](../../plan/phase-2.md). Số liệu chuẩn dạng JSON: [contract-v1.1.md](contract-v1.1.md).

## Spec theo lát

| Lát | Nội dung | Spec | Plan | Chủ |
|---|---|---|---|---|
| 0 | Nền v1.1: `game.contract.json` 1.1, 6 nguyên liệu, kiểm hợp đồng | [contract-v1.1.md](contract-v1.1.md) | [plan/phase-2/gather.md](../../plan/phase-2/gather.md) bước 0 | TV1 (Integrator) |
| 1 | Số chuẩn gather, cá bơi, sinh cá | [gather.md](gather.md) mục A | [plan/phase-2/gather.md](../../plan/phase-2/gather.md) | TV1 |
| 2 | Cá Sấu Năm Chèo, Máu, ngất | [gather.md](gather.md) mục B | [plan/phase-2/gather.md](../../plan/phase-2/gather.md) | TV1 |
| 3 | 2 bếp / 4 bàn / 6 món, kế hoạch ngày, Shop (sim) | [quan-shop.md](quan-shop.md) | [plan/phase-2/quan-shop.md](../../plan/phase-2/quan-shop.md) | TV2 (PO) |
| 4 | `--mode day`, chuyển pha, pause, menu, HUD, QA | [day-ui.md](day-ui.md) | [plan/phase-2/day-ui-qa.md](../../plan/phase-2/day-ui-qa.md) | TV3 (QA lead) |

TV1 = sybui2004 · TV2 = lit1numyt (Khoa) · TV3 = hgmdz1210 (Hưng). Sang Phan (admin) không nhận lát.

## 1. Định nghĩa hoàn thành (DoD) — theo Ticket-02

1. `contract_version: "1.1"`, tuning chuẩn, đủ 6 nguyên liệu và 6 món theo dữ liệu. Cá bơi/sinh, Cá Sấu, Máu/ngất, 2 bếp/4 bàn chạy đúng.
2. Chơi trọn vòng ngày với menu, pause, HUD. `--mode day` công bố đúng kế hoạch D1–D5, chốt Ngày khi Shop đóng, áp cấp oxygen/hp từ Ngày kế.
3. Smoke tích hợp có bằng chứng. Regression P1 còn hiệu lực đạt với số chuẩn; test nào đổi thì ghi lý do trong commit.
4. `docs/verification/phase-2.md` + bằng chứng khớp commit gắn tag. Mỗi người có commit trong phase; `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md` cập nhật.
5. Tag `phase-2` trỏ commit bàn giao trên `main`, đẩy **trước 1:55**.

Không làm mục "Mở rộng" (nhóm 4 người không bắt buộc). Phần sáng tạo (`feature/creative-ui`) chỉ làm khi lõi xanh, luôn tắt ở headless.

## 2. Danh sách AC-P2 (dùng cho test, verification, chia việc)

| AC | Nội dung | Chủ |
|---|---|---|
| AC-P2-01 | Manifest `contract_version:"1.1"`, tuning đúng [contract-v1.1.md](contract-v1.1.md); kho/scenario nhận 6 loại: `ca_loc, ca_linh, ca_keo, bong_dien_dien, bong_sung, keo_neo` | TV1 |
| AC-P2-02 | Gather số chuẩn: N1–N6, `fish_yield` 3 loài (cá kèo 2), oxy/ngạt/hái như v1.0 với số mới | TV1 |
| AC-P2-03 | Cá bơi 1.5 m/s, miền x [4,96], dải d theo loài, đổi hướng theo seed ở bước bơi 120, 240…, phản xạ mép | TV1 |
| AC-P2-04 | Đầu ca 8 đàn ở 8 điểm khác nhau; sinh tối đa 1 đàn ở `phase_tick = 360k` theo luật trần/khoảng cách/trọng số; `fish_spawned` | TV1 |
| AC-P2-05 | Bắt cá xét theo vị trí cá **trước** khi bơi; cá mới tham gia từ bước sau | TV1 |
| AC-P2-06 | Cá Sấu patrol ↔ chase (≤ 10 m, d ≥ 10) ↔ patrol (> 16 m hoặc d < 10), chặn d ∈ [10,30]; M2 chỉ từ Ngày 3 | TV1 |
| AC-P2-07 | Chạm: −1 Máu, rơi `floor(n/2)` LIFO, bất tử 90, recoil 60 bước × 2/60 m; tối đa 1 hit/bước; `monster_hit` | TV1 |
| AC-P2-08 | Ngất do quái: `faint{cause:"monster"}`, mất giỏ, `gather_end(fainted)` ngay; ngạt xuyên bất tử, không rơi hàng | TV1 |
| AC-P2-09 | Thứ tự bước gather v1.1 (mục 4.5 đề) | TV1 |
| AC-P2-10 | Quán 2 bếp B1/B2, 4 bàn T1–T4, 6 món theo dữ liệu | TV2 |
| AC-P2-11 | Tương tác: gần nhất, hòa bếp trước bàn rồi id; bếp lấy đơn `reserved` cũ nhất theo `order_tick` rồi id bàn | TV2 |
| AC-P2-12 | Khách ở tick 120 + 900k vào ghế trống id nhỏ nhất; kiên nhẫn 3600, ăn 600; boa/uy tín như v1.0 | TV2 |
| AC-P2-13 | Đóng ca: khách đang ăn trả ngay, khách chờ rời không trừ uy tín, dọn món + phần giữ | TV2 |
| AC-P2-14 | `day_plan` D1–D5 là dữ liệu; `ingredients` = Σ công thức × suất (test tính lại) | TV2 |
| AC-P2-15 | Trong day: khách chọn đều theo seed trong món **của kế hoạch** còn đủ nguyên liệu; quán độc lập dùng cả 6 món | TV2 |
| AC-P2-16 | Shop: mua oxygen/hp theo dữ liệu, đủ đúng giá vẫn mua; trừ `money`, giữ `earned`; `bought` / `buy_failed{funds,max_level,unknown}` | TV2 |
| AC-P2-17 | Shop đóng bằng `shop_done` → `shop_end(done)` hoặc sau 600 tick hoạt động → `shop_end(time)`; `buy` xử lý trước `shop_done` cùng bước | TV2 |
| AC-P2-18 | `--mode day --days N`: chuỗi `day_start → day_plan → phase_start(gather)`, chuyển pha cùng tick, gameplay pha mới từ bước sau; `end` có `days_completed`, `reason:"days_complete"` | TV3 |
| AC-P2-19 | Xuyên Ngày: giữ money/earned/reputation/upgrades; oxy/Máu đầy theo `active_upgrades`; `active_upgrades` chỉ đổi khi dựng Ngày mới; kho dư bỏ sau Shop; ngất → quán mở với kho rỗng | TV3 |
| AC-P2-20 | Pause (cả 3 mode): cạnh `pause` → `paused`, chỉ `tick` tăng; `sim_tick`/`phase_tick`/timer đứng; bỏ qua hành động và `buy`; cạnh kế → `resumed` + chạy gameplay ngay bước đó | TV3 |
| AC-P2-21 | Scenario `day`: khối `day{money,earned,reputation,upgrades,day_plan}`, `0 ≤ money ≤ earned`; cấm `quan.stock`/`quan.reputation` → mã 2; các khóa scenario gather mới (monsters, `age_ticks`, `random_fish`, `invuln_ticks`) | TV3 (khối day) + TV1 (khóa gather) |
| AC-P2-22 | Snapshot day có `day, day_plan, upgrades, active_upgrades`, `phase ∈ gather/quan/shop`, `state:"paused"`; vỏ event có `day`; Shop có `stock`, `time_left_ticks` | TV3 |
| AC-P2-23 | Headless 1 Ngày (≤ 22.200 tick) chạy ≤ 20 s; cùng seed → file giống từng byte | TV3 |
| AC-P2-24 | Menu chính (Chơi/Thoát), DayIntro (4 s hoặc phím), EveningIntro, DayResult, Shop, Summary sau Ngày 5 | TV3 |
| AC-P2-25 | Esc/P: menu pause làm mờ nền, Tiếp tục / Về menu; dừng mọi timer kể cả trong Shop | TV3 |
| AC-P2-26 | HUD sáng + HUD quán đủ mục đề yêu cầu; chữ không chân ≥ 18 px ở 1280×720; ≥ 30 FPS | TV3 |
| AC-P2-27 | Smoke tích hợp phút 20: `gather --inventory-out` → `quan --inventory`, kho ở snapshot tick 0 khớp; lưu `docs/proof/phase-2/integration.*` | TV1 + TV3 |
| AC-P2-28 | Regression P1 với số chuẩn; test đổi có lý do; verification/clarify/ai-log/retro; tag `phase-2` trên `main` trước 1:55 | Cả nhóm (TV1 gắn tag) |

## 3. Hợp đồng chuyển pha — CHỐT ở phút 0–5, không đổi sau đó

Mọi lát code theo giao diện dưới để người làm day (TV3) tích hợp sớm bằng fixture.

### 3.1 Ba khái niệm tick
- `tick`: số bước ngoài (dòng JSONL), **tăng cả khi pause**.
- `sim_tick`: số bước gameplay đã chạy (đứng yên khi pause). Ngoài pause: `sim_tick == tick`.
- `phase_tick`: số bước gameplay trong pha hiện tại; `0` ở snapshot đổi pha. Lịch cá (`360k`) và lịch khách (`120 + 900k`) đếm theo `phase_tick` **[clarify #13]**.

### 3.2 Giao diện sim (Python)

```python
GatherSim(tuning, scenario, streams, ids, ctx=None)
QuanSim(tuning, scenario, streams, ids, inventory=None, ctx=None)
ShopSim(tuning, streams, ids, ctx)          # mới, chonoi/sim/shop.py (TV2)
DaySim(tuning, scenario, streams, ids, days) # mới, chonoi/sim/day.py (TV3)
```

`ctx` (dict, `None` = chạy độc lập, dùng mặc định Ngày 1):

| Khóa | Dùng ở | Ý nghĩa |
|---|---|---|
| `day` | gather, quan, shop | số Ngày 1..5 |
| `hp_max`, `oxygen_max_s` | gather | theo `active_upgrades` |
| `plan_dishes` | quan | map món → suất của Ngày (lọc menu); `None` = cả 6 món |
| `money`, `earned`, `reputation` | quan, shop | trạng thái xuyên Ngày |
| `upgrades` | shop | cấp đã mua `{oxygen:int, hp:int}` |
| `stock` | shop | kho dư sau ca (chỉ để hiển thị) |

Mọi sim giữ thuộc tính như v1.0: `mode, phase, done, reason, money, earned, reputation, time_left_ticks, step(inp) -> [(name, data)], snapshot() -> dict`. Thêm: gather `inventory_items()`; quan `stats()` → `{served, left, money, tips, reputation_delta, best_dish}` cho DayResult/Summary; shop `upgrades`, `money`.

- Một `Streams(seed)` cho cả lượt `day`; mỗi lát dùng tên luồng riêng: `fish`, `monsters`, `customers`, `shop` (nếu cần).
- `ids` dùng chung một `IdAllocator` cho cả lượt.

### 3.3 Bàn giao kho
Gather → quan dùng schema kho v1.0 `{"items": {kind: int}}` truyền trong bộ nhớ (không qua file). Hàng ngất = `{}`. Hai cờ `--inventory`/`--inventory-out` chỉ dùng cho hai mode độc lập.

## 4. Sự kiện mới (v1.1)

| Sự kiện | `data` | Ai phát |
|---|---|---|
| `fish_spawned` | `{id, kind, pos}` | gather (TV1) |
| `monster_hit` | `{monster_id, hp, lost:[kind… theo LIFO], pos}` (`pos` = người chơi) | gather (TV1) |
| `faint` | thêm `cause:"monster"` khi do chạm; `lost` = phần giỏ còn lại; `hp:0` | gather (TV1) |
| `day_start`, `phase_start` | `{}` | day (TV3) |
| `day_plan` | `{dishes, ingredients}` | day (TV3) |
| `paused`, `resumed` | `{}` | runner (TV3) |
| `bought` | `{upgrade, level, price, money}` | shop (TV2) |
| `buy_failed` | `{action, reason: funds\|max_level\|out_of_stock\|unknown}` | shop (TV2) |
| `shop_end` | `{reason: done\|time}` | shop (TV2) |

Vỏ event ở mode `day` có thêm khóa `day`. Event kết thúc (`gather_end`, `quan_end`, `shop_end`) mang **pha cũ**; `phase_start` mang pha mới.

## 5. File khung bị đụng (báo cả nhóm, ghi lý do trong commit)

| File | Đổi gì | Ai |
|---|---|---|
| `game.contract.json` | v1.1 + tuning chuẩn + `day_plan` + `shop` | TV1 (commit đầu tiên của phase) |
| `chonoi/inventory.py`, `chonoi/contract.py` | 6 loại nguyên liệu, kiểm khóa mới | TV1 |
| `chonoi/scenario.py` | khóa gather mới (TV1), quan (TV2), khối `day` + kiểm mã 2 (TV3) | chia theo hàm |
| `chonoi/inputs.py` | nút `pause`, `shop_done`; `buy` là chuỗi | TV3 |
| `chonoi/headless.py`, `chonoi/runner.py` | `--mode day`, `--days`, pause, `sim_tick`/`phase_tick`, `days_completed` | TV3 |
| `chonoi/live.py`, `chonoi/web/` | mode day, menu, pause, HUD | TV3 |

## 6. Quy ước Phase 2
- Nhánh: `feature/p2-gather`, `feature/p2-quan-shop`, `feature/p2-day-ui`. Gộp `main` sớm và thường xuyên; TV1 gộp.
- Số liệu chỉ đọc từ tuning; tất định qua `Streams`; duyệt qua `sort_by_id`.
- Test v1.0 sai vì số mới ⇒ sửa test, ghi `Đổi test: <lý do>` trong commit. Luật sai ⇒ sửa luật.
- Test mới đặt tên theo AC: `tests/test_p2_gather.py`, `tests/test_p2_quan_shop.py`, `tests/test_p2_day.py`.
