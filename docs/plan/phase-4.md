# Kế hoạch Phase 4 — Ticket-04 "Phát hành v1.0.0" (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.3 (`bench_cmd`, `soak_cmd`), ba cảnh báo + tương phản cao, clone sạch ≤ 3 lệnh, CHANGELOG/LICENSE/CREDITS, retro + phản tư; tag `phase-4` và Release `v1.0.0` cùng commit trên `main` trước **3:00**.
- **Spec:** [`docs/spec/phase-4/`](../spec/phase-4/README.md) · **Verification:** [`docs/verification/phase-4.md`](../verification/phase-4.md)
- **Không làm Mở rộng** (nhóm 4 người): leaderboard, phụ đề SFX. `extensions: []`.

## Việc / người / phụ thuộc

| # | Việc | Người | Phụ thuộc | Checklist |
|---|---|---|---|---|
| 0 | Phase 3 đã gộp vào `main` (gameplay v1.2) | TV1 (Integrator) | — | trước phút 0 nếu được |
| A | `chonoi.bench` + `bench.js` + test công thức | TV1 | — | mục TV1 |
| B | `chonoi.soak` + bot tối thiểu + `DaySim` > 5 Ngày + test | TV2 | — | mục TV2 |
| C | Ba cảnh báo + tương phản cao + ảnh chụp | TV3 | — | mục TV3 |
| D | Contract 1.3, README, AGENTS, CHANGELOG, LICENSE, CREDITS, zip, tag, Release | TV1 (+TV3 clone sạch) | A, B | mục TV1, TV3 |
| E | Retro, members × 4, verification, clarify, ai-usage-log | TV2 điều phối, mọi người | — | mục TV2 |

## Mốc giờ

| Phút | Giờ | Việc |
|---|---|---|
| 0–2 | 2:30–2:32 | Đọc spec, **gật**; PO mở clarify #35–39 (#39 hỏi giảng viên giấy phép) |
| 2–15 | 2:32–2:45 | Song song A, B, C trên nhánh ngắn; TV3 thử clone sạch bản `main` hiện tại (B1) để lộ lỗi sớm; TV1 nháp CHANGELOG + release notes |
| **15** | **2:45** | Gộp A → B → C, test xanh mỗi lần; **bật `"1.3"`**; chạy bench + soak trên commit ứng viên, lưu proof |
| 15–25 | 2:45–2:55 | Retro + members (mỗi người ≤ 200 từ, tự commit); **phút 20 standup** ghi `docs/standup.md`, ai xong sang hỗ trợ; TV3 điền verification, clone sạch lần cuối + zip |
| 25–30 | 2:55–3:00 | TV1 kiểm commit/proof/sha, tag `phase-4` + `v1.0.0`, `gh release create` **chậm nhất 3:00** |

## Checklist theo người

### TV1 (sybui2004) — lát A, D · Release/Integrator
- [ ] `chonoi/bench.py`, `chonoi/web/bench.js`, route `/bench/*` trong `live.py`, `tests/test_p4_bench.py` theo [bench-soak.md](../spec/phase-4/bench-soak.md) A.
- [ ] Contract 1.3 (3 khóa), `contract.py` nhận 1.3; README mục chạy/lệnh/giới hạn; `AGENTS.md`; `CHANGELOG.md` theo phase; `LICENSE`; `CREDITS.md`.
- [ ] `docs/release-notes-v1.0.0.md`; tag + Release theo [release-docs.md](../spec/phase-4/release-docs.md) C.
- [ ] `docs/members/sybui2004.md`.

### TV2 (lit1numyt, Khoa) — lát B, E · PO + điều phối retro
- [ ] Ghi clarify #35–39, hỏi trợ giảng/giảng viên (#39 giấy phép).
- [ ] `chonoi/soak.py`, `chonoi/sim/bot.py`, `DaySim` chạy > 5 Ngày (CLI headless vẫn 1..5), `tests/test_p4_soak.py` theo [bench-soak.md](../spec/phase-4/bench-soak.md) B.
- [ ] `docs/retro.md` theo [release-docs.md](../spec/phase-4/release-docs.md) D1; nhắc đủ 4 file members; `docs/members/lit1numyt.md`.

### TV3 (hgmdz1210, Hưng) — lát C, đóng gói, Bench/QA
- [ ] Cảnh báo + tương phản cao theo [alerts-ui.md](../spec/phase-4/alerts-ui.md); 6 ảnh chụp vào `docs/proof/phase-4/`.
- [ ] Clone sạch 3 lệnh trên Linux/macOS/WSL + thử zip ⇒ `clean-clone.txt`.
- [ ] Regression đầy đủ ⇒ `unittest.txt`; `docs/verification/phase-4.md`; `docs/ai-usage-log.md`; `docs/members/hgmdz1210.md`.

### Sang Phan (sangdaden) — admin
- [ ] Kiểm quyền repo/Release (người tạo Release có quyền Write); `docs/members/sangdaden.md` (phần đã làm + đánh giá chéo).

## Rủi ro
- **Phase 3 chưa gộp** ⇒ v1.3 phải giữ gameplay v1.2. Phút 15 chưa có: vẫn bật 1.3, ghi "Giới hạn đã biết" + verification trung thực.
- **Máy chấm không có Chrome** ⇒ bench thoát mã 3 có hướng dẫn; README nêu yêu cầu; hỗ trợ `CHONOI_BROWSER`.
- **Headless Chrome giới hạn rAF / không GPU** ⇒ số FPS chỉ để báo cáo; ghi máy + trình duyệt trong `bench-run.txt`.
- **Soak 10 Ngày chậm** (`Fraction`) ⇒ đo thời gian ở phút 10; nếu > 60 s vẫn chấp nhận (không chấm thời gian), test 10 Ngày để sau cờ `CHONOI_SLOW`.
- **Live chưa có `--mode day`** ⇒ demo theo [release-docs.md](../spec/phase-4/release-docs.md) C (gather → file kho → quan, Shop qua headless). Không mở rộng phạm vi P4 để làm UI day nếu chưa xong lõi.
- **Proof khác commit tag** ⇒ thứ tự X (code) → X+1 (chỉ docs/proof) → tag X+1, ghi sha X trong verification.
