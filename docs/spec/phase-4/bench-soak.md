# Phase 4 — Lát A (bench) và lát B (soak)

> Phần chung: [README.md](README.md). Chỉ dùng thư viện chuẩn Python (giữ `requirements.txt` rỗng); trình duyệt là phần mềm hệ thống, không phải gói pip.

## A. `bench_cmd` — `python -m chonoi.bench` (TV1)

### A1. Giao diện lệnh
```
python -m chonoi.bench --seed 42 --duration 30 --out bench.json [--warmup 3] [--browser PATH] [--timeout 120]
```
- Bắt buộc: `--seed <int>`, `--duration <giây, >0>`, `--out <path>`. Sai/thiếu ⇒ mã 2 (giống headless).
- `--browser` mặc định: biến môi trường `CHONOI_BROWSER`, rồi tìm lần lượt `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser`, `microsoft-edge` trong `PATH`, rồi đường dẫn chuẩn macOS (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`) và Windows (`Program Files\Google\Chrome\Application\chrome.exe`, `msedge.exe`).
- Không thấy trình duyệt ⇒ in hướng dẫn cài/đặt `CHONOI_BROWSER`, mã 3. Quá `--timeout` ⇒ dừng trình duyệt, mã 4. Hai trường hợp **không ghi** `--out`.

### A2. Luồng chạy
1. `t0 = time.perf_counter()` ngay đầu `main()`.
2. Dựng `LiveGame(mode="gather", seed, scenario=None)` + `LiveServer(port=0)` (dùng lại `chonoi/live.py`, không viết sim riêng). Cảnh: tuning mặc định của contract (độ tươi, cá bơi, Cá Sấu Năm Chèo theo v1.2), Út Sen ở `start_pos` = bến, **không gửi input** ⇒ đứng yên. Nếu mặc định chưa đúng cảnh mới thêm scenario riêng cho bench.
3. Mở trình duyệt:
   `<browser> --headless=new --window-size=1280,720 --user-data-dir=<tmpdir> --no-first-run --no-default-browser-check --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows "<url>/?bench=1&warmup=3&duration=30"`
4. Trang (`?bench=1`, code trong `chonoi/web/bench.js`, chỉ nạp khi có cờ — không ảnh hưởng chơi thường):
   - Vòng `requestAnimationFrame` có sẵn vẫn vẽ như chơi thường (cùng hàm vẽ, cùng `fetch('/state')`).
   - Khung đầu tiên **đã vẽ một snapshot** ⇒ `POST /bench/first-frame`. Server ghi `load_ms = (perf_counter() lúc nhận − t0) × 1000`.
   - Làm nóng `warmup` s kể từ khung đầu. Sau đó ghi `dt` giữa hai callback rAF liên tiếp (ms, `performance.now()`) tới khi tổng `dt ≥ duration × 1000`.
   - `POST /bench/result {"frame_ms":[…]}`.
5. Server tính số liệu (A3), ghi `--out` (file tạm rồi `os.replace`), tắt trình duyệt + server, xóa `tmpdir`, thoát 0.
6. Route `/bench/*` chỉ bật khi `LiveGame` được dựng bởi `chonoi.bench` (cờ `bench=True`); chơi thường trả 404.

### A3. Công thức (hàm thuần `bench_stats(frame_ms) -> dict`, có unit test)
| Trường | Cách tính |
|---|---|
| `frames` | `len(frame_ms)` |
| `measured_s` | `sum(frame_ms) / 1000` (thời gian thực của khoảng đo) |
| `avg_fps` | `frames / measured_s` |
| `p1_low_fps` | `k = max(1, ceil(0.01 × frames))`; lấy `k` giá trị lớn nhất của `frame_ms`; `1 / (mean / 1000)` |
| `load_ms` | từ A2 bước 4 |
- Làm tròn khi ghi: `avg_fps`, `p1_low_fps`, `measured_s` 2 chữ số; `frames`, `load_ms` số nguyên. Thứ tự khóa như đề: `avg_fps, p1_low_fps, frames, measured_s, load_ms`.
- Test bắt buộc: `[16.0]*100 + [50.0]` ⇒ `frames=101`, `k=2`, `p1_low = 1/((50+16)/2/1000)`; `frames=1` ⇒ `k=1`; dãy rỗng ⇒ lỗi.
- Test tích hợp (bỏ qua nếu không có trình duyệt: `skipUnless(find_browser())`): `--duration 2` ⇒ file đủ 5 khóa, `frames > 0`.

### A4. Bằng chứng
- `docs/proof/phase-4/bench.json` chạy trên commit tag + `bench-run.txt` (lệnh, OS, trình duyệt + phiên bản).
- Mốc báo cáo (không chấm đạt/trượt): avg ≥ 60, 1% low ≥ 30, load ≤ 10 000 ms — ghi đạt/không vào verification.
- Chrome headless có thể khóa rAF theo 60 Hz ⇒ `avg_fps` ≈ 60 là bình thường. [clarify #33]

## B. `soak_cmd` — `python -m chonoi.soak` (TV2)

### B1. Giao diện lệnh
```
python -m chonoi.soak --seed 7 --days 10 --out soak.json
```
- `--seed <int>`, `--days <int ≥ 1>`, `--out <path>` bắt buộc; sai ⇒ mã 2. Không ghi JSONL, không ghi bảng xếp hạng, không mở cổng mạng.

### B2. Chạy
- Một tiến trình, một `Streams(seed)`, một `IdAllocator`, **một** `DaySim(tuning, scenario=None, streams, ids, days=N)`.
- `chonoi/sim/day.py`: giữ `validate_days` (1..5) cho CLI headless, nhưng `DaySim` không tự chặn N > 5. Ngày `d` dùng `day_plan[(d - 1) % len(day_plan)]`. Tiền, tổng thu, uy tín, cấp nâng cấp, `days_completed`, id cá thể **không reset** giữa các Ngày (đã theo hợp đồng P2/P3 — chỉ cần kiểm).
- Vòng: `while sim.reason is None: events = sim.step(bot.next(sim.snapshot()))`; gặp `shop_end` ⇒ thêm `{"day": d, "earned": sim.earned, "reputation": round(sim.reputation, 3), "score": <như runner._common>}` vào `results`. Dùng **giá trị lũy kế** của lượt (giống snapshot). [clarify #34]
- Bọc vòng bằng `try/except Exception`: lỗi ⇒ `crashes = 1`, dừng, vẫn ghi `soak.json` với `days_completed` tới lúc đó, in traceback ra stderr, thoát 1. Không lỗi ⇒ thoát 0.
- `duration_s` = thời gian thực toàn lượt (làm tròn 3) — trường duy nhất được phép khác giữa hai lần chạy.
- Giới hạn tick an toàn: `days × (gather + quan + shop.max_ticks + 10)` tick; vượt ⇒ coi là crash (ghi lý do `stuck` ra stderr).

### B3. Bot tất định (`chonoi/sim/bot.py`)
- Chỉ đọc snapshot, không dùng RNG, không đọc đồng hồ ⇒ tất định theo seed.
- **Mức tối thiểu (bắt buộc):** gather: không input (đứng ở bến, hết giờ thì sang quán với giỏ rỗng); quán: không input; Shop: nhấn `shop_done` ngay. Đủ để `days_completed = 10`, `crashes = 0`.
- **Mức nâng (chỉ khi mức tối thiểu đã gộp và còn giờ):** gather bơi tới nút `ready` gần nhất, `interact`, về bến khi giỏ đầy hoặc còn ≤ 20 s; quán nấu món đủ nguyên liệu cho khách `order_tick` nhỏ nhất rồi phục vụ. Chạy lại B4 trước khi gộp.

### B4. Test `tests/test_p4_soak.py`
- `--days 10 --seed 7` ⇒ `days_completed == 10`, `crashes == 0`, `len(results) == 10`, `results[i]["day"] == i + 1`.
- Chạy hai lần ⇒ bằng nhau sau khi bỏ `duration_s`.
- Ngày 6 dùng kế hoạch Ngày 1 (so menu/`plan_ingredients` trong event `phase_start` hoặc snapshot).
- `earned` không giảm qua các Ngày; `--days 0` ⇒ mã 2.
- `headless --mode day --days 6` vẫn mã 2 (giữ AC-P2).
- Nếu ca 10 Ngày chạy > 20 s: đặt `skipUnless(os.environ.get("CHONOI_SLOW"))`, giữ ca 2 Ngày luôn chạy; ghi lệnh chạy đủ trong verification.

### B5. Bằng chứng
`docs/proof/phase-4/soak.json` (seed 7, 10 Ngày) + `soak-diff.txt` (hai lần chạy, so bỏ `duration_s`).
