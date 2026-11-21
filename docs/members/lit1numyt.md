# lit1numyt (Khoa, TV2) — phản tư

- **Tôi đã làm:** toàn bộ `sim/quan` — khách (`5683266`), bếp/phục vụ/đóng ca (`55051ff`), độ tươi, giữ theo id (`c5d424c`); `--mode day`, Shop, pause (`daa20a0`, `dbc06c3`); soak 10 Ngày. PO: clarify #7–12, #20–34, verification AC-P2-10..23.
- **Đã giúp ai:** nhận bếp lát 4 khi TV1 chưa đẩy; làm day/pause vốn trong plan của TV3; viết hàm cá thể (`b93b4f3`) khi lát A chưa có trên `main`.
- **AI sai ở đâu, phát hiện thế nào:** (1) P2 AI code trước khi đọc spec nhóm ⇒ lệch hợp đồng 3.2; đối chiếu spec và đề rồi sửa (`dbc06c3`). (2) Kỳ vọng test sai (đếm bước pause; hàng 31 điểm ươn ở tick 241, không phải 240) — test đỏ, đọc lại luật, sửa test, giữ luật. (3) Ví dụ giá trong spec P3 mâu thuẫn luật "giá sau hao" — ghi clarify #29.
- **Bài học:** đọc plan nhóm trước khi giao việc cho AI; commit nhỏ, chạy test ở từng commit; ghi giả định vào clarify ngay.
