# Bằng chứng cảnh báo và tương phản cao (AC-P4-10..13)

Ngưỡng theo clarify #35, là hằng số trình bày trong `chonoi/web/index.html`, không thuộc `tuning`.

| Cảnh báo | Điều kiện | Hiển thị | Thường | Tương phản cao |
|---|---|---|---|---|
| Thủy quái gần | quái cách người chơi ≤ 8 đơn vị | "⚠ 🐊 Thủy quái gần!", mũi tên chỉ hướng con gần nhất, viền quái nhấp nháy | [ảnh](alert-monster.png) | [ảnh](alert-monster-hc.png) |
| Oxy sắp hết | oxy < 25 % và không ở mặt nước | "⚠ O₂ sắp hết — lên mặt nước!" kèm số giây; khi ngạt đổi thành "⚠ NGẠT, hết hơi!" | [ảnh](alert-oxygen.png) | [ảnh](alert-oxygen-hc.png) |
| Khách sắp giận | khách chờ còn ≤ 25 % kiên nhẫn | "😠 ! Sắp giận" trên bàn, HUD đếm "N khách sắp giận" | [ảnh](alert-customer.png) | [ảnh](alert-customer-hc.png) |

Máy không có font biểu tượng thì dùng ký hiệu ASCII: `!!`, `O2`, `>:(`.

## Tương phản cao
- Bật hoặc tắt bằng phím `C`, hoặc mở `?contrast=high`. Lựa chọn được lưu trong `localStorage`, trình duyệt chặn lưu thì vẫn áp dụng cho lượt đang chơi.
- Nền đen, chữ trắng, cảnh báo nền vàng chữ đen, viền đỏ 3 px, không gradient và không cảnh trang trí.
- Mọi màu canvas đi qua `PALETTE` trong `chonoi/web/index.html`.

## Cách tái hiện
```bash
python -m chonoi.live --mode gather --scenario docs/proof/phase-4/scenarios/monster-near.json
python -m chonoi.live --mode gather --scenario docs/proof/phase-4/scenarios/oxygen-low.json
python -m chonoi.live --mode quan --scenario docs/proof/phase-4/scenarios/customer-angry.json
```
Mở địa chỉ in ra, thêm `?contrast=high` để xem chế độ cao.

## Đã kiểm
Chrome headless 1280×720 trên code thật: cả 6 trường hợp hiện đúng cảnh báo, phím `C` bật và tắt được, lựa chọn còn sau khi tải lại trang, không có lỗi JavaScript. Chưa có người chơi kiểm tra trực tiếp.
