---
name: phase-check
description: Dùng trước khi đẩy nhánh, gộp vào main hoặc gắn tag phase. Chạy unittest, check_team, headless 2 mode seed 1, so byte 2 lần chạy, luồng kho gather -> quan và in bảng đạt/không đạt.
---

# phase-check

## Chạy

```bash
python .agents/skills/phase-check/phase_check.py
```

Khi chốt phase, ghi luôn bằng chứng:

```bash
python .agents/skills/phase-check/phase_check.py --proof docs/proof/phase-1
```

Lệnh `--proof` ghi `unittest.txt`, `gather-seed1.jsonl.txt`, `quan-seed1.jsonl.txt`, `cmp.txt`, `phase-check.txt`.

## Đọc kết quả

- Mã thoát 0: đạt hết, được đẩy hoặc gắn tag.
- Mã thoát 1: có mục KHÔNG ĐẠT. Không gắn tag cho tới khi sửa, hoặc ghi rõ phần chưa đạt trong `docs/verification/phase-1.md`.
- Test đỏ do luật sai thì sửa luật, không sửa test cho xanh (xem `AGENTS.md`).
- Báo đúng kết quả đã thấy. Không ghi "đạt" nếu chưa chạy.
