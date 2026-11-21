# Phase 4 — Lát D (contract, đóng gói, phát hành) và lát E (retro, phản tư, verification)

> Phần chung: [README.md](README.md).

## A. Contract v1.3 (TV1)
```json
{
  "contract_version": "1.3",
  "run_cmd": "python -m chonoi.live --mode gather",
  "headless_cmd": "python -m chonoi.headless",
  "bench_cmd": "python -m chonoi.bench",
  "soak_cmd": "python -m chonoi.soak",
  "extensions": []
}
```
- Chỉ đổi 3 khóa trên; `tuning` giữ nguyên v1.2 (so `git diff` phải chỉ thấy các dòng này). `chonoi/contract.py` chấp nhận `"1.3"`; mọi chỗ rẽ nhánh theo phiên bản (vd kho cá thể từ 1.2) dùng so sánh `>= (1, 2)`, không so chuỗi bằng.
- Bật `"1.3"` **sau** khi lát A, B đã gộp và chạy được (mốc phút 15). Chạy toàn bộ unittest ngay sau khi bật.
- Nếu `run_cmd` đổi sang `--mode day` (khi live có day) thì cập nhật cùng lúc README.

## B. Đóng gói + clone sạch (TV3)
### B1. Ba lệnh từ clone sạch (Linux/macOS, Python ≥ 3.10, không cần pip)
```bash
git clone https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi
python3 -m chonoi.live --mode gather     # mở địa chỉ in ra
```
- Thử thật trên Linux hoặc macOS (máy thành viên, WSL Ubuntu, hoặc GitHub Codespaces). Lưu log vào `docs/proof/phase-4/clean-clone.txt`: OS, `python3 --version`, 3 lệnh, dòng địa chỉ in ra, ảnh màn hình đầu.
- Không có máy Linux/macOS ⇒ dùng WSL; ghi rõ môi trường đã thử. [clarify #35]

### B2. Bản đóng gói
- `git archive --format=zip --prefix=chonoi-v1.0.0/ -o chonoi-v1.0.0.zip <commit-tag>` (chỉ file trong git, không kèm `handoff/`, worktree, file tạm).
- Thử giải nén ở thư mục mới rồi chạy `python3 -m chonoi.live --mode gather` và `PYTHONPATH=tests:. python3 -m unittest discover -s tests` — ghi vào `clean-clone.txt`.

### B3. README.md (TV1 + TV3)
Thêm/sửa các mục (giữ nội dung lab gốc phía trên, thêm phần của nhóm):
- **Yêu cầu:** Python ≥ 3.10, thư viện chuẩn; trình duyệt hiện đại; bench cần Chrome/Chromium/Edge (hoặc `CHONOI_BROWSER`).
- **Chạy nhanh (≤ 3 lệnh)** — B1.
- **Điều khiển:** WASD bơi, `E` tương tác, `Space` bắt cá / hành động, `R` chơi lại, `C` tương phản cao (đối chiếu đúng phím trong `index.html` trước khi ghi).
- **Lệnh test, headless (gather/quan/day), bench, soak** — đúng lệnh trong `AGENTS.md`.
- **Sáng tạo của nhóm** (đã có) + bằng chứng lõi vẫn đúng: headless tắt `creative`, link test.
- **Giới hạn đã biết** (trung thực: phần v1.2 chưa đạt nếu có, UI day nếu chưa có, FPS phụ thuộc máy).
- Cập nhật `AGENTS.md` mục Lệnh: thêm bench, soak.

### B4. CHANGELOG, LICENSE, CREDITS (TV1)
- `CHANGELOG.md` viết lại theo phase (dựa `git log` từng tag):
  - `## [v1.0.0 / phase-4]` bench, soak, cảnh báo + tương phản cao, contract 1.3.
  - `## [phase-3]` breaking v1.2 (bản nháp ở spec phase-3 README mục 5).
  - `## [phase-2]` v1.1: 6 nguyên liệu, cá bơi/sinh, Cá Sấu, Máu/ngất, 2 bếp/4 bàn/6 món, day/Shop, pause.
  - `## [phase-1]` PRD-0: gather + quan, headless, live.
- `LICENSE`: đề xuất MIT cho code nhóm; giữ ghi chú khung starter thuộc giảng viên. **Chờ PO hỏi giảng viên giấy phép của starter** [clarify #36]. Nếu chưa có trả lời trước 2:55 ⇒ MIT kèm câu "Khung starter © giảng viên khóa học, dùng theo điều kiện của lab".
- `CREDITS.md`: không có asset ngoài (vẽ bằng canvas, âm thanh Web Audio tự sinh — kiểm lại `creative.js`); liệt kê công cụ AI (Claude Code/Opus 5.5, DeepSeek, Gemini/agy — theo `docs/ai-usage-log.md`); nhân vật Bến Tre là hư cấu của nhóm.

## C. Tag + Release (TV1, Release/Integrator)
1. Kiểm commit bàn giao trên `main`: unittest xanh, `phase-check` xanh, `bench.json`/`soak.json` trong proof sinh từ đúng commit này (ghi sha trong `docs/verification/phase-4.md`).
   - Proof phải nằm trong commit được tag ⇒ thứ tự: chạy bench/soak trên commit ứng viên X → commit proof (X+1, chỉ thêm `docs/`) → tag X+1. Ghi rõ "artifact sinh từ X, X+1 chỉ thêm tài liệu".
2. `git tag -a phase-4 -m "Phase 4 — v1.0.0"`, `git tag -a v1.0.0` cùng commit; `git push origin phase-4 v1.0.0`.
3. `gh release create v1.0.0 chonoi-v1.0.0.zip --title "Quán Ăn Chợ Nổi v1.0.0" --notes-file docs/release-notes-v1.0.0.md --verify-tag`.
4. `docs/release-notes-v1.0.0.md` (nhóm viết, tiếng Việt): Điểm mới (theo phase), Cách chạy (3 lệnh + test + headless + bench + soak), Giới hạn đã biết, Thành viên.
5. Hạn chót **3:00**. Phút 25 nếu còn đỏ: tag trạng thái tốt nhất, ghi trung thực phần chưa đạt.
- Demo "Chơi một Ngày Lặn → Quán → đóng Shop": nếu `chonoi.live` chưa có `--mode day` thì demo bằng `live --mode gather --inventory-out kho.json` → `live --mode quan --inventory kho.json`, còn Shop minh họa bằng `headless --mode day` + JSONL. Ghi vào "Giới hạn đã biết".

## D. Retro, phản tư, verification (TV2 điều phối + mọi người)
### D1. `docs/retro.md`
- Mở đầu: **rà hành động đã chốt ở retro P2** (mục "1 hành động cho Phase 3" hiện còn trống ⇒ ghi trung thực "P2 chưa chốt hành động; hành động thực tế đã làm là …", dựa `docs/standup.md`, PR #8–#14).
- Điều làm tốt / cần sửa / hành động tiếp theo (mỗi mục ≥ 2 ý, có dẫn chứng commit/PR).
- Số liệu: commit theo người (`git shortlog -sn --all`), cách đọc code của nhau, token theo người (lấy từ ai-usage-log, ghi "không đo" nếu không có).
- **Một lỗi AI + cách xác minh** (ví dụ thật đã có: AI viết sai kỳ vọng test pause, phát hiện khi test đỏ và đọc lại ticket 4.2 — `docs/ai-usage-log.md`).

### D2. `docs/members/<handle>.md` (≤ 200 từ, theo `TEMPLATE.md`)
Bốn file: `sybui2004.md`, `lit1numyt.md`, `hgmdz1210.md`, `sangdaden.md`. Mỗi người tự viết bằng tài khoản mình; dẫn link commit/PR/proof. Sang Phan (admin) ghi phần đã làm (quản trị repo, collaborator…) và đánh giá chéo.

### D3. `docs/verification/phase-4.md` (TV3)
Bảng AC-P4-01…19 → cách kiểm → bằng chứng → kết quả trên commit tag (khung đã tạo sẵn). Thêm dòng regression P1–P3 (`unittest.txt`).

### D4. `docs/clarify.md`, `docs/ai-usage-log.md`
Mỗi người thêm dòng Phase 4 của mình vào ai-usage-log; PO chốt #32–#36.
