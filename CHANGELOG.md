# Changelog
## Unreleased

## [phase-3] Test Contract v1.2 — BREAKING
- File kho: `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}`, sắp theo id; kho đếm bị từ chối (mã 2).
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id.
- JSONL: `hold`, `stock`, `reserved`, `lost`, `gather_end.inventory` theo schema mới; thêm event `spoiled`; `cook_started.items`; giá món theo độ tươi (`base_price`).
- Manifest: `contract_version` là `1.2`, thêm `tuning.freshness`.
- HUD: giỏ và kho quán hiện độ tươi và hàng ươn.
- Sửa lỗi: mode `day` không còn làm tròn độ tươi khi bàn giao từ giỏ sang kho quán.
- Cập nhật fixture: `{"ca_loc":2}` → `[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"ca_loc","fresh":100}]`.
