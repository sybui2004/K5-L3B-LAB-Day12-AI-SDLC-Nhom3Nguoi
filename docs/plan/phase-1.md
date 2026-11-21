# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** Lõi PRD-0 chạy đúng Test Contract v1.0 — gather (lặn, oxy, hái, bắt cá, kho) + quan (khách, bếp, phục vụ, tiền, uy tín); luồng kho gather → quan; tag `phase-1` trước **1:00**. Spec: [`docs/spec/phase-1/`](../spec/phase-1/README.md).

- **Việc / người / phụ thuộc:**

| # | Việc | Người | Phụ thuộc | Plan chi tiết |
|---|---|---|---|---|
| 1 | Điền TEAM.md, chốt hợp đồng `docs/contracts/` | TV1 (Integrator) | — | [gather.md](phase-1/gather.md) bước 0 |
| 2 | Đối chiếu spec với PRD-0, ghi clarify | TV2 (PO) | — | [quan-customers.md](phase-1/quan-customers.md) bước 0 |
| 3 | Gather lát 1+2: review, chốt clarify #1–5, commit | TV1 | #2 | [gather.md](phase-1/gather.md) |
| 4 | Khung `step()` quan + lát 3 khách + scenario quan | TV2 | #2 | [quan-customers.md](phase-1/quan-customers.md) |
| 5 | Quan lát 4 bếp/bưng/phục vụ/tiền | TV1 | #3, khung của #4 | [quan-kitchen.md](phase-1/quan-kitchen.md) |
| 6 | Test hộp đen quan, HUD, verification, 2 skill | TV3 | spec | [ui-qa.md](phase-1/ui-qa.md) |
| 7 | Tích hợp, chạy `phase-check`, gắn tag `phase-1` | TV1 + TV3 | #3–#6 | [gather.md](phase-1/gather.md) bước cuối |

- **Mốc giờ:** 0:00–0:15 kickoff (TEAM.md, hợp đồng, đọc PRD-0) · 0:15–0:45 làm song song · 0:45 đóng băng tính năng, gộp nhánh · 0:45–0:55 test + bằng chứng · 0:55 gắn tag.
- **Rủi ro:**
  - Chỉ 3 người (đã được phép, clarify #6) ⇒ mỗi người ôm nhiều việc; ưu tiên lõi đúng trước, cắt phần sáng tạo.
  - Spec quan suy từ khung code, chưa trích nguyên văn PRD-0 ⇒ PO đối chiếu ngay đầu phase (mục **[đối chiếu PRD-0]**).
  - Hai người sửa `chonoi/sim/quan.py` ⇒ chia theo hàm, TV2 đẩy khung `step()` trước, gộp thường xuyên.
  - Hết giờ chưa xong lát 4 ⇒ gắn tag với phần đã xanh, ghi "chưa đạt" trung thực trong verification.
