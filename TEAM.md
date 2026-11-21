# TEAM

**Tên nhóm:** Nhom3Nguoi  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

> Nhóm có 4 người: 3 thành viên làm việc + 1 admin (Sang Phan, không nhận module). Trước đó nhóm được phép làm 3 người (xem [`docs/clarify.md`](docs/clarify.md) #6).

- Repo chung là fork công khai trên GitHub, với cả bốn tài khoản trong bảng có quyền cộng tác. [Repo nhóm](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi)
- Lịch sử đến `bffd2e5` ghi nhận ít nhất 3 commit có nội dung cho mỗi người trong ba thành viên phụ trách module. Phần đóng góp của admin cần bổ sung dẫn chứng hoặc xin giảng viên xác nhận cách áp dụng yêu cầu commit.

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Bùi Thái Sỹ | sybui2004 | `sim/gather` + `sim/quan` lát 4 | Integrator · Scrum/Release | Thành viên 2 |
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

## Nhiệm vụ Phase 2 (Ticket-02 — Một ngày ở chợ nổi, Test Contract v1.1)

Spec chung (DoD, AC-P2-01…28, hợp đồng chuyển pha, sự kiện mới): [`docs/spec/phase-2/README.md`](docs/spec/phase-2/README.md) · Kế hoạch + mốc giờ: [`docs/plan/phase-2.md`](docs/plan/phase-2.md)

### Thành viên 1 (sybui2004) — lát 0, 1, 2 · Integrator/Release
- Gộp gather + quan lát 4 của P1, gắn tag `phase-1` (trễ, ghi trung thực).
- Lát 0: `game.contract.json` v1.1, 6 nguyên liệu. Spec: [`contract-v1.1.md`](docs/spec/phase-2/contract-v1.1.md)
- Lát 1: số chuẩn gather, cá bơi, sinh cá. Lát 2: Cá Sấu, Máu, ngất.
  - Spec: [`docs/spec/phase-2/gather.md`](docs/spec/phase-2/gather.md) · Plan: [`docs/plan/phase-2/gather.md`](docs/plan/phase-2/gather.md)
- Gộp nhánh, gắn tag `phase-2` trước 1:55.

### Thành viên 2 (lit1numyt) — lát 3 + Shop · PO
- 2 bếp / 4 bàn / 6 món, chọn món theo kế hoạch ngày, `plan_ingredients`, Shop (`buy`, `shop_done`).
  - Spec: [`docs/spec/phase-2/quan-shop.md`](docs/spec/phase-2/quan-shop.md) · Plan: [`docs/plan/phase-2/quan-shop.md`](docs/plan/phase-2/quan-shop.md)
- Giữ `docs/clarify.md` (#13–19), hỏi trợ giảng trên lab board.

### Thành viên 3 (hgmdz1210) — lát 4 day/pause + UI + QA · QA lead
- `--mode day`, `DaySim`, pause, scenario `day`; menu, màn Intro/Result/Shop/Summary, HUD; smoke tích hợp, verification.
  - Spec: [`docs/spec/phase-2/day-ui.md`](docs/spec/phase-2/day-ui.md) · Plan: [`docs/plan/phase-2/day-ui-qa.md`](docs/plan/phase-2/day-ui-qa.md)

## Nhiệm vụ Phase 3 (Ticket-03 — Change Request "Mùa Nước Nổi", Test Contract v1.2)

Spec chung (DoD, AC-P3-01…16, bảng tác động, schema cá thể): [`docs/spec/phase-3/README.md`](docs/spec/phase-3/README.md) · Quyết định schema: [`docs/adr/0001-kho-ca-the-v1.2.md`](docs/adr/0001-kho-ca-the-v1.2.md) · Kế hoạch + mốc giờ: [`docs/plan/phase-3.md`](docs/plan/phase-3.md)

### Thành viên 1 (sybui2004) — gộp gather P2 + lát B Lặn · Integrator/Release
- Gộp gather Phase 2 còn dở, gắn tag còn thiếu; giỏ cá thể, hao tươi, `spoiled`, LIFO cá thể. Spec: [`docs/spec/phase-3/gather.md`](docs/spec/phase-3/gather.md)
- Gắn tag `phase-3` trước 2:30.

### Thành viên 2 (lit1numyt) — lát C Quán + day · PO
- Kho cá thể, hao, giữ theo id, giữ lại một lần, giá theo tươi; bàn giao cùng tick, id xuyên Ngày. Spec: [`docs/spec/phase-3/quan-day.md`](docs/spec/phase-3/quan-day.md)
- Giữ `docs/clarify.md` (#28–31).

### Thành viên 3 (hgmdz1210) — lát A adapter + HUD + QA · QA lead
- Adapter kho v1.2 (đẩy trước phút 10), HUD độ tươi, smoke kho, bật v1.2, CHANGELOG, verification. Spec: [`docs/spec/phase-3/adapter-hud-qa.md`](docs/spec/phase-3/adapter-hud-qa.md)

## Nhiệm vụ Phase 4 (Ticket-04 — Phát hành v1.0.0, Test Contract v1.3)

Spec chung (DoD, AC-P4-01…19, bảng tác động): [`docs/spec/phase-4/README.md`](docs/spec/phase-4/README.md) · Kế hoạch + mốc giờ: [`docs/plan/phase-4.md`](docs/plan/phase-4.md) · Verification: [`docs/verification/phase-4.md`](docs/verification/phase-4.md)

### Thành viên 1 (sybui2004) — bench + contract 1.3 + Release · Integrator/Release
- `bench_cmd` (Chrome headless, `bench.json`). Spec: [`bench-soak.md`](docs/spec/phase-4/bench-soak.md) mục A
- Contract 1.3, README, CHANGELOG, LICENSE, CREDITS, release notes, tag `phase-4` + Release `v1.0.0` trước 3:00. Spec: [`release-docs.md`](docs/spec/phase-4/release-docs.md)

### Thành viên 2 (lit1numyt) — soak + retro · PO, điều phối retro
- `soak_cmd` 10 Ngày, bot tất định. Spec: [`bench-soak.md`](docs/spec/phase-4/bench-soak.md) mục B
- Clarify #35–39, `docs/retro.md`, nhắc đủ `docs/members/`.

### Thành viên 3 (hgmdz1210) — cảnh báo + tương phản cao + đóng gói · Bench/QA
- Ba cảnh báo, chế độ tương phản cao. Spec: [`alerts-ui.md`](docs/spec/phase-4/alerts-ui.md)
- Clone sạch ≤ 3 lệnh, zip, regression, `docs/verification/phase-4.md`.

### Sang Phan (sangdaden) — admin
- Kiểm quyền repo/Release, `docs/members/sangdaden.md`.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: nhóm chat chung để trao đổi, GitHub PR và [`docs/standup.md`](docs/standup.md) để lưu tiến độ và quyết định.
- Khi bất đồng về thiết kế: nói 2 phút, không xong thì Integrator (TV1) quyết và ghi lý do vào `docs/adr/`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng (cột cuối bảng) nhận việc.
- Giờ standup giữa phase: phút thứ 30 của mỗi phase, ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát kế bên (TV1 ↔ TV2 đọc `quan.py` của nhau, TV3 đọc gather) trước khi gộp.
- Cách làm việc với Git: nhánh ngắn `feature/<module>-<việc>`, chạy test xanh rồi gộp vào `main`; TV1 gắn tag.

## Đánh giá (100 điểm)

Cột **Điểm** ghi trọng số của đề. Kết quả chấm chính thức, gồm test ẩn, do giảng viên xác nhận.

| Hạng mục | Điểm | Kết quả và bằng chứng | Còn thiếu hoặc cần xác nhận |
|---|---:|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 | Bốn mốc chạy `phase-check` đều đạt 7/7. Bản phát hành đạt 209/209 unittest trên Windows. Lượt headless `day` seed 1 của v1.2 và v1.3 khớp từng byte. [Hồi quy cuối](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/verification/phase-4.md) | Chờ kết quả test ẩn. Tag `phase-1` gốc sử dụng contract v1.1 dù spec Phase 1 yêu cầu v1.0. [Spec Phase 1](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/spec/phase-1/README.md) |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 | Fork công khai, cả bốn tài khoản có quyền cộng tác, phân vai theo phase. Ba thành viên phụ trách module có ít nhất ba commit có nội dung mỗi người. Có hồ sơ đổi schema kho và nhật ký làm rõ yêu cầu. [Repo](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi) · [Quyết định về kho](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/adr/0001-kho-ca-the-v1.2.md) | Chưa có bằng chứng `sangdaden` đủ ba commit có nội dung. Cần chính chủ bổ sung dẫn chứng hoặc PO xác nhận ngoại lệ với giảng viên. Các tag bàn giao và Release được hoàn tất sau hạn lab. |
| Kiểm chứng & bằng chứng | 15 | Có ma trận và bằng chứng cho [Phase 1](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/verification/phase-1.md), [Phase 2](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/verification/phase-2.md), [Phase 3](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/verification/phase-3.md) và [Phase 4](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/verification/phase-4.md). Có log so byte, bàn giao kho, ảnh UI, benchmark, soak và kiểm tra clone/ZIP trên Ubuntu. | Smoke tích hợp Phase 2 chạy lại đạt, thời điểm phút 20 chưa được chứng minh. Một ca Chrome được bỏ qua trên Ubuntu vì thiếu trình duyệt và đã chạy đạt trên Windows. Clarify #42 vẫn chờ PO xác nhận môi trường máy chấm. |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 | Có hướng dẫn lệnh chạy theo phase, hai skill `phase-check` và `clarify-log`, nhật ký AI có ví dụ lỗi và cách xác minh. [AGENTS.md](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/AGENTS.md) · [Nhật ký AI](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/ai-usage-log.md) | AC-QA-04 tại tag Phase 1 thiếu mục dùng AI của TV1. Nhật ký hiện có mục của TV1 ở Phase 4. |
| Đánh giá & retro | 10 | Retro ghi việc đã làm sau Phase 2, số liệu commit, lỗi AI phát hiện qua test và hành động đề xuất có người phụ trách. Có bốn hồ sơ thành viên. [Retro](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/retro.md) · [Hồ sơ thành viên](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/tree/4df39b9/docs/members) | `sybui2004`, `hgmdz1210` và `sangdaden` còn ở dạng nháp, chờ chính chủ hoàn tất hoặc xác nhận. Retro ghi rõ Phase 2 chưa chốt hành động tại thời điểm đó. |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 | Có vòng Ngày, kho độ tươi, ba cảnh báo, tương phản cao và bản phát hành v1.0.0. Soak 10/10 ngày, 0 crash và tất định. Âm thanh, lời thoại và sổ tay sáng tạo nằm sau cờ giao diện. [Release](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/releases/tag/v1.0.0) · [Ý tưởng sáng tạo](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/creative-ideas.md) | Benchmark 59,97 FPS, dưới mốc tham khảo 60 FPS. Hiệu ứng nước/bọt/hơi bếp thuộc kế hoạch sáng tạo còn dở. Tài liệu chưa ghi nhận kiểm tra nghe/nhìn trực tiếp đối với các tính năng sáng tạo. |
| Demo | 5 | Chrome 1280×720 đã chạy từ Menu qua Lặn, Quán, Shop đến Tổng kết. Kịch bản rút ngắn có nấu và phục vụ một món bằng bàn phím, khách trả 70 xu gồm 11 xu boa. [Log demo](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/blob/4df39b9/docs/proof/phase-4/ui-smoke.txt) | Hồ sơ có demo tự động và ảnh. Chưa có bằng chứng nhóm đã trình bày demo trực tiếp cho giảng viên. |
| **Tổng** | **100** | | |
