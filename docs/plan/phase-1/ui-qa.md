# Plan — Thành viên 3: `client/ui` + `qa` + harness (QA lead, Scrum)

Spec: [../../spec/phase-1/client-ui.md](../../spec/phase-1/client-ui.md), [../../spec/phase-1/qa-harness.md](../../spec/phase-1/qa-harness.md)
Nhánh: `feature/ui-qa-phase-1` (gộp ba việc dự kiến `feature/ui-hud`, `feature/qa-quan-tests`, `feature/agent-skills`)

## Bước 0 — Kickoff (0:00–0:15)
- [x] Ghi standup đầu phase vào `docs/standup.md` (dòng của TV3).
- [x] Dựng khung `docs/verification/phase-1.md`: một dòng cho mỗi AC (AC-G, AC-Q, AC-UI, AC-QA).

## Bước 1 — Test trước (0:15–0:30)
- [x] `tests/test_quan_rules.py`: test hộp đen AC-Q-01..12 (dùng `tests/helpers.py`). Đẩy sớm để TV1/TV2 chạy được.
- [x] `.agents/skills/phase-check/SKILL.md` và `.agents/skills/clarify-log/SKILL.md`; cập nhật mục "Skills / hooks" trong `AGENTS.md`.

## Bước 2 — UI (0:30–0:45)
- [x] HUD gather + quan trong `chonoi/web/index.html` theo bảng trường snapshot; toast sự kiện.
- [x] `test_live.py` xanh; luồng gather → `--inventory-out kho.json` → quan `--inventory kho.json` nạp đúng kho.
- [ ] Chơi trọn gather và quan trên luật thật (chờ TV1, TV2 đẩy luật).

## Bước 3 — Bằng chứng (0:45–0:55)
- [x] Log unittest, JSONL mẫu (đuôi `.jsonl.txt`), kết quả `cmp`, ảnh UI vào `docs/proof/phase-1/`.
- [x] Điền kết quả trung thực vào `docs/verification/phase-1.md`.
- [ ] Nhắc cả nhóm ghi `docs/ai-usage-log.md` (mới có dòng của TV3).
- [ ] Chạy lại `phase-check --proof` và cập nhật verification sau khi gộp luật.

## Dự phòng
Người dự phòng của TV3 là TV2 (test quan); nếu UI trễ, ưu tiên bằng chứng + verification trước HUD.
