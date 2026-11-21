# Spec lát 4 — `--mode day`, chuyển pha, pause, menu, HUD, QA (TV3)

> Nguồn: Ticket-02 mục 2 (vòng ngày, menu/pause/HUD), 4.1–4.5, 5 (quy trình). Giao diện sim: [README.md](README.md) mục 3.
> File: mới `chonoi/sim/day.py`; sửa khung `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/inputs.py`, `chonoi/scenario.py` (khối `day`), `chonoi/live.py`, `chonoi/web/index.html`.
> **Tích hợp sớm bằng fixture:** trong lúc TV1/TV2 chưa xong, `DaySim` gọi `GatherSim`/`QuanSim` hiện có + một `ShopSim` giả (đóng ngay khi `shop_done`). Đổi sang bản thật khi gộp.

## A. CLI và vòng ngày (AC-P2-18, 19)

### A1. CLI
```
python -m chonoi.headless --mode gather|quan|day --seed N [--scenario s.json] [--inputs i.json]
  [--inventory k.json] [--inventory-out k.json] [--days N] --ticks N --out f.jsonl [--snapshot-every N]
```
- `--days` chỉ hợp lệ với `day`, số nguyên 1..5, mặc định 1; sai ⇒ mã 2.
- `--inventory`/`--inventory-out` với `day` ⇒ mã 2 (chỉ cho hai mode độc lập).

### A2. Máy trạng thái `DaySim`
```
day_start → day_plan → phase_start(gather) … gather_end
  → phase_start(quan) [cùng tick] … quan_end
  → phase_start(shop) [cùng tick] … shop_end
  → days_completed += 1 → (Ngày kế: day_start …) | kết thúc reason "days_complete"
```
- Ngày mới: phát `day_start {}` → `day_plan {dishes, ingredients}` → `phase_start {}` (gather) ở cùng tick dựng Ngày. Ngày 1 dựng lúc khởi tạo, nên ba event này mang `tick: 0` (theo ví dụ của đề). Ghi chúng trước hay sau snapshot tick 0 ⇒ **[clarify #19]**, tạm chọn: snapshot tick 0 trước, rồi ba event.
- Đổi pha: dựng sim pha mới và phát `phase_start` **cùng tick** với event kết thúc pha cũ; pha mới chạy gameplay **từ bước sau**. Event kết thúc mang `phase` cũ; snapshot đổi pha ghi pha mới với `phase_tick: 0`.
- Ngất ⇒ vẫn sang quan với kho rỗng.
- Đóng Shop ⇒ `days_completed += 1`; nếu `days_completed == days` ⇒ kết thúc; ngược lại dựng Ngày kế **ngay tick đó**.
- Một Ngày không pause dài tối đa 10.800 + 10.800 + 600 = **22.200 tick**.

### A3. Trạng thái xuyên Ngày
| Giữ qua Ngày | Làm mới mỗi Ngày |
|---|---|
| `money`, `earned`, `reputation`, `upgrades` (đã mua) | Máu, oxy đầy theo `active_upgrades`; giỏ rỗng; kho dư bỏ sau Shop |

- `active_upgrades` = bản sao `upgrades` **chỉ khi dựng Ngày mới**. Mua ở Shop Ngày 1 ⇒ áp từ Ngày 2.
- `hp_max` = `shop.upgrades.hp[level-1].hp_max` (cấp 0 ⇒ tuning gather); tương tự `oxygen_max_s`.
- Bố trí quái theo Ngày (`from_day`): M2 xuất hiện từ Ngày 3.

### A4. Output (AC-P2-22)
- Snapshot mọi pha thêm `day, day_plan, upgrades, active_upgrades`; `phase ∈ {gather, quan, shop}`; `state` thêm `"paused"`.
- Vỏ event ở `day` thêm khóa `day`.
- Dòng `end` thêm `days_completed`; xong đủ Ngày ⇒ `reason:"days_complete"`, hết `--ticks` trước ⇒ `"tick_limit"`.
- Ví dụ đề: `{"type":"event","tick":0,"phase":"gather","day":1,"name":"day_plan","data":{...}}` — event dựng Ngày 1 có `tick:0` **[clarify #19]**.

## B. Pause (AC-P2-20) — áp cho cả 3 mode, làm ở `runner.Session`
- Nút boolean mới `pause` (cả 3 mode), `shop_done` (Shop). Tất cả tính **cạnh lên**; giữ nút qua đổi pha không tạo cạnh mới (bộ chốt nút liên tục qua các pha).
- `buy` là chuỗi khác rỗng, chỉ chạy tại frame khai báo.
- Mỗi bước, xét cạnh `pause` **trước**:
  - Đang chạy + cạnh `pause` ⇒ chỉ `tick += 1`, cập nhật chốt nút, phát `paused {}`. Không gọi `sim.step`.
  - Đang pause, không có cạnh ⇒ `tick += 1`, bỏ qua cạnh hành động và `buy`.
  - Đang pause + cạnh `pause` ⇒ phát `resumed {}` **và** chạy gameplay ngay trong bước đó.
- `sim_tick`, `phase_tick`, lịch khách/cá, timer Shop đứng yên khi pause.
- Session tách `tick` / `sim_tick` / `phase_tick` (hiện `_common` dùng `self.tick` cho cả ba ⇒ sửa).

## C. Scenario `day` (AC-P2-21)
- `day` nhận `gather` và `quan` làm mẫu khởi tạo mỗi Ngày.
- Khối `day {money, earned, reputation, upgrades, day_plan}`: mặc định `money=earned=0`, `reputation` theo tuning, `upgrades={}`, `day_plan` theo preset.
- Kiểm (mã 2): `0 ≤ money ≤ earned`; khai `money` thì phải khai `earned`; có `quan.stock` hoặc `quan.reputation` khi `day`; `day.day_plan[i]` thiếu `dishes`; `ingredients` khai khác giá trị tính lại (`plan_ingredients`, TV2).
- Kho, khách, bếp, món thuộc kế hoạch được kiểm trên **kho thực lúc mở quán**; mâu thuẫn ⇒ mã 2.
- Ví dụ đề: `{"day":{"money":200,"earned":200},"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}` — tương tác khi ở bến đóng ca sáng ngay.

## D. UI (`chonoi.live` + `chonoi/web/`) (AC-P2-24 … 26)

### D1. Màn hình (chỉ ở client, sim **không** chạy trong lúc hiện)
| Màn | Nội dung | Rời màn |
|---|---|---|
| Menu chính | Chơi, Thoát | chọn |
| DayIntro | "Ngày n", Má Tư đọc danh sách món + nguyên liệu cần | 4 s hoặc nhấn phím |
| EveningIntro | số lượng nhập kho, món nấu được | phím / vài giây |
| DayResult | khách đã phục vụ/bỏ đi, tiền, boa, thay đổi uy tín (`QuanSim.stats()`) | phím |
| Shop | cấp oxygen/hp, giá, tiền; mua; Xong (`shop_done`) | `shop_end` |
| Summary (sau Ngày 5) | tổng tiền, tổng điểm, uy tín, món bán chạy | về menu |

### D2. Pause
Esc/P gửi `pause`. Menu pause làm mờ nền, nút **Tiếp tục** và **Về menu**. Đồng hồ và mọi timer dừng, kể cả trong Shop.

### D3. HUD
- **Sáng:** Máu; oxy (< 25% đổi màu/nhấp nháy); thời gian (≤ 30 s đổi màu); độ sâu; giỏ theo loại; danh sách cần lấy dạng đã lấy/cần; hồi bắt; gợi ý hái/cập bến khi gần; "Thủy quái!" + viền tím khi quái gần; "Hết hơi!" khi oxy cạn.
- **Quán:** đồng hồ ca, tiền ca, uy tín; món + kiên nhẫn từng bàn (< 25% đổi màu); tiến độ bếp / món chín; món đang cầm; kho khả dụng.
- Chữ không chân ≥ 18 px ở 1280×720; trung bình ≥ 30 FPS.

## E. QA và bằng chứng
- `tests/test_p2_day.py`: chuỗi event Ngày 1 (AC-P2-18); mua oxygen ở Ngày 1 ⇒ `active_upgrades.oxygen` = 0 trong Ngày 1, = 1 ở Ngày 2 và oxy max 2700 (AC-P2-19); pause giữa gather giữ nguyên `sim_tick` (AC-P2-20); scenario cấm `quan.stock` ⇒ mã 2 (AC-P2-21); 1 Ngày headless ≤ 20 s và chạy 2 lần giống byte (AC-P2-23).
- Smoke tích hợp phút 20 (AC-P2-27): `gather --seed 1 --inventory-out kho.json` → `quan --inventory kho.json`; so `stock` ở snapshot tick 0 với `kho.json`; lưu `docs/proof/phase-2/integration.{md,jsonl}`.
- Smoke `day --days 1` và `--days 3` (kiểm cấp nâng cấp, M2) phút 35–45; lưu `docs/proof/phase-2/day-*.jsonl`.
- Điền `docs/verification/phase-2.md` (AC ↔ bằng chứng ↔ kết quả trên commit tag).
