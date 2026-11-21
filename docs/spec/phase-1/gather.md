# Spec `sim/gather` — Buổi sáng: Lặn & Hái (lát 1 + lát 2)

**Chủ:** Thành viên 1 · **File:** `chonoi/sim/gather.py` · **Test:** `tests/test_gather_rules.py` · **Plan:** [../../plan/phase-1/gather.md](../../plan/phase-1/gather.md)
**Trạng thái lúc chia việc:** code lát 1 + 2 đã viết (chưa commit), test đơn vị đã có; chờ review và PO chốt giả định clarify #1–5.

## Hệ tọa độ
Mặt cắt ngang, `pos = [x, d]`, `d` là độ sâu (0 = mặt nước, dương = xuống). Biên `x ∈ [0,100]`, `d ∈ [0,30]`. Ở mặt nước khi `d <= surface_depth (0.5)`.

## Thứ tự một bước (PRD mục 13.8 "Gather")
1. Đồng hồ: `time_left_ticks`, `invuln_ticks`, `catch_cd_ticks` giảm 1 (kẹp 0); nút đang mọc giảm `regrow_ticks`, chạm 0 ⇒ `node_regrown {node_id}`.
2. Bơi + chặn mép (khung, `ramp_velocity`, `swim_speed = 4.0`, `ramp_max_ticks = 6`). So vùng đầu/cuối bước: mặt → dưới ⇒ `dive {pos}`; dưới → mặt ⇒ `surface {pos}`.
3. Oxy theo `d` **cuối bước**:
   - Mặt nước: `oxygen_ticks += oxygen_refill_per_tick (6)`, kẹp `oxygen_max = 30 s × 60 = 1800`; `zero_oxy_ticks = 0`.
   - Dưới nước: `oxygen_ticks -= 1`; từ dương xuống 0 ⇒ `oxygen_empty {pos}`.
   - Oxy = 0 và dưới nước: `zero_oxy_ticks += 1`; đủ `choke_interval_ticks (60)` ⇒ `hp -= 1`, `choke {hp}`, đặt lại bộ đếm (clarify #1: tick oxy vừa về 0 tính là tick 1).
   - `hp == 0` ⇒ `faint {pos, lost:{items}}`, giỏ rỗng, `gather_end {reason: "fainted", inventory: {items: {}}}`, **dừng bước**.
4. `interact` (cạnh lên): trong bến (`dist(pos, dock_pos) <= dock_radius`) ⇒ `gather_end docked` (xét **trước** hái). Ngược lại, chỉ khi ở mặt nước: nút `ready` gần nhất trong `interact_radius (2.0)` (bằng khoảng cách ⇒ id nhỏ):
   - Lấy `min(node_yield, chỗ trống)`; > 0 ⇒ thêm vào giỏ, `regrow_ticks = regrow_s × 60 (1200)`, `gather {node_id, kind, count}`; lấy thiếu ⇒ thêm `hold_full`.
   - Giỏ đầy hẳn ⇒ chỉ `hold_full {source, kind}`, nút giữ nguyên.
5. `catch` (cạnh lên), chỉ khi `catch_cd_ticks == 0` và dưới nước: đàn cá gần nhất trong `catch_radius (2.0)`; `fish_yield` (`ca_linh: 3`, `ca_loc: 1`) cắt theo chỗ trống; bắt trúng ⇒ đặt hồi chiêu `catch_cooldown_s × 60 (30)`, gỡ đàn khỏi bản đồ, `fish_caught {fish_id, kind, count}` (+ `hold_full` nếu thiếu chỗ). Trượt / giỏ đầy: không tốn hồi chiêu (clarify #4, #5).
6. Hết giờ ⇒ `gather_end {reason: "time"}` giữ nguyên giỏ.

## Giỏ (hold)
Mảng kind theo thứ tự nhặt (cuối mảng = mới nhất, LIFO), `hold_capacity = 12`. Xuất kho bằng `hold_to_items` (đếm, sắp theo kind).

## Tiêu chí chấp nhận (đánh số để QA truy vết)
| AC | Nội dung | Test |
|---|---|---|
| AC-G-01 | Lặn/nổi phát `dive`/`surface` đúng tick | `Oxygen.test_dive_and_surface_events` |
| AC-G-02 | Oxy trừ dưới nước, hồi ở mặt, kẹp `[0, max]` | `Oxygen.test_oxygen_drains_underwater_and_refills_at_surface` |
| AC-G-03 | `oxygen_empty` một lần, `choke` mỗi 60 tick | `Oxygen.test_oxygen_empty_then_choke_every_interval` |
| AC-G-04 | Ngất: mất giỏ, kho rỗng, `gather_end fainted` | `Oxygen.test_faint_empties_hold_and_writes_empty_inventory` |
| AC-G-05 | Hái ở mặt nước, mọc lại sau 1200 tick, `node_regrown` | `Harvest.*` |
| AC-G-06 | Không hái dưới nước; hòa khoảng cách ⇒ id nhỏ | `Harvest.test_no_harvest_underwater`, `test_nearest_tie_picks_smaller_id` |
| AC-G-07 | Bắt cá dưới nước, hồi chiêu, không bắt ở mặt | `Catch.*` |
| AC-G-08 | Giỏ đầy một phần / đầy hẳn ⇒ `hold_full` | `Harvest.test_hold_full_on_harvest`, `Catch.test_partial_room_fills_hold_then_hold_full` |
| AC-G-09 | Cập bến ⇒ ghi kho đúng một lần | `Catch.test_dock_after_catch_writes_inventory`, smoke `test_inv_01_*` |

## Ngoài phạm vi Phase 1
Cá bơi / sinh thêm, `invuln_ticks` có tác dụng, chế độ `day` (phase sau).
