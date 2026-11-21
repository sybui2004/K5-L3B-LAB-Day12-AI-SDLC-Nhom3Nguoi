# TEAM

**Tên nhóm:** Nhom3Nguoi  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

> Nhóm có 4 người: 3 thành viên làm việc + 1 admin (Sang Phan, không nhận module). Trước đó nhóm được phép làm 3 người (xem [`docs/clarify.md`](docs/clarify.md) #6).

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Thành viên 1 (điền tên) | sybui2004 | `sim/gather` + `sim/quan` lát 4 | Integrator · Scrum/Release | Thành viên 2 |
| Đồng Hữu Nguyên Khoa | lit1numyt | `sim/quan` lát 3 + `scenario` | PO | Thành viên 3 |
| Đoàn Sỹ Hưng | hgmdz1210 | `client/ui` + `qa` | QA lead | Thành viên 1 |
| Sang Phan | sangdaden | — (admin, không nhận module) | Admin | — |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Nhiệm vụ Phase 1 (PRD-0)

Spec chung (Test Contract, hợp đồng kho, bảng sự kiện, giao diện sim ↔ UI): [`docs/spec/phase-1/README.md`](docs/spec/phase-1/README.md) · Kế hoạch tổng + mốc giờ: [`docs/plan/phase-1.md`](docs/plan/phase-1.md)

### Thành viên 1 — `sim/gather` + `sim/quan` lát 4 · Integrator/Release
- Hoàn tất gather lát 1+2 (oxy, ngạt, Máu, ngất, hái, bắt cá, giỏ, cập bến) — code đã viết, chờ review + PO chốt clarify #1–5.
  - Spec: [`docs/spec/phase-1/gather.md`](docs/spec/phase-1/gather.md) · Plan: [`docs/plan/phase-1/gather.md`](docs/plan/phase-1/gather.md)
- Quan lát 4: interact bếp/bàn, nấu, bưng, phục vụ, trả tiền, boa, uy tín.
  - Spec: [`docs/spec/phase-1/quan.md`](docs/spec/phase-1/quan.md) (mục 0, B) · Plan: [`docs/plan/phase-1/quan-kitchen.md`](docs/plan/phase-1/quan-kitchen.md)
- Chốt `docs/contracts/`, gộp nhánh, gắn tag `phase-1` trước 1:00.

### Thành viên 2 — `sim/quan` lát 3 + `scenario` · PO
- Đối chiếu spec với PRD-0 trên lab board, giữ `docs/clarify.md`.
- Khung `step()` quan (đẩy sớm), khách đến theo lịch, chọn món, giữ chỗ nguyên liệu, kiên nhẫn, `customer_left`, `no_dish`; kiểm mâu thuẫn scenario quan (mã 2).
  - Spec: [`docs/spec/phase-1/quan.md`](docs/spec/phase-1/quan.md) (mục 0, A) · Plan: [`docs/plan/phase-1/quan-customers.md`](docs/plan/phase-1/quan-customers.md)

### Thành viên 3 — `client/ui` + `qa` · QA lead
- HUD gather/quan trên `chonoi.live`, toast sự kiện.
  - Spec: [`docs/spec/phase-1/client-ui.md`](docs/spec/phase-1/client-ui.md) · Plan: [`docs/plan/phase-1/ui-qa.md`](docs/plan/phase-1/ui-qa.md)
- Test hộp đen quan (`tests/test_quan_rules.py`), `docs/verification/phase-1.md`, `docs/proof/phase-1/`, 2 skill trong `.agents/skills/`, `docs/ai-usage-log.md`.
  - Spec: [`docs/spec/phase-1/qa-harness.md`](docs/spec/phase-1/qa-harness.md) · Plan: [`docs/plan/phase-1/ui-qa.md`](docs/plan/phase-1/ui-qa.md)

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: … (nhóm chat chung)
- Khi bất đồng về thiết kế: nói 2 phút, không xong thì Integrator (TV1) quyết và ghi lý do vào `docs/adr/`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng (cột cuối bảng) nhận việc.
- Giờ standup giữa phase: phút thứ 30 của mỗi phase, ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát kế bên (TV1 ↔ TV2 đọc `quan.py` của nhau, TV3 đọc gather) trước khi gộp.
- Cách làm việc với Git: nhánh ngắn `feature/<module>-<việc>`, chạy test xanh rồi gộp vào `main`; TV1 gắn tag.
