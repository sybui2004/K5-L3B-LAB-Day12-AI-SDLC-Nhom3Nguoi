# Plan — Thành viên 1: `sim/quan` lát 4 (bếp, bưng, phục vụ, tiền, uy tín)

Spec: [../../spec/phase-1/quan.md](../../spec/phase-1/quan.md) mục 0, B
Nhánh: `feature/quan-kitchen` (tạo từ `main` **sau** khi có khung `step()` của TV2)

## Các bước (0:30–0:45)
- [ ] `_interact`: lọc bếp/bàn trong `interact_radius`, sắp `(dist, 0 nếu bếp / 1 nếu bàn, id_key)`, chỉ xử lý đối tượng đầu.
- [ ] `_cook`: bếp `idle`, tay trống, có khách `waiting` chưa có món đang nấu ⇒ trừ kho phần đã giữ chỗ, `cook_started`.
- [ ] `_tick_stoves`: đếm `cook_ticks_left` ⇒ `dish_ready`; `ready_ticks` chỉ đếm (`burn_s` null).
- [ ] `_pick_up`: bếp `ready`, tay trống (`carry_limit`) ⇒ `dish_picked`.
- [ ] `_serve`: bàn có khách `waiting` đúng món ⇒ `served`, chốt `price`, `tip` theo tỉ lệ kiên nhẫn.
- [ ] `_tick_eating` + `_pay`: ⇒ `paid`, cộng `money/earned/shift_earned`, uy tín `+tip_reputation` khi có boa, kẹp.
- [ ] Chạy `tests/test_quan_rules.py` cho AC-Q-07..12 + toàn bộ unittest; headless quan seed 1 chạy 2 lần, `cmp`.
- [ ] Commit, ghi kết quả test; báo TV3 các trường snapshot mới cho HUD.

## Lưu ý
- Không sửa `_spawn_customer` / `_tick_customers` của TV2; cần đổi ⇒ nhắn TV2.
- Mọi số đọc từ `self.t` và `self.menu`.
