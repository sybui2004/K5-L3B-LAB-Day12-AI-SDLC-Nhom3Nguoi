# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | lit1numyt (TV2) | Claude Code (Opus 5.5) | Lát 3 quan: khung `step()`, khách đến/chọn món/giữ chỗ/kiên nhẫn, kiểm scenario quan (mã 2), `tests/test_quan_customers.py` | — | Spec ghi trường khách `dish`/`patience_ticks`; AI đối chiếu client khung (`index.html` đọc `dish_id`, `patience_ticks_left`) và sửa spec theo khung (clarify #7). |
| 2 | lit1numyt (TV2) | Claude Code (Opus 5.5) | Quán v1.1 (bếp, phục vụ, tiền, đóng ca, 2 bếp/4 bàn, 6 món), `--mode day`, Shop, pause, contract 1.1 (quan/menu/day_plan/shop), 26 test mới | — | AI tự viết sai 2 kỳ vọng test (đếm số bước pause thiếu 1; tìm snapshot ở tick không ghi) — test đỏ, đọc lại luật pause trong ticket 4.2 rồi sửa test, luật giữ nguyên. |
