# Plan — Thành viên 3: `client/ui` + `qa` + harness (QA lead, Scrum)

Spec: [../../spec/phase-1/client-ui.md](../../spec/phase-1/client-ui.md), [../../spec/phase-1/qa-harness.md](../../spec/phase-1/qa-harness.md)
Nhánh: `feature/ui-hud`, `feature/qa-quan-tests`, `feature/agent-skills`

## Bước 0 — Kickoff (0:00–0:15)
- [ ] Ghi standup đầu phase vào `docs/standup.md` (ai làm gì, vướng gì).
- [ ] Dựng khung `docs/verification/phase-1.md`: một dòng cho mỗi AC (AC-G, AC-Q, AC-UI, AC-QA).

## Bước 1 — Test trước (0:15–0:30)
- [ ] `tests/test_quan_rules.py`: test hộp đen AC-Q-01..12 theo kiểu `tests/test_gather_rules.py` (dùng `tests/helpers.py`). Đẩy sớm để TV1/TV2 chạy được.
- [ ] `.agents/skills/phase-check/SKILL.md` và `.agents/skills/clarify-log/SKILL.md`; cập nhật mục "Skills / hooks" trong `AGENTS.md`.

## Bước 2 — UI (0:30–0:45)
- [ ] HUD gather + quan trong `chonoi/web/index.html` theo bảng trường snapshot; toast sự kiện.
- [ ] `test_live.py` xanh; chơi thử gather → `--inventory-out kho.json` → quan `--inventory kho.json`.

## Bước 3 — Bằng chứng (0:45–0:55)
- [ ] Log unittest, JSONL mẫu (đuôi `.jsonl.txt`), kết quả `cmp`, ảnh UI vào `docs/proof/phase-1/`.
- [ ] Điền kết quả trung thực vào `docs/verification/phase-1.md`.
- [ ] Nhắc cả nhóm ghi `docs/ai-usage-log.md`.

## Dự phòng
Người dự phòng của TV3 là TV2 (test quan); nếu UI trễ, ưu tiên bằng chứng + verification trước HUD.
