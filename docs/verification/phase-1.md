# Ma trận truy vết Phase 1

> Trạng thái ngày 2026-11-21 trên nhánh `feature/ui-qa-phase-1`. Luật gather (lát 1, 2) và quan (lát 3, 4) **chưa có trong repo**, nên các AC phụ thuộc vẫn ghi chưa đạt. Chạy lại `phase-check` và cập nhật bảng này sau khi gộp code của TV1, TV2.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-G-01 | `Oxygen.test_dive_and_surface_events` | Chưa có `tests/test_gather_rules.py` | Chưa đạt: chờ TV1 |
| AC-G-02 | `Oxygen.test_oxygen_drains_underwater_and_refills_at_surface` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-03 | `Oxygen.test_oxygen_empty_then_choke_every_interval` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-04 | `Oxygen.test_faint_empties_hold_and_writes_empty_inventory` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-05 | `Harvest.*` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-06 | `Harvest.test_no_harvest_underwater`, `test_nearest_tie_picks_smaller_id` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-07 | `Catch.*` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-08 | `Harvest.test_hold_full_on_harvest`, `Catch.test_partial_room_fills_hold_then_hold_full` | Chưa có test | Chưa đạt: chờ TV1 |
| AC-G-09 | Smoke `test_inv_01_*`; `Catch.test_dock_after_catch_writes_inventory` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: cập bến ghi kho đã xanh, phần sau khi bắt cá chưa có test |
| AC-Q-01 | `test_ac_q_01_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV2 |
| AC-Q-02 | `test_ac_q_02_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV2 |
| AC-Q-03 | `test_ac_q_03_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV2 |
| AC-Q-04 | `test_ac_q_04_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV2 |
| AC-Q-05 | `test_ac_q_05_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ vì chưa có khách, chờ TV2 |
| AC-Q-06 | `ScenarioConflicts.test_ac_q_06_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV2 |
| AC-Q-07 | `test_ac_q_07_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-Q-08 | `test_ac_q_08_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-Q-09 | `test_ac_q_09_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-Q-10 | `test_ac_q_10_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-Q-11 | `test_ac_q_11_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-Q-12 | `test_ac_q_12_*` | [unittest.txt](../proof/phase-1/unittest.txt) | Chưa đạt: test đỏ, chờ TV1 |
| AC-UI-01 | Chơi gather bằng phím trên trình duyệt | [ui-gather-hud.png](../proof/phase-1/ui-gather-hud.png), [ui-gather-end-toast.png](../proof/phase-1/ui-gather-end-toast.png) | Chưa đạt: HUD và cập bến chạy, chưa hái/bắt cá được vì thiếu luật gather |
| AC-UI-02 | Chơi quan với `--inventory` lấy từ lượt gather | [ui-quan-hud.png](../proof/phase-1/ui-quan-hud.png) | Chưa đạt: kho nạp đúng, HUD hiện đúng với scenario dựng sẵn, chưa có khách thật vì thiếu luật quan |
| AC-UI-03 | `tests/test_live.py` | [unittest.txt](../proof/phase-1/unittest.txt) | Đạt |
| AC-UI-04 | Ảnh chụp hai chế độ | [ui-gather-hud.png](../proof/phase-1/ui-gather-hud.png), [ui-quan-hud.png](../proof/phase-1/ui-quan-hud.png) | Đạt (ảnh dùng scenario dựng sẵn) |
| AC-QA-01 | Đối chiếu bảng này với các spec | File này | Đạt |
| AC-QA-02 | `tests/test_quan_rules.py` có test cho AC-Q-01..12 | [tests/test_quan_rules.py](../../tests/test_quan_rules.py) | Đạt (test đã viết; luật chưa qua) |
| AC-QA-03 | 2 skill và mục Skills trong `AGENTS.md` | [phase-check](../../.agents/skills/phase-check/SKILL.md), [clarify-log](../../.agents/skills/clarify-log/SKILL.md) | Đạt |
| AC-QA-04 | `docs/ai-usage-log.md` có mục của cả 3 người | [ai-usage-log.md](../ai-usage-log.md) | Chưa đạt: mới có mục của Đoàn Sỹ Hưng |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đạt 5/29 AC (UI-03, UI-04, QA-01, QA-02, QA-03). 24 AC còn lại chưa đạt, chủ yếu vì chưa có luật gather và quan.
- `phase-check` hiện đạt 6/7 mục. Mục không đạt là unittest: 59 test, 21 test đỏ, đều nằm trong `tests/test_quan_rules.py`.
- Bộ test quan đã được chạy thử với một bản luật tham chiếu viết tạm ngoài repo và xanh 59/59. Điều này chỉ cho thấy test thỏa mãn được, không phải bằng chứng luật của nhóm đúng.
- Điều cần chỉnh cho phase sau: gộp luật sớm hơn để QA kiểm trên code thật; PO chốt clarify #1–5 và #7.
