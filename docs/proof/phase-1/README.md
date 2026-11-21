# Bằng chứng Phase 1

Tạo ngày 2026-11-21 trên nhánh `feature/ui-qa-phase-1`, sau khi gộp `origin/main` (`949028a`, contract v1.1). Tất cả chạy trên luật thật trong repo.

| File | Nội dung |
|---|---|
| `phase-check.txt` | Bảng kết quả của skill `phase-check`: 7/7 mục đạt |
| `unittest.txt` | Log `unittest -v`: 117 test xanh, không có test bị bỏ qua |
| `gather-seed1.jsonl.txt`, `quan-seed1.jsonl.txt` | JSONL headless seed 1, 600 tick |
| `cmp.txt` | So byte hai lần chạy cùng seed |
| `ui-gather-hud.png` | Chơi gather: đã hái điên điển, lặn bắt cá linh, giỏ 4/12 |
| `ui-gather-choke.png` | Hết oxy dưới nước: cảnh báo ngạt, mất Máu (scenario đặt sẵn oxy thấp) |
| `ui-gather-end-toast.png` | Về bến bằng phím E, toast kết thúc buổi sáng |
| `ui-quan-inventory-flow.png` | Quán nạp kho từ lượt gather vừa chơi, khách đến theo lịch |
| `ui-quan-hud.png` | Bếp đang nấu món của khách, có thanh tiến độ |
| `ui-quan-paid.png` | Khách ăn xong trả 144k gồm 24k boa, uy tín 3.2 |

Tạo lại log: `python .agents/skills/phase-check/phase_check.py --proof docs/proof/phase-1`.

Ảnh được chụp từ Chrome headless, thao tác bằng sự kiện phím thật qua giao diện.
