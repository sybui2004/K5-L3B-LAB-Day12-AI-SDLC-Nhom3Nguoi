# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Tick oxy vừa về 0 có tính vào bộ đếm ngạt không? | Giả định: CÓ — oxy 1 → 0 ở tick 1 thì `choke` ở tick `choke_interval_ticks` (60). | Chờ PO xác nhận với PRD-0 |
| 2 | 2026-11-21 | `data` của sự kiện gather? | Giả định: `dive`/`surface`/`oxygen_empty` `{pos}`; `choke` `{hp}`; `faint` `{pos, lost:{items}}`; `gather` `{node_id, kind, count}`; `fish_caught` `{fish_id, kind, count}`; `hold_full` `{source, kind}`. | Chờ PO |
| 3 | 2026-11-21 | Giỏ còn chỗ nhưng ít hơn sản lượng (vd cá linh cho 3, còn 1 chỗ)? | Giả định: nhặt đầy phần còn chỗ, phát `fish_caught`/`gather` (count = số nhặt được) rồi `hold_full`. Giỏ đầy hẳn: chỉ `hold_full`, nút/cá giữ nguyên. | Chờ PO |
| 4 | 2026-11-21 | Hồi chiêu bắt cá tính khi nào? | Giả định: chỉ khi bắt TRÚNG; bấm trượt / giỏ đầy không tốn hồi chiêu. | Chờ PO |
| 5 | 2026-11-21 | Bắt xong đàn cá có biến mất? | Giả định: có, đàn cá bị gỡ khỏi bản đồ (P1 cá đứng yên, chưa sinh thêm). | Chờ PO |
| 6 | 2026-11-21 | Nhóm 3 người có được chấp nhận không (đề và `tools/check_team.py` yêu cầu 4–6)? | ĐƯỢC PHÉP làm 3 người. `team_size` = 3. `tools/check_team.py` (khung, không sửa) vẫn báo "số thành viên phải từ 4 đến 6" — đây là ngoại lệ đã được duyệt, CI chỉ cảnh báo. | Giảng viên (đã xác nhận) |
| 7 | 2026-11-21 | Tên trường khách trong snapshot/scenario? | Theo client khung (`chonoi/web/index.html` đọc `c.dish_id`, `c.patience_ticks_left`): khách có `id, table_id, dish_id, state (waiting\|eating), patience_ticks_left, reserved` (+ `eat_ticks_left, price, tip` khi eating). Spec cũ ghi `dish`/`patience_ticks` ⇒ đã sửa. | PO (TV2), chờ đối chiếu PRD-0 mục D/F |
| 8 | 2026-11-21 | `data` của sự kiện khách? | `customer_arrived {customer_id, table_id, dish_id}`; `customer_left {customer_id, table_id, dish_id}`; `no_dish {table_id}` (bàn khách định ngồi). | PO (TV2), chờ PRD-0 mục E |
| 9 | 2026-11-21 | Tới lịch khách mà hết bàn trống? | Bỏ lượt, KHÔNG phát sự kiện, không dời lịch. Có bàn trống mà không món nào nấu được ⇒ `no_dish`. | PO (TV2) |
| 10 | 2026-11-21 | Lịch khách tính theo tick nào khi scenario đặt `time_left_ticks`? | Theo số bước đã chạy (tick của dòng event): khách ở tick `first_customer_tick`, rồi cứ `customer_interval_s×60`. Không phụ thuộc `time_left_ticks`. | PO (TV2) |
| 11 | 2026-11-21 | Thứ tự trong bước quan; khách bỏ đi cùng tick lịch? | `_tick_customers` → `_tick_stoves` → `_tick_eating` → đi → `interact` → khách mới. Khách hết kiên nhẫn ở tick t nhả bàn trước, nên khách mới có thể ngồi ngay tick t. Kiên nhẫn chỉ giảm khi `waiting` (kể cả khi món đang nấu). | PO (TV2), chờ PRD-0 mục F |
| 12 | 2026-11-21 | Chọn món ngẫu nhiên thế nào cho tất định? | Ứng viên = món nấu được từ kho CHƯA giữ chỗ, sắp theo tên; `Streams.get("customers").choice(...)`. Uy tín làm tròn 3 chữ số sau mỗi lần đổi, kẹp `[reputation_min, reputation_max]` (`_change_reputation`, dùng chung với lát 4). | PO (TV2) |
| 13 | 2026-11-21 (P2) | Lịch khách (120 + 900k) và lịch sinh cá (360k) đếm theo tick nào khi có pause / trong `day`? | Giả định: theo `phase_tick` (bước gameplay trong pha, đứng yên khi pause). Ở mode độc lập không pause thì trùng clarify #10. | Chờ PO (TV2) |
| 14 | 2026-11-21 (P2) | `recoil_dist` trong `species.ca_sau` là tổng quãng lùi hay quãng mỗi bước? | Giả định: TỔNG = 2.0 m (60 bước × 2/60 m). | Chờ PO |
| 15 | 2026-11-21 (P2) | 8 đàn đầu ca chọn thế nào? "8 điểm khác nhau" là khác vị trí hình học hay khác cặp loài–vị trí? | Giả định: lặp thủ tục sinh theo lịch 8 lần (trọng số loài, điểm hợp lệ cách mọi đàn > 1 m) ⇒ 8 vị trí hình học khác nhau. | Chờ PO |
| 16 | 2026-11-21 (P2) | "Đổi hướng theo seed" của cá: phân phối hướng? | Giả định: góc đều trong [0°, 360°) qua `Streams.get("fish")`. | Chờ PO |
| 17 | 2026-11-21 (P2) | Ngưỡng độ sâu phát hiện/chạm của quái (d ≥ 10 với Cá Sấu) lấy từ đâu? | Giả định: `depths[0]` của loài (Cá Sấu 10; Rắn ở mở rộng là 8). | Chờ PO |
| 18 | 2026-11-21 (P2) | `buy` = `weapon`/`net`/`buy:<kind>` khi chưa bật mở rộng: bỏ qua hay `buy_failed(unknown)`? | Giả định: bỏ qua, không event (đề: "mở rộng chưa bật thì bỏ qua"); chuỗi lạ khác ⇒ `buy_failed{reason:"unknown"}`. | Chờ PO |
| 19 | 2026-11-21 (P2) | Ba event dựng Ngày 1 (`day_start`, `day_plan`, `phase_start`) mang `tick:0` (theo ví dụ đề): ghi trước hay sau snapshot tick 0? | Giả định: snapshot tick 0 trước, rồi ba event `tick:0`. Ngày 2+ dựng ở tick đóng Shop. | Chờ PO |
