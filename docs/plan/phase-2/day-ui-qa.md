# Plan Phase 2 — TV3 (hgmdz1210, Hưng): lát 4 day/pause + UI + QA

Spec: [day-ui](../../spec/phase-2/day-ui.md) · [chung](../../spec/phase-2/README.md)
Nhánh: `feature/p2-day-ui`. Phần sáng tạo (`feature/creative-ui`) **tạm dừng** tới khi lõi Phase 2 xanh.

## Bước 1 — Khung day + pause (phút 5–20)
- [ ] `chonoi/inputs.py`: nút `pause`, `shop_done`; `buy` là chuỗi chỉ ở frame khai báo; chốt nút liên tục qua đổi pha.
- [ ] `chonoi/runner.py`: tách `tick`/`sim_tick`/`phase_tick`; pause trong `Session` (mục B spec); `build_sim("day")`; `end` thêm `days_completed`.
- [ ] `chonoi/headless.py`: bật `--mode day`, `--days 1..5`, cấm cờ kho với `day` (mã 2).
- [ ] `chonoi/sim/day.py`: máy trạng thái mục A2 với GatherSim/QuanSim hiện có + ShopSim giả; vỏ event thêm `day`; snapshot thêm `day, day_plan, upgrades, active_upgrades`.

## Bước 2 — Smoke tích hợp (phút 20) — cùng TV1
Fixture để kho không rỗng: `docs/proof/phase-2/smoke-scenario.json` = `{"gather":{"hold":["ca_loc","ca_keo","ca_keo","keo_neo","bong_sung","bong_sung"],"random_fish":false}}` và `smoke-inputs.json` bấm `interact` ở tick 0 (đang ở bến ⇒ cập bến ngay).
```bash
python -m chonoi.headless --mode gather --seed 1 --ticks 10800 --scenario docs/proof/phase-2/smoke-scenario.json --inputs docs/proof/phase-2/smoke-inputs.json --out docs/proof/phase-2/integration-gather.jsonl --inventory-out /tmp/kho.json
python -m chonoi.headless --mode quan --seed 1 --ticks 600 --out docs/proof/phase-2/integration-quan.jsonl --inventory /tmp/kho.json
```
- [ ] So `stock` ở snapshot tick 0 của quan với `kho.json`; ghi kết quả + lệnh vào `docs/proof/phase-2/integration.md`.
- [ ] Ghi standup vào `docs/standup.md`.

## Bước 3 — Day thật + scenario + UI (phút 20–35)
- [ ] Thay ShopSim giả bằng bản thật (TV2); truyền `ctx` (`hp_max`, `oxygen_max_s` theo `active_upgrades`).
- [ ] Scenario khối `day` + kiểm mã 2 (mục C spec).
- [ ] `chonoi.live` + `chonoi/web/`: mode day, menu chính, DayIntro/EveningIntro/DayResult/Shop/Summary, pause Esc/P, HUD sáng + quán (mục D spec).
- [ ] `tests/test_p2_day.py` AC-P2-18…23.

## Bước cuối — Bằng chứng (phút 35–50)
- [ ] `day --days 1` và `--days 3` seed 1 → `docs/proof/phase-2/day-*.jsonl`; đo thời gian 1 Ngày (`time`), ≤ 20 s.
- [ ] Regression P1: toàn bộ unittest trên commit bàn giao → `docs/proof/phase-2/unittest.txt`.
- [ ] Ảnh chụp HUD/menu ở 1280×720 → `docs/proof/phase-2/`.
- [ ] Điền `docs/verification/phase-2.md` (mỗi AC một dòng: cách kiểm, bằng chứng, kết quả trung thực).
- [ ] Cập nhật `docs/ai-usage-log.md`, `AGENTS.md` (lệnh `--mode day`).

## Dự phòng
UI chưa kịp ⇒ ưu tiên headless `day` + pause (được chấm tự động), UI làm tối thiểu menu + HUD, ghi chỗ thiếu trong verification.
