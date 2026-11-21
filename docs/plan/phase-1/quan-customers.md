# Plan — Thành viên 2: `sim/quan` lát 3 (khách) + scenario quan + PO

Spec: [../../spec/phase-1/quan.md](../../spec/phase-1/quan.md) mục 0, A · Hợp đồng chung: [../../spec/phase-1/README.md](../../spec/phase-1/README.md)
Nhánh: `feature/quan-customers`

## Bước 0 — PO (0:00–0:15)
- [ ] Mở tab Phase 1 trên lab board, đối chiếu từng mục **[đối chiếu PRD-0]** trong `quan.md` và `gather.md`; sửa spec nếu khác.
- [ ] Trả lời / ghi vào `docs/clarify.md`: clarify #1–5 (gather) và 5 câu hỏi mở cuối `quan.md`. Câu hỏi PRD không trả lời được ⇒ hỏi giảng viên ("Anh Năm hàng xóm" trên lab board).

## Bước 1 — Khung `step()` (≤ 0:20, đẩy sớm để TV1 làm song song)
- [ ] Viết thứ tự gọi hàm trong `QuanSim.step()` như spec mục 0, tất cả hàm rỗng.
- [ ] Unittest xanh ⇒ commit + push `main` (hoặc gộp ngay), báo TV1.

## Bước 2 — Lát 3 (0:20–0:45)
- [ ] `_can_cook`, `_reserve`, `_release` (phần kho chưa giữ chỗ = `stock - Σ reserved`).
- [ ] `_spawn_customer`: lịch 120 / mỗi 900 tick, bàn trống id nhỏ, chọn món qua `self.rng.get("customers")`, `no_dish`, `customer_arrived`; tôn trọng `random_customers: false`.
- [ ] `_tick_customers`: giảm kiên nhẫn, `customer_left`, uy tín `-0.5` kẹp `[0,5]`.
- [ ] Khách dựng sẵn từ scenario: suy ra `reserved` nếu thiếu; cập nhật `snapshot()`.
- [ ] `_validate_quan`: thêm các luật mâu thuẫn mục A4 ⇒ `BadInput`.
- [ ] Chạy `tests/test_quan_rules.py` (TV3 viết) cho AC-Q-01..06 + smoke.

## Dự phòng
Nếu TV3 vướng UI: TV2 viết thêm test exit-2 cho scenario. Người dự phòng của TV2 là TV1.
