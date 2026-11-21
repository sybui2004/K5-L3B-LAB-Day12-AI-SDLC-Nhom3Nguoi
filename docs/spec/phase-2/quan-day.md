# Spec Phase 2 — Quán v1.1 + mode `day` + Shop + pause (TV2: lit1numyt)

Nguồn: TICKET-02 mục 1.3, 2, 4. Giả định ngoài ticket: [`docs/clarify.md`](../../clarify.md) #13–#20.

## Chia việc Phase 2 (đã chốt với nhóm)
| Lát ticket | Chủ |
|---|---|
| (1) số chuẩn gather + cá bơi/sinh, (2) Cá Sấu, Máu, ngất | TV1 (sybui2004) |
| (3) 2 bếp/4 bàn, 6 món, kế hoạch ngày + **toàn bộ `sim/quan`** (gồm bếp lát 4 của P1) | TV2 (lit1numyt) |
| (4) headless `day`, Shop, pause | TV2 |
| (4) menu, DayIntro/EveningIntro/DayResult/Summary, HUD, pause menu | TV3 (hgmdz1210) |

## File
- `chonoi/sim/quan.py` — luật quán v1.1. `QuanSim(..., dishes=None, carry=None)`: `dishes` lọc menu theo kế hoạch (day), `carry` mang tiền/earned/uy tín.
- `chonoi/sim/day.py` — `DaySim`: vòng Ngày, bàn giao kho trong bộ nhớ, Shop, áp cấp oxygen/hp từ Ngày kế (ghi đè `oxygen_max_s`/`hp_max` trong bản sao tuning gather).
- **File khung đã sửa (báo nhóm):** `runner.py` (pause, `sim_tick`/`phase_tick`, vỏ event có `day`, sự kiện tick 0, snapshot khi đổi pha, `days_completed`), `headless.py` (`--days`, mở `--mode day`), `inputs.py` (`pause`, `shop_done`, `buy`), `inventory.py` (thêm `ca_keo`, `keo_neo`), `scenario.py` (khối `day`, kiểm quán).
- `game.contract.json`: `contract_version 1.1`, `quan` (B2, T2–T4), `menu` 6 món, `day_plan` D1–D5, `shop`. **Phần `gather` v1.1 (fish_*, monsters, N5/N6) do TV1 thêm.**

## Giao diện cho TV1 (gather)
- Nếu `GatherSim.__init__` có tham số `day`, `DaySim` truyền số Ngày (cho `from_day` của Cá Sấu M2). Không có thì bỏ qua.
- `DaySim` đọc `child.done`, `child.reason`, `child.inventory_items()`; `fainted` ⇒ kho bàn giao rỗng.
- Oxy/Máu theo cấp: `DaySim` truyền tuning đã ghi đè `gather.oxygen_max_s` / `gather.hp_max` — gather chỉ cần đọc từ `self.t`.

## Giao diện cho TV3 (UI)
Snapshot `day`: mọi trường của pha hiện tại + `day`, `days_completed`, `day_plan {dishes, ingredients}`, `upgrades`, `active_upgrades`; `state: "paused"` khi tạm dừng; Shop có `stock`, `time_left_ticks`. Quán thêm `shift_earned`, khách có `order_status`, bếp có `order_id`. Input live: `LiveInputs.set(pause=..., shop_done=..., buy="oxygen")`.

## AC (TV2)
| AC | Nội dung | Test |
|---|---|---|
| AC-P2-Q1 | contract 1.1: 2 bếp, 4 bàn, 6 món, 6 nguyên liệu, `day_plan` = Σ công thức × suất | `test_quan_kitchen.Data.*` |
| AC-P2-Q2 | Bếp lấy đơn reserved cũ nhất (order_tick, id bàn); nấu → chín; nhặt khi tay trống | `test_quan_kitchen.Stove.*` |
| AC-P2-Q3 | Phục vụ, trả tiền, boa `floor(giá×0.2)` khi ≥ 50% kiên nhẫn, uy tín +0.2 | `test_quan_kitchen.Serve.*` |
| AC-P2-Q4 | Đóng ca: khách ăn trả ngay, khách chờ rời không trừ uy tín, dọn bếp/tay/giữ chỗ | `test_quan_kitchen.CloseShift.*` |
| AC-P2-Q5 | Khách vào 4 bàn theo id, lịch 120 + 900k, chọn đều theo seed | `test_quan_customers.*` |
| AC-P2-D1 | `--mode day`: thứ tự day_start → day_plan → phase_start, đổi pha cùng tick, kết thúc `days_complete`, ≤ 22.200 tick/Ngày | `test_day.DayLoop.*` |
| AC-P2-D2 | Bàn giao kho gather → quán trong bộ nhớ; khách chỉ gọi món trong kế hoạch | `test_day.DayLoop.test_handoff_inventory_to_quan_and_plan_filter` |
| AC-P2-D3 | Shop: bought / buy_failed (funds, max_level, unknown), đúng giá vẫn mua, cấp áp từ Ngày kế | `test_day.Shop.*` |
| AC-P2-D4 | Pause: tick tăng, sim_tick/phase_tick/timer đứng, bỏ qua hành động | `test_day.Pause.*` |
| AC-P2-D5 | `--days` 1..5, scenario day mâu thuẫn ⇒ mã 2 | `test_day.BadInput.*` |
| AC-P2-D6 | Headless 1 Ngày ≤ 20 s, cùng seed giống từng byte | [`proof/phase-2/integration.txt`](../../proof/phase-2/integration.txt) |

## Test cũ đã đổi (lý do)
- `test_smoke_p1.test_con_03_old_and_future_modes_rejected`: bỏ `day` khỏi danh sách mode bị từ chối (v1.1 mở `day`).
- `test_quan_customers`: 3 test viết cho 1 bàn (P1) → 4 bàn (v1.1); `customer_left` thêm `reason`.
