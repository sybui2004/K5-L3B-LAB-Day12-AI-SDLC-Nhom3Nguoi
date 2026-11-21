# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | lit1numyt (TV2) | Claude Code (Opus 5.5) | Lát 3 quan: khung `step()`, khách đến/chọn món/giữ chỗ/kiên nhẫn, kiểm scenario quan (mã 2), `tests/test_quan_customers.py` | — | Spec ghi trường khách `dish`/`patience_ticks`; AI đối chiếu client khung (`index.html` đọc `dish_id`, `patience_ticks_left`) và sửa spec theo khung (clarify #7). |
