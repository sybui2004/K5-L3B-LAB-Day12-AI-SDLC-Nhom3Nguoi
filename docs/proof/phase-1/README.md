# Bằng chứng Phase 1

Tạo ngày 2026-11-21 trên nhánh `feature/ui-qa-phase-1`, khi luật gather và quan **chưa có trong repo**.

| File | Nội dung |
|---|---|
| `phase-check.txt` | Bảng kết quả của skill `phase-check`: 6/7 mục đạt |
| `unittest.txt` | Log `unittest -v`: 59 test, 21 test đỏ trong `tests/test_quan_rules.py` |
| `gather-seed1.jsonl.txt`, `quan-seed1.jsonl.txt` | JSONL headless seed 1, 600 tick |
| `cmp.txt` | So byte hai lần chạy cùng seed |
| `ui-gather-hud.png` | HUD gather với scenario dựng sẵn: oxy 0, cảnh báo ngạt, giỏ 3/12 |
| `ui-gather-end-toast.png` | Cập bến bằng phím E, toast `gather_end` |
| `ui-quan-hud.png` | HUD quan với scenario dựng sẵn: bếp đang nấu, khách chờ, tay cầm món |

Tạo lại log: `python .agents/skills/phase-check/phase_check.py --proof docs/proof/phase-1`.

Các ảnh chụp từ code trong repo bằng Chrome headless. Vì chưa có luật nên số liệu trong ảnh quan là trạng thái dựng sẵn, không phải một ca chơi thật.
