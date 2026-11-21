# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | lit1numyt (TV2) | Khung `step()` quan + lát 3 khách + kiểm scenario quan; 15 test mới, toàn bộ unittest xanh | TV1 điền lát 4 trên khung; PO đối chiếu clarify #7–12 với PRD-0 | Chưa có nguyên văn PRD-0 mục D/E/F trong repo |
| 2 | lit1numyt (TV2) | Nhận cả `sim/quan` (bếp P1 chưa có trên main) + headless day/Shop/pause; 76 test xanh; smoke tích hợp ở `docs/proof/phase-2/integration.txt` | Gộp vào main, TV1 thêm gather v1.1 (cá, Cá Sấu), TV3 nối UI day | Gather lát 1–2 vẫn TODO trên main; chưa có tag `phase-1` |
| 1 | Đoàn Sỹ Hưng (TV3) | Test hộp đen quan, HUD + toast, 2 skill, verification, proof | Chờ review PR #5 | TV1 chưa ghi nhật ký AI (AC-QA-04) |
| 3 | Đoàn Sỹ Hưng (TV3) | Adapter kho v1.2, bật contract 1.2, HUD độ tươi, smoke bàn giao, CHANGELOG, verification | Mở PR, chờ gộp để TV1 gắn tag `phase-3` | Có sửa một dòng ở `sim/day.py` của TV2 và fixture test của cả nhóm, cần review |
| 4 | Đoàn Sỹ Hưng (TV3) | Ba cảnh báo, tương phản cao, 6 ảnh, thử clone sạch và zip | Chạy lại clone sạch, regression và verification trên commit tag | PR #19 chưa merge; cần PO quyết clarify #42 (`python` và `python3`) |
