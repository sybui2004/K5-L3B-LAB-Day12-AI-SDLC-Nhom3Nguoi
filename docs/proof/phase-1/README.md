# Bằng chứng Phase 1

Tạo ngày 2026-11-21 trên nhánh `feature/ui-qa-phase-1`, sau khi gộp `origin/main` (`0302397`). Đã có luật khách (lát 3); luật gather và quan lát 4 **chưa có trong repo**.

| File | Nội dung |
|---|---|
| `phase-check.txt` | Bảng kết quả của skill `phase-check`: 6/7 mục đạt |
| `unittest.txt` | Log `unittest -v`: 76 test, 8 test đỏ, đều là test lát 4 trong `tests/test_quan_rules.py` |
| `gather-seed1.jsonl.txt`, `quan-seed1.jsonl.txt` | JSONL headless seed 1, 600 tick |
| `cmp.txt` | So byte hai lần chạy cùng seed |
| `ui-gather-hud.png` | HUD gather với scenario dựng sẵn: oxy 0, cảnh báo ngạt, giỏ 3/12 |
| `ui-gather-end-toast.png` | Cập bến bằng phím E, toast `gather_end` |
| `ui-quan-hud.png` | HUD quan với scenario dựng sẵn: bếp đang nấu, khách chờ, tay cầm món |
| `ui-quan-inventory-flow.png` | Quan nạp kho từ lượt gather vừa cập bến, khách thật đến theo lịch |

Tạo lại log: `python .agents/skills/phase-check/phase_check.py --proof docs/proof/phase-1`.

Các ảnh chụp từ code trong repo bằng Chrome headless. Giỏ của lượt gather được dựng sẵn vì chưa có luật hái và bắt cá. Trạng thái bếp trong `ui-quan-hud.png` cũng dựng sẵn vì chưa có lát 4.
