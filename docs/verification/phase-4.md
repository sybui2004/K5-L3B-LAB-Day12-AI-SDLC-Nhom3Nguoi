# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3)

> Bench, soak và hồi quy chạy với mã nguồn ứng viên `2e07328` trên nhánh `feature/sybui-phase-closeout`. Commit kế tiếp chỉ bổ sung bằng chứng. Các tag phát hành chờ review và tích hợp vào `main`. [Tiêu chí Phase 4](../spec/phase-4/README.md)

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-4/...`) | Kết quả |
|---|---|---|---|
| AC-P4-01 manifest 1.3, `bench_cmd`, `soak_cmd` | So với ứng viên v1.2 `0701271` | [contract-diff.txt](../proof/phase-4/contract-diff.txt) | Đạt, tuning giữ nguyên |
| AC-P4-02 `bench.json` 5 trường | Bench chuẩn 30 giây | [bench.json](../proof/phase-4/bench.json) | Đạt |
| AC-P4-03 công thức avg / 1% low | `tests/test_p4_bench.py` | `unittest.txt` | Đạt |
| AC-P4-04 cảnh đo chuẩn 1280×720, warmup 3 s | Kiểm tham số Chrome và lệnh chạy | [bench-run.txt](../proof/phase-4/bench-run.txt) | Đạt |
| AC-P4-05 không có trình duyệt ⇒ mã ≠ 0 | Test các trường hợp thiếu Chrome | `unittest.txt` | Mã 3 và không tạo file |
| AC-P4-06 `soak.json` cấu trúc | Soak seed 7, 10 Ngày | [soak.json](../proof/phase-4/soak.json) | Đạt |
| AC-P4-07 kế hoạch lặp D1–D5, giá trị nối tiếp | `tests/test_soak.py` | `unittest.txt` | Đạt |
| AC-P4-08 tất định, 10/10, 0 crash | So hai lượt sau khi bỏ `duration_s` | [soak-diff.txt](../proof/phase-4/soak-diff.txt) | Đạt |
| AC-P4-09 headless day vẫn 1..5 | `tests/test_day.py`, `tests/test_soak.py` | `unittest.txt` | Đạt |
| AC-P4-10 cảnh báo thủy quái gần | chơi thử | [thường](../proof/phase-4/alert-monster.png), [cao](../proof/phase-4/alert-monster-hc.png) | Đạt trên nhánh `feature/p4-alerts-contrast` bằng Chrome headless; chạy lại trên commit tag |
| AC-P4-11 cảnh báo oxy | chơi thử | [thường](../proof/phase-4/alert-oxygen.png), [cao](../proof/phase-4/alert-oxygen-hc.png) | Đạt trên nhánh `feature/p4-alerts-contrast` bằng Chrome headless; chạy lại trên commit tag |
| AC-P4-12 cảnh báo khách sắp giận | chơi thử | [thường](../proof/phase-4/alert-customer.png), [cao](../proof/phase-4/alert-customer-hc.png) | Đạt trên nhánh `feature/p4-alerts-contrast` bằng Chrome headless; chạy lại trên commit tag |
| AC-P4-13 tương phản cao (`C`, `?contrast=high`) | chơi thử ba cảnh báo ở chế độ cao | [alerts.md](../proof/phase-4/alerts.md) và 3 ảnh `*-hc.png` | Đạt trên nhánh `feature/p4-alerts-contrast` bằng Chrome headless; chạy lại trên commit tag |
| AC-P4-14 clone sạch ≤ 3 lệnh (Linux/macOS) | làm theo README | [clean-clone.txt](../proof/phase-4/clean-clone.txt) | Chưa chốt: bản thử trên Ubuntu WSL mở được giao diện bằng 3 lệnh; còn chạy lại trên commit tag và xử lý clarify #42 |
| AC-P4-15 README đủ mục | Đối chiếu lệnh và phím điều khiển | [README](../../README.md) | Đạt |
| AC-P4-16 CHANGELOG theo phase, LICENSE, CREDITS | Kiểm nội dung ba file | [CHANGELOG](../../CHANGELOG.md), [LICENSE](../../LICENSE), [CREDITS](../../CREDITS.md) | Áp dụng giả định giấy phép trong clarify #39 |
| AC-P4-17 Release v1.0.0 + zip + notes, cùng commit tag | Kiểm release sau khi có tag | [Release notes](../release-notes-v1.0.0.md) | Chờ review và phát hành |
| AC-P4-18 regression P1–P3 | `phase-check` | [unittest.txt](../proof/phase-4/unittest.txt), [phase-check.txt](../proof/phase-4/phase-check.txt) | 205 test, 7/7 mục đạt |
| AC-P4-19 retro + members × 4 | Đọc `docs/retro.md`, `docs/members/` | [Bản nháp TV1](../members/sybui2004.md) | Chờ phản tư cá nhân và phần bàn giao của nhóm |

## Benchmark (báo cáo, không chấm ngưỡng)

| Chỉ số | Giá trị | Mốc | Đạt? |
|---|---|---|---|
| avg_fps | 60,00 | ≥ 60 | Đạt |
| p1_low_fps | 51,02 | ≥ 30 | Đạt |
| load_ms | 886 | ≤ 10 000 | Đạt |

Windows x64, Python 3.13.18, Chrome 158.0.8127.37.
