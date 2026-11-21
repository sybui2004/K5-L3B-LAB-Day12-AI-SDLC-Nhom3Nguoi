# Spec `qa` + harness AI

**Chủ:** Thành viên 3 (QA lead) · **Plan:** [../../plan/phase-1/ui-qa.md](../../plan/phase-1/ui-qa.md)

## 1. Kiểm chứng (15 điểm "Kiểm chứng & bằng chứng")
- `docs/verification/phase-1.md`: mỗi AC trong [gather.md](gather.md), [quan.md](quan.md), [client-ui.md](client-ui.md) một dòng: cách kiểm, link bằng chứng, kết quả **trung thực** (đạt / chưa đạt).
- `docs/proof/phase-1/`: log `unittest` (`... -v 2>&1 | tee docs/proof/phase-1/unittest.txt`), 2 file JSONL headless mẫu của seed 1 (gather + quan; nhớ `.gitignore` chặn `*.jsonl` ⇒ lưu đuôi `.jsonl.txt` hoặc đoạn trích), lệnh so byte (`cmp a.jsonl b.jsonl`), ảnh UI.

## 2. Test hộp đen bổ sung (`tests/test_quan_rules.py`)
Viết theo kiểu `tests/test_gather_rules.py` / `tests/helpers.py` (chạy headless, đọc JSONL). Mỗi AC-Q-xx ít nhất một test; viết **trước** khi TV1/TV2 xong code (test đỏ là bình thường), báo cho chủ module khi có test đỏ thật.
- Kịch bản chuẩn: scenario quan với `stock` đủ một món, `random_customers` mặc định, đứng cạnh bếp → `interact` → đi tới bàn → `interact`.
- Kiểm tất định: chạy 2 lần cùng seed, so byte.
- Kiểm hồi quy gather: luồng `gather --inventory-out` → `quan --inventory` (đã có `test_inv_01_*`, giữ xanh).

## 3. Harness AI (10 điểm)
Tối thiểu **2 skill/hook/command nhóm tự viết** trong `.agents/skills/`:
1. `.agents/skills/phase-check/SKILL.md` — "trước khi đẩy/gắn tag": chạy unittest, `tools/check_team.py`, headless 2 mode seed 1, so byte 2 lần chạy, in bảng đạt/không đạt.
2. `.agents/skills/clarify-log/SKILL.md` — khi gặp chỗ PRD mơ hồ: thêm dòng vào `docs/clarify.md` đúng định dạng bảng (#, ngày giờ, câu hỏi, giả định, ai quyết) và ghi giả định vào docstring chỗ code liên quan.
- Cập nhật mục "Skills / hooks của nhóm" trong `AGENTS.md` (tên + khi nào dùng).
- `docs/ai-usage-log.md`: mỗi người ghi ≥ 1 dòng/phase (prompt chính, AI sai ở đâu, sửa thế nào).

## AC
| AC | Nội dung |
|---|---|
| AC-QA-01 | `docs/verification/phase-1.md` phủ hết AC, có link bằng chứng |
| AC-QA-02 | `tests/test_quan_rules.py` có test cho AC-Q-01..12 |
| AC-QA-03 | 2 skill trong `.agents/skills/`, `AGENTS.md` đã liệt kê |
| AC-QA-04 | `docs/ai-usage-log.md` có mục của cả 3 người |
