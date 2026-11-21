---
name: clarify-log
description: Dùng khi PRD, spec hoặc contract mơ hồ hay mâu thuẫn trong lúc code hoặc viết test. Ghi câu hỏi và giả định vào docs/clarify.md đúng định dạng, rồi ghi giả định vào docstring chỗ code liên quan.
---

# clarify-log

Không tự bịa yêu cầu. Khi gặp chỗ mơ hồ:

1. Đọc `docs/clarify.md`. Nếu câu hỏi đã có thì dùng câu trả lời đó, không thêm dòng trùng.
2. Thêm một dòng vào cuối bảng, số `#` tiếp theo:

   ```markdown
   | <#> | <YYYY-MM-DD> | <Câu hỏi cụ thể, nêu trường/sự kiện/tick> | Giả định: <cách đang làm tạm> | Chờ PO |
   ```

3. Ghi giả định vào docstring hoặc comment ngay chỗ code/test phụ thuộc, kèm số dòng clarify, ví dụ `(clarify #7)`.
4. Báo PO (Thành viên 2). Chỉ PO hoặc giảng viên đổi cột "Ai quyết" khỏi `Chờ PO`.
5. Khi PO chốt khác giả định: sửa luật và test theo câu trả lời, ghi lý do trong commit.

## Quy tắc

- Mỗi dòng một câu hỏi. Dấu `|` trong nội dung phải viết thành `\|`.
- Không sửa câu trả lời đã chốt của người khác.
- Không đổi `game.contract.json` hoặc `docs/contracts/` để né câu hỏi.
