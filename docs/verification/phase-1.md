# Ma trận truy vết Phase 1

> Trạng thái ngày 2026-11-21 trên nhánh `feature/ui-qa-phase-1`, đã gộp `origin/main` (`949028a`, contract v1.1). Kết quả dưới đây chạy trên luật thật trong repo.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-G-01 | `Oxygen.test_dive_and_surface_events` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-02 | `Oxygen.test_oxygen_drains_underwater_and_refills_at_surface` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-03 | `Oxygen.test_oxygen_empty_then_choke_every_interval` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-04 | `Oxygen.test_faint_empties_hold_and_writes_empty_inventory` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-05 | `Harvest.*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-06 | `Harvest.test_no_harvest_underwater`, `test_nearest_tie_picks_smaller_id` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-07 | `Catch.*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-08 | `Harvest.test_hold_full_on_harvest`, `Catch.test_partial_room_fills_hold_then_hold_full` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-G-09 | Smoke `test_inv_01_*`; `Catch.test_dock_after_catch_writes_inventory` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo giả định clarify #1–5, chờ PO chốt) |
| AC-Q-01 | `test_ac_q_01_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-02 | `test_ac_q_02_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-03 | `test_ac_q_03_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-04 | `test_ac_q_04_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-05 | `test_ac_q_05_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-06 | `ScenarioConflicts.test_ac_q_06_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-07 | `test_ac_q_07_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-08 | `test_ac_q_08_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-09 | `test_ac_q_09_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-10 | `test_ac_q_10_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-11 | `test_ac_q_11_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-Q-12 | `test_ac_q_12_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt (theo clarify, PO còn đối chiếu PRD-0) |
| AC-UI-01 | Chơi gather bằng phím trên trình duyệt | [ui-gather-hud.png](../proof/phase-1/ui-gather-hud.png), [ui-gather-choke.png](../proof/phase-1/ui-gather-choke.png), [ui-gather-end-toast.png](../proof/phase-1/ui-gather-end-toast.png) | Đạt: chơi bằng phím trên Chrome headless, từ bến, hái, lặn bắt cá, về bến |
| AC-UI-02 | Chơi quan với `--inventory` lấy từ lượt gather | [ui-quan-inventory-flow.png](../proof/phase-1/ui-quan-inventory-flow.png), [ui-quan-hud.png](../proof/phase-1/ui-quan-hud.png), [ui-quan-paid.png](../proof/phase-1/ui-quan-paid.png) | Đạt: dùng kho của lượt gather, nấu, bưng, phục vụ, nhận 144k, uy tín 3.2 |
| AC-UI-03 | `tests/test_live.py` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| AC-UI-04 | Ảnh chụp hai chế độ | [ui-gather-hud.png](../proof/phase-1/ui-gather-hud.png), [ui-quan-hud.png](../proof/phase-1/ui-quan-hud.png) | Đạt |
| AC-QA-01 | Đối chiếu bảng này với các spec | File này | Đạt |
| AC-QA-02 | `tests/test_quan_rules.py` có test cho AC-Q-01..12 | [tests/test_quan_rules.py](../../tests/test_quan_rules.py) | Đạt |
| AC-QA-03 | 2 skill và mục Skills trong `AGENTS.md` | [phase-check](../../.agents/skills/phase-check/SKILL.md), [clarify-log](../../.agents/skills/clarify-log/SKILL.md) | Đạt |
| AC-QA-04 | `docs/ai-usage-log.md` có mục của cả 3 người | [ai-usage-log.md](../ai-usage-log.md) | Chưa đạt: đã có TV2 và TV3, còn thiếu TV1 |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đạt 28/29 AC. Còn AC-QA-04 vì `docs/ai-usage-log.md` chưa có mục của TV1.
- `phase-check` đạt 7/7 mục: 117 test xanh, không có test bị bỏ qua, headless 2 mode giống từng byte, luồng kho gather -> quan thông.
- Giao diện đã chơi bằng phím trên Chrome headless, phát đủ 13 loại toast trong spec và không có lỗi JavaScript. Chưa có người chơi thử trực tiếp.
- Nhiều AC dựa trên giả định trong `docs/clarify.md`; PO cần chốt các dòng còn ghi chờ với PRD-0.
- Điều cần chỉnh cho phase sau: gộp `main` thường xuyên hơn để test và UI không lệch tên trường.
