# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3)

> Kiểm chứng trên mã nguồn tích hợp `f498edd`. Các commit sau bổ sung hồ sơ bàn giao và giữ nguyên mã nguồn chạy. Bản bàn giao được hoàn tất sau mốc giờ của lab. [Tiêu chí Phase 4](../spec/phase-4/README.md)

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-4/...`) | Kết quả |
|---|---|---|---|
| AC-P4-01 manifest 1.3, `bench_cmd`, `soak_cmd` | So với mã nguồn v1.2 `6ba4d26` | [contract-diff.txt](../proof/phase-4/contract-diff.txt) | Đạt, tuning giữ nguyên |
| AC-P4-02 `bench.json` 5 trường | Bench chuẩn 30 giây | [bench.json](../proof/phase-4/bench.json) | Đạt |
| AC-P4-03 công thức avg / 1% low | `tests/test_p4_bench.py` | `unittest.txt` | Đạt |
| AC-P4-04 cảnh đo chuẩn 1280×720, warmup 3 s | Kiểm tham số Chrome và lệnh chạy | [bench-run.txt](../proof/phase-4/bench-run.txt) | Đạt |
| AC-P4-05 không có trình duyệt ⇒ mã ≠ 0 | Test các trường hợp thiếu Chrome | `unittest.txt` | Mã 3 và không tạo file |
| AC-P4-06 `soak.json` cấu trúc | Soak seed 7, 10 Ngày | [soak.json](../proof/phase-4/soak.json) | Đạt |
| AC-P4-07 kế hoạch lặp D1–D5, giá trị nối tiếp | `tests/test_p4_soak.py` | `unittest.txt` | Đạt |
| AC-P4-08 tất định, 10/10, 0 crash | So hai lượt sau khi bỏ `duration_s` | [soak-diff.txt](../proof/phase-4/soak-diff.txt) | Đạt |
| AC-P4-09 headless day vẫn 1..5 | `tests/test_day.py`, `tests/test_p4_soak.py`, so JSONL v1.2/v1.3 | [day-regression.txt](../proof/phase-4/day-regression.txt) | Đạt, đầu ra seed 1 giống từng byte |
| AC-P4-10 cảnh báo thủy quái gần | Chrome headless 1280×720 | [thường](../proof/phase-4/alert-monster.png), [cao](../proof/phase-4/alert-monster-hc.png) | Đạt |
| AC-P4-11 cảnh báo oxy | Chrome headless 1280×720 | [thường](../proof/phase-4/alert-oxygen.png), [cao](../proof/phase-4/alert-oxygen-hc.png) | Đạt |
| AC-P4-12 cảnh báo khách sắp giận | Chrome headless 1280×720 | [thường](../proof/phase-4/alert-customer.png), [cao](../proof/phase-4/alert-customer-hc.png) | Đạt |
| AC-P4-13 tương phản cao (`C`, `?contrast=high`) | chơi thử ba cảnh báo ở chế độ cao | [alerts.md](../proof/phase-4/alerts.md) và 3 ảnh `*-hc.png` | Đạt, lựa chọn còn sau tải lại |
| AC-P4-14 clone sạch ≤ 3 lệnh (Linux/macOS) | Ubuntu WSL, mở live từ clone và ZIP | [clean-clone.txt](../proof/phase-4/clean-clone.txt) | Đạt khởi chạy. Bộ test từ ZIP chạy với `venv --without-pip`, 208 test đạt, bỏ qua một ca Chrome vì Ubuntu này thiếu trình duyệt. Clarify #42 chờ PO xác nhận môi trường chấm |
| AC-P4-15 README đủ mục | Đối chiếu lệnh và phím điều khiển | [README](../../README.md) | Đạt |
| AC-P4-16 CHANGELOG theo phase, LICENSE, CREDITS | Kiểm nội dung ba file | [CHANGELOG](../../CHANGELOG.md), [LICENSE](../../LICENSE), [CREDITS](../../CREDITS.md) | Áp dụng giả định giấy phép trong clarify #39 |
| AC-P4-17 Release v1.0.0 + zip + notes, cùng commit tag | Đối chiếu commit hai tag và commit trong ZIP | [Release notes](../release-notes-v1.0.0.md), [GitHub Release](https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi/releases/tag/v1.0.0) | Phát hành muộn. Tag và ZIP được đối chiếu khi phát hành |
| AC-P4-18 regression P1–P3 | `phase-check` trên Windows với Chrome thật | [unittest.txt](../proof/phase-4/unittest.txt), [phase-check.txt](../proof/phase-4/phase-check.txt) | 209 test, 7/7 mục đạt |
| AC-P4-19 retro + members × 4 | Đọc `docs/retro.md`, `docs/members/` | [Retro](../retro.md), [hồ sơ thành viên](../members/) | Một phản tư cá nhân đã có. Ba bản nháp chờ chính chủ xác nhận hoặc thay bằng bản tự viết |

## Benchmark (báo cáo, không chấm ngưỡng)

| Chỉ số | Giá trị | Mốc | Đạt? |
|---|---|---|---|
| avg_fps | 59,97 | ≥ 60 | Dưới mốc báo cáo |
| p1_low_fps | 45,14 | ≥ 30 | Đạt |
| load_ms | 839 | ≤ 10 000 | Đạt |

Windows x64, Python 3.13.18, Chrome 158.0.8127.37.

## Demo

Chrome 1280×720 xác nhận đi từ Menu qua Lặn, Quán, Shop đến Tổng kết. Kịch bản ngắn dựng sẵn một cá lóc. Sau khi cập bến, người chơi dùng bàn phím để nấu, mang món và phục vụ cá lóc nướng trui. Khách trả 70 xu, gồm 11 xu boa. [Log](../proof/phase-4/ui-smoke.txt) · [Menu](../proof/phase-4/demo/day-menu.png) · [Phục vụ](../proof/phase-4/demo/day-served.png) · [Shop](../proof/phase-4/demo/day-shop.png)
