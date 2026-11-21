# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Tick oxy vừa về 0 có tính vào bộ đếm ngạt không? | Giả định: CÓ — oxy 1 → 0 ở tick 1 thì `choke` ở tick `choke_interval_ticks` (60). | Chờ PO xác nhận với PRD-0 |
| 2 | 2026-11-21 | `data` của sự kiện gather? | Giả định: `dive`/`surface`/`oxygen_empty` `{pos}`; `choke` `{hp}`; `faint` `{pos, lost:{items}}`; `gather` `{node_id, kind, count}`; `fish_caught` `{fish_id, kind, count}`; `hold_full` `{source, kind}`. | Chờ PO |
| 3 | 2026-11-21 | Giỏ còn chỗ nhưng ít hơn sản lượng (vd cá linh cho 3, còn 1 chỗ)? | Giả định: nhặt đầy phần còn chỗ, phát `fish_caught`/`gather` (count = số nhặt được) rồi `hold_full`. Giỏ đầy hẳn: chỉ `hold_full`, nút/cá giữ nguyên. | Chờ PO |
| 4 | 2026-11-21 | Hồi chiêu bắt cá tính khi nào? | Giả định: chỉ khi bắt TRÚNG; bấm trượt / giỏ đầy không tốn hồi chiêu. | Chờ PO |
| 5 | 2026-11-21 | Bắt xong đàn cá có biến mất? | Giả định: có, đàn cá bị gỡ khỏi bản đồ (P1 cá đứng yên, chưa sinh thêm). | Chờ PO |
| 6 | 2026-11-21 | Nhóm 3 người có được chấp nhận không (đề và `tools/check_team.py` yêu cầu 4–6)? | ĐƯỢC PHÉP làm 3 người. `team_size` = 3. `tools/check_team.py` (khung, không sửa) vẫn báo "số thành viên phải từ 4 đến 6" — đây là ngoại lệ đã được duyệt, CI chỉ cảnh báo. | Giảng viên (đã xác nhận) |
