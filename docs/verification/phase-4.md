# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3)

> Commit bàn giao (tag `phase-4` = `v1.0.0`): `<điền sha>` · Artifact bench/soak sinh từ: `<sha code>` · AC: [`docs/spec/phase-4/README.md`](../spec/phase-4/README.md) mục 2 · Kết quả ghi **trung thực** trên đúng commit tag.

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-4/...`) | Kết quả |
|---|---|---|---|
| AC-P4-01 manifest 1.3, `bench_cmd`, `soak_cmd` | `git diff phase-3 -- game.contract.json`; unittest contract | `contract-diff.txt` | |
| AC-P4-02 `bench.json` 5 trường | `python -m chonoi.bench --seed 42 --duration 30 --out bench.json` | `bench.json`, `bench-run.txt` | |
| AC-P4-03 công thức avg / 1% low | `tests/test_p4_bench.py` | `unittest.txt` | |
| AC-P4-04 cảnh đo chuẩn 1280×720, warmup 3 s | đọc `bench-run.txt` + ảnh khung bench | `bench-run.txt` | |
| AC-P4-05 không có trình duyệt ⇒ mã ≠ 0 | `CHONOI_BROWSER=/nope python -m chonoi.bench …` | `bench-run.txt` | |
| AC-P4-06 `soak.json` cấu trúc | `python -m chonoi.soak --seed 7 --days 10 --out soak.json` | `soak.json` | |
| AC-P4-07 kế hoạch lặp D1–D5, giá trị nối tiếp | `tests/test_p4_soak.py` | `unittest.txt` | |
| AC-P4-08 tất định, 10/10, 0 crash | chạy 2 lần, so bỏ `duration_s` | `soak-diff.txt` | |
| AC-P4-09 headless day vẫn 1..5 | `tests/test_day.py`, `test_p4_soak.py` | `unittest.txt` | |
| AC-P4-10 cảnh báo thủy quái gần | chơi thử | `alert-monster.png`, `alert-monster-hc.png` | |
| AC-P4-11 cảnh báo oxy | chơi thử | `alert-oxygen.png`, `alert-oxygen-hc.png` | |
| AC-P4-12 cảnh báo khách sắp giận | chơi thử | `alert-customer.png`, `alert-customer-hc.png` | |
| AC-P4-13 tương phản cao (`C`, `?contrast=high`) | chơi thử ba cảnh báo ở chế độ cao | 3 ảnh `*-hc.png`, `alerts.md` | |
| AC-P4-14 clone sạch ≤ 3 lệnh (Linux/macOS) | làm theo README | `clean-clone.txt` | |
| AC-P4-15 README đủ mục | đọc README | link mục README | |
| AC-P4-16 CHANGELOG theo phase, LICENSE, CREDITS | đọc file | — | |
| AC-P4-17 Release v1.0.0 + zip + notes, cùng commit tag | `gh release view v1.0.0`; `git rev-list -n1 phase-4 v1.0.0` | `release.txt` | |
| AC-P4-18 regression P1–P3 | `PYTHONPATH=tests:. python -m unittest discover -s tests -v` | `unittest.txt`, `phase-check.txt` | |
| AC-P4-19 retro + members × 4 | đọc `docs/retro.md`, `docs/members/` | — | |

## Benchmark (báo cáo, không chấm ngưỡng)

| Chỉ số | Giá trị | Mốc | Đạt? |
|---|---|---|---|
| avg_fps | | ≥ 60 | |
| p1_low_fps | | ≥ 30 | |
| load_ms | | ≤ 10 000 | |

Máy / OS / trình duyệt: …
