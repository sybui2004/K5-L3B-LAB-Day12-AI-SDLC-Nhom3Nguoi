# Phase 4 — Lát C: cảnh báo dễ nhận biết + tương phản cao (TV3)

> Phần chung: [README.md](README.md). Chỉ sửa `chonoi/web/index.html` (đọc snapshot, **không chứa luật**). Ngưỡng cảnh báo là quyết định trình bày, đặt hằng số đầu file JS, không đưa vào `tuning` (không đổi contract gameplay). [clarify #32]

## C1. Ba cảnh báo

| Cảnh báo | Điều kiện (từ snapshot) | Hiển thị bắt buộc |
|---|---|---|
| Thủy quái gần | có `monsters[]` với khoảng cách tới `player.pos` ≤ `ALERT_MONSTER_NEAR` (giả định **8** đơn vị) | Băng chữ **"⚠ 🐊 Thủy quái gần!"** ở cạnh trên, thêm mũi tên chỉ hướng con gần nhất; viền quái nhấp nháy |
| Oxy sắp hết | `oxygen_ticks < 0.25 × oxygen_max_ticks` và **không** ở mặt nước (giữ ngưỡng 25 % đang có ở HUD) | Nhãn **"⚠ O₂ sắp hết — lên mặt nước!"** cạnh thanh oxy + số giây còn lại; khi `zero_oxy_ticks > 0` đổi thành **"⚠ NGẠT"** |
| Khách sắp giận | khách có `patience_ticks_left ≤ 0.25 × patience_max` và chưa được phục vụ | Biểu tượng **"😠 !"** + chữ **"Sắp giận"** trên bàn khách đó; HUD góc trên đếm "N khách sắp giận" |

- Không cảnh báo nào chỉ dựa vào màu: luôn có chữ **và** biểu tượng (emoji hoặc ký hiệu ASCII dự phòng `!!`, `O2`). Nhiều cảnh báo cùng lúc ⇒ xếp dọc, thứ tự: oxy → quái → khách.
- `patience_max`: đọc từ `meta.patience_s × 60` như HUD hiện có; nếu P3 đổi snapshot thì ưu tiên trường snapshot.
- Không phát cảnh báo ở headless (UI-only). Lớp `creative` (âm thanh) nếu bật có thể thêm tiếng, nhưng chữ/biểu tượng phải có khi `creative` tắt.

## C2. Chế độ tương phản cao
- Bật/tắt: phím **`C`** hoặc URL `?contrast=high`; nhớ lựa chọn bằng `localStorage` (bọc `try/catch`). Hiện chữ "Tương phản cao: BẬT" ở góc HUD vài giây khi đổi.
- Bảng màu: nền `#000`, chữ/đường viền `#fff`, cảnh báo nền `#ffd600` chữ `#000`, nguy hiểm viền `#ff1744` dày ≥ 3 px; bỏ gradient/hiệu ứng nước mờ; font HUD ≥ 18 px, chữ cảnh báo đậm.
- Mọi màu vẽ đi qua một đối tượng `PALETTE` (thường / cao) để đổi một chỗ.
- Thêm `C` vào dòng điều khiển ở README và màn hướng dẫn trong game (nếu có).

## C3. Kiểm chứng (bằng chứng `docs/proof/phase-4/`)
Dựng ba scenario nhỏ trong `docs/proof/phase-4/scenarios/` (chỉ để chụp, không đổi test):
1. `monster-near.json` (gather): quái đặt cách Út Sen ~5 đơn vị.
2. `oxygen-low.json` (gather): Út Sen ở đáy, oxy còn ~5 s.
3. `customer-angry.json` (quan): một khách còn ~10 % kiên nhẫn.

Chạy `python -m chonoi.live --mode gather --scenario <file>` mở `?contrast=high`, chụp: `alert-monster-hc.png`, `alert-oxygen-hc.png`, `alert-customer-hc.png` + một ảnh chế độ thường mỗi loại. Nếu scenario chưa hỗ trợ đặt quái/oxy, chơi tay tới lúc cảnh báo hiện rồi chụp, ghi cách làm trong `alerts.md`.

- `tests/test_live.py` giữ xanh (server phục vụ được trang). Không thêm test trình duyệt bắt buộc.
