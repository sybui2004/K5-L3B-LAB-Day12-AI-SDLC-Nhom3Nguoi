# Spec Phase 4 (Ticket-04 — Phát hành v1.0.0) — phần chung

> Nguồn: lab board tab **Phase 4 — Ticket-04** (30 phút, 2:30–3:00, Test Contract v1.3). Kế hoạch: [`docs/plan/phase-4.md`](../../plan/phase-4.md).
> Chỗ đề chưa rõ ghi **[clarify #n]** ở [`docs/clarify.md`](../../clarify.md). Nhóm 4 người ⇒ **không làm Mở rộng** (leaderboard, phụ đề SFX); `extensions` giữ `[]`.
> **Gameplay, tuning, kho, JSONL giữ nguyên v1.2.** Phase 4 chỉ thêm lệnh đo/soak, cảnh báo UI, đóng gói và tài liệu. Không sửa luật trong `chonoi/sim/*` trừ chỗ soak cần chạy > 5 Ngày (mục B của [bench-soak.md](bench-soak.md)).

## Spec theo lát

| Lát | Nội dung | Spec | Chủ |
|---|---|---|---|
| A | `bench_cmd`: Chrome headless + trang đo khung hình, `bench.json` | [bench-soak.md](bench-soak.md) mục A | TV1 (sybui2004) |
| B | `soak_cmd`: 10 Ngày một tiến trình, bot tất định, `soak.json` | [bench-soak.md](bench-soak.md) mục B | TV2 (Khoa) |
| C | Ba cảnh báo chữ/biểu tượng + chế độ tương phản cao | [alerts-ui.md](alerts-ui.md) | TV3 (Hưng) |
| D | Contract v1.3, README, CHANGELOG, LICENSE/CREDITS, gói phát hành, tag + Release | [release-docs.md](release-docs.md) mục A–C | TV1 (Release) + TV3 (đóng gói) |
| E | Retro, phản tư cá nhân, verification, clarify, nhật ký AI | [release-docs.md](release-docs.md) mục D | TV2 (điều phối retro) + mọi người |

## 1. DoD (Ticket-04)
1. `game.contract.json`: `contract_version:"1.3"`, khai `bench_cmd`, `soak_cmd` ở gốc. `bench_cmd` chạy cảnh chuẩn, tạo `bench.json` đúng 5 trường. `soak_cmd` chạy 10 Ngày, tạo `soak.json` đúng cấu trúc.
2. Clone sạch chạy bản có giao diện bằng **≤ 3 lệnh** trên macOS/Linux. Ba cảnh báo có chữ hoặc biểu tượng; chế độ tương phản cao hoạt động và đã thử cả ba cảnh báo ở chế độ đó.
3. Regression P1–P3 còn hiệu lực đạt. `docs/verification/phase-4.md` + `docs/proof/phase-4/` khớp commit gắn tag. `docs/clarify.md`, `docs/ai-usage-log.md` cập nhật.
4. `CHANGELOG.md` theo từng phase, release notes, bản đóng gói. Tag `phase-4` và GitHub Release `v1.0.0` cùng trỏ một commit trên `main`, **chậm nhất 3:00**.
5. `docs/retro.md` rà hành động P2, chốt việc tiếp theo, nêu một lỗi AI và cách xác minh. `docs/members/<handle>.md` đủ 4 người.

## 2. AC-P4

| AC | Nội dung | Chủ |
|---|---|---|
| AC-P4-01 | Manifest `contract_version:"1.3"`, `bench_cmd:"python -m chonoi.bench"`, `soak_cmd:"python -m chonoi.soak"` ở gốc; `tuning` không đổi so với v1.2; `extensions: []` | TV1 |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` thoát 0, file có đúng `avg_fps, p1_low_fps, frames, measured_s, load_ms` (số) | TV1 |
| AC-P4-03 | Công thức: `avg_fps = frames / measured_s`; `p1_low_fps = 1 / mean(k khung chậm nhất, giây)`, `k = max(1, ceil(0.01 × frames))`; có unit test trên dãy thời gian khung cố định | TV1 |
| AC-P4-04 | Cảnh đo: buổi sáng (gather) v1.2 có độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định; Út Sen đứng yên ở bến; cửa sổ 1280×720; làm nóng 3 s rồi đo `--duration` s | TV1 |
| AC-P4-05 | Không tìm thấy trình duyệt / quá hạn ⇒ thoát khác 0, thông báo rõ, không ghi `bench.json` dở | TV1 |
| AC-P4-06 | `soak_cmd --seed 7 --days 10 --out soak.json`: `days, days_completed, crashes, results[], duration_s`; mỗi `results[]` có `day, earned, reputation, score` lúc Shop đóng | TV2 |
| AC-P4-07 | Soak: một tiến trình, một `DaySim`; kế hoạch Ngày `d` dùng `day_plan[(d-1) % 5]`; tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày, id cá thể nối tiếp | TV2 |
| AC-P4-08 | Soak tất định: hai lần cùng seed ⇒ `soak.json` giống nhau khi bỏ `duration_s`; đạt khi `days_completed = days` và `crashes = 0` | TV2 |
| AC-P4-09 | `headless --mode day` vẫn chỉ nhận `--days` 1..5 (mã 2 ngoài khoảng); JSONL day không đổi so với v1.2 | TV2 |
| AC-P4-10 | Cảnh báo **thủy quái gần**: chữ + biểu tượng, không chỉ dựa vào màu | TV3 |
| AC-P4-11 | Cảnh báo **oxy sắp hết**: chữ + biểu tượng | TV3 |
| AC-P4-12 | Cảnh báo **khách sắp giận**: chữ + biểu tượng trên bàn của khách | TV3 |
| AC-P4-13 | Chế độ tương phản cao: bật bằng phím `C` hoặc `?contrast=high`; cả ba cảnh báo đọc được ở chế độ đó (ảnh chụp) | TV3 |
| AC-P4-14 | Clone sạch ⇒ chạy giao diện bằng ≤ 3 lệnh theo README trên Linux/macOS (log thật) | TV3 |
| AC-P4-15 | README ghi: yêu cầu môi trường, điều khiển, lệnh test, headless, bench, soak, giới hạn đã biết | TV1 + TV3 |
| AC-P4-16 | `CHANGELOG.md` có mục phase-1…phase-4; `LICENSE` có; `CREDITS.md` liệt kê asset/công cụ đã dùng | TV1 |
| AC-P4-17 | GitHub Release `v1.0.0` có release notes do nhóm viết (điểm mới, cách chạy, giới hạn) + file `chonoi-v1.0.0.zip`; tag `phase-4` và `v1.0.0` cùng commit trên `main` | TV1 |
| AC-P4-18 | Regression toàn bộ unittest đạt trên commit tag; artifact `bench.json`, `soak.json` từ commit tag trong `docs/proof/phase-4/` | TV3 |
| AC-P4-19 | `docs/retro.md` (rà hành động P2, tốt/sửa/tiếp theo, một lỗi AI + cách xác minh); `docs/members/<handle>.md` × 4 | TV2 + mọi người |

## 3. Bảng tác động

| Module | File | Test | Người |
|---|---|---|---|
| Contract | `game.contract.json`, `chonoi/contract.py` (chấp nhận 1.3, đọc `bench_cmd`/`soak_cmd` nếu kiểm) | đổi test contract version nếu có | TV1 |
| Bench | **mới** `chonoi/bench.py`; `chonoi/live.py` (route `/bench/*`, cờ cảnh bench); **mới** `chonoi/web/bench.js` (chỉ nạp khi `?bench=1`) | **mới** `tests/test_p4_bench.py` (công thức, đối số, lỗi không có trình duyệt) | TV1 |
| Soak | **mới** `chonoi/soak.py`, **mới** `chonoi/sim/bot.py`; `chonoi/sim/day.py` (bỏ giới hạn 5 Ngày ở tầng sim, giữ ở CLI) | **mới** `tests/test_p4_soak.py`; `tests/test_day.py` giữ nguyên | TV2 |
| UI | `chonoi/web/index.html` (cảnh báo, tương phản); `chonoi/live.py` chỉ nếu cần thêm trường snapshot | `tests/test_live.py` giữ; ảnh chụp | TV3 |
| Tài liệu / phát hành | `README.md`, `CHANGELOG.md`, `LICENSE` (mới), `CREDITS.md`, `AGENTS.md` (lệnh bench/soak), `TEAM.md` | — | TV1 + TV3 |
| QA / retro | `docs/verification/phase-4.md`, `docs/proof/phase-4/`, `docs/retro.md`, `docs/members/*.md`, `docs/clarify.md`, `docs/ai-usage-log.md` | toàn bộ regression | TV3 + TV2 + mọi người |

## 4. Phụ thuộc vào Phase 3
- v1.3 giữ gameplay **v1.2** ⇒ cần lát A–C Phase 3 trên `main` trước khi bật `"1.3"`. Lát A, B, C của Phase 4 viết được trên `main` hiện tại vì chỉ gọi `DaySim`/`LiveGame` qua giao diện có sẵn.
- Nếu tới phút 15 (2:45) Phase 3 chưa gộp đủ: vẫn bật `"1.3"` + khai lệnh, ghi trung thực trong verification và release notes mục "Giới hạn đã biết" phần v1.2 nào chưa đạt.
- `chonoi.live` hiện chỉ có `--mode gather|quan` (chưa có `day`, xem verification P2). Demo "một Ngày từ Lặn tới đóng Shop" cần UI day ⇒ xem [release-docs.md](release-docs.md) mục C, rủi ro trong plan.
