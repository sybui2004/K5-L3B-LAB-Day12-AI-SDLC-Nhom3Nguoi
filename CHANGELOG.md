# Changelog
## [v1.0.0 / phase-4] Test Contract v1.3
- Thêm `bench_cmd` để đo FPS, 1% low và thời gian tải khung hình đầu.
- Thêm `soak_cmd` để mô phỏng nhiều Ngày trong một tiến trình.
- Thêm cảnh báo thủy quái, oxy thấp và khách sắp giận cùng chế độ tương phản cao.

## [phase-3] Test Contract v1.2 — BREAKING
- File kho: `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}`, sắp theo id; kho đếm bị từ chối (mã 2).
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id.
- JSONL: `hold`, `stock`, `reserved`, `lost`, `gather_end.inventory` theo schema mới; thêm event `spoiled`; `cook_started.items`; giá món theo độ tươi (`base_price`).
- Manifest: `contract_version` là `1.2`, thêm `tuning.freshness`.
- HUD: giỏ và kho quán hiện độ tươi và hàng ươn.
- Sửa lỗi: mode `day` không còn làm tròn độ tươi khi bàn giao từ giỏ sang kho quán.
- Cập nhật fixture: `{"ca_loc":2}` → `[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"ca_loc","fresh":100}]`.

## [phase-2] Test Contract v1.1
- Sáu nguyên liệu, cá bơi và sinh theo lịch, Cá Sấu Năm Chèo, sát thương và ngất.
- Hai bếp, bốn bàn, sáu món, vòng Ngày Lặn → Quán → Shop và tạm dừng.

## [phase-1] PRD-0
- Luật Lặn và Quán, chuyển kho bằng file, mô phỏng headless và chơi trên trình duyệt.
