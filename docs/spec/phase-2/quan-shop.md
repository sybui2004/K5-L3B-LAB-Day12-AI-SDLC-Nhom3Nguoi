# Spec lát 3 — `sim/quan` v1.1 + kế hoạch ngày + `sim/shop` (TV2)

> Nguồn: Ticket-02 mục 1.3, 2 (vòng ngày, Shop), 4.2 (`buy`, `shop_done`), 4.4, 4.5 (Quán, Shop). Giao diện `ctx`: [README.md](README.md) mục 3.2.
> File: `chonoi/sim/quan.py`, mới `chonoi/sim/shop.py`. Lát 4 của Phase 1 (bếp/bưng/tiền) phải gộp vào `main` **trước** khi bắt đầu lát này.

## A. Quán 2 bếp / 4 bàn / 6 món (AC-P2-10 … 13)

### A1. Bố trí và dữ liệu
- Bếp, bàn, món đọc từ `self.t["stoves"]`, `self.t["tables"]`, `self.menu` (đã có trong v1.1). Không vòng lặp nào giả định 1 bếp / 1 bàn.
- Kho nhận đủ 6 loại (`ca_keo`, `keo_neo` mới).

### A2. Tương tác (AC-P2-11)
- Mục tiêu = vật gần nhất trong `interact_radius` (1.5 m). Hòa khoảng cách: **bếp trước bàn**, rồi theo id.
- Tay cầm tối đa 1 món (`carry_limit`).
- Tương tác bếp rảnh: nấu đơn `reserved` **cũ nhất theo `order_tick`**, hòa theo id bàn. Mỗi đơn cần lưu `order_tick` (= `phase_tick` lúc gọi món).
- Bếp có món chín + tay rỗng ⇒ bưng (`dish_picked`). Bàn có khách chờ đúng món đang cầm ⇒ `served`.

### A3. Khách (AC-P2-12)
- Lượt khách ở `phase_tick = 120 + 900·k` (k ≥ 0) **[clarify #13]**. Có bàn trống ⇒ ngồi bàn trống id nhỏ nhất; không có ⇒ bỏ lượt, không event (clarify #9).
- Gọi món xong giữ chỗ nguyên liệu ngay. Kiên nhẫn 3600 tick, ăn 600 tick.
- Boa `floor(giá × 0.2)` nếu kiên nhẫn còn ≥ 50% (≥ 1800 tick) lúc giao; thu boa dương ⇒ uy tín +0.2. Khách hết kiên nhẫn khi ca còn giờ ⇒ −0.5. Kẹp [0,5].

### A4. Chọn món (AC-P2-15)
- Ứng viên = món nấu được từ **kho trừ phần đang giữ**, sắp theo id; chọn đều bằng `Streams.get("customers").choice`.
- Trong `day`: lọc theo id món có trong `ctx["plan_dishes"]` **trước** rồi mới lọc nguyên liệu. Không giới hạn theo số suất (bán quá số suất vẫn được).
- Quán độc lập (`ctx is None`): dùng cả 6 món.
- Có bàn trống nhưng không món nào ⇒ `no_dish`.

### A5. Đóng ca (AC-P2-13)
Khi hết giờ: khách **đang ăn trả tiền ngay** (có boa theo luật lúc giao); khách **đang chờ rời, không trừ uy tín**; dọn món trên bếp/tay và phần giữ của đơn. Sau đó `quan_end`. `burn_s: null` ⇒ không có cháy món.

### A6. Dùng trong `day`
- Khởi tạo từ `ctx`: `money`, `earned`, `reputation` mang sang; kho = `inventory` bàn giao từ gather (rỗng nếu ngất).
- `stats()` trả `{served, left, money_shift, tips, reputation_delta, best_dish}` để UI vẽ DayResult/Summary.
- Scenario quan **không** dùng `stock`/`reputation` khi mode `day` (TV3 kiểm mã 2).

## B. Kế hoạch ngày (AC-P2-14)
- `tuning.day_plan` là mảng 5 Ngày `{day, dishes, ingredients}` (xem [contract-v1.1.md](contract-v1.1.md) mục 5).
- Viết hàm thuần `plan_ingredients(dishes, menu) -> dict` (Σ recipe × suất) trong `chonoi/sim/plan.py` ✱; dùng ở `contract.py` (kiểm dữ liệu) và ở scenario `day.day_plan` (TV3 tính lại, so với giá trị khai).
- Không có thưởng khi lấy đủ danh sách.

## C. Shop (`chonoi/sim/shop.py`) (AC-P2-16, 17)

### C1. Trạng thái
`money`, `earned` (chỉ đọc), `upgrades` = cấp **đã mua** `{oxygen: 0..2, hp: 0..2}`, `stock` (kho dư, chỉ hiển thị), `time_left_ticks = shop.max_ticks` (600).

### C2. Một bước Shop (thứ tự)
1. Nếu frame có `buy` (chuỗi, chỉ chạy đúng frame khai báo) ⇒ xử lý một lệnh mua.
2. Cạnh lên `shop_done` ⇒ `shop_end(done)`, kết thúc.
3. Giảm `time_left_ticks`; về 0 ⇒ `shop_end(time)`.

Bước cuối có cả `buy` và `shop_done`: mua trước rồi `shop_end(done)`.

### C3. Lệnh mua
| `buy` | Xử lý |
|---|---|
| `oxygen`, `hp` | cấp kế = cấp hiện tại + 1. Hết cấp ⇒ `buy_failed{action, reason:"max_level"}`. `money < price` ⇒ `reason:"funds"`. Ngược lại `money -= price` (đủ **đúng** giá vẫn mua), `upgrades[kind] = level`, phát `bought{upgrade, level, price, money}` (`money` sau trừ). |
| `weapon`, `net`, `buy:<kind>`, `sell:<kind>` | mở rộng chưa bật ⇒ **bỏ qua** (không event) **[clarify #18]** |
| chuỗi khác | `buy_failed{action, reason:"unknown"}` |

- Không trừ `earned`, không đổi điểm. Cấp vừa mua hiện ngay trong `upgrades`; **hiệu lực từ Ngày kế** (TV3 sao sang `active_upgrades` khi dựng Ngày mới).
- Snapshot Shop: `phase:"shop"`, `stock`, `time_left_ticks`, `upgrades`, `money`, `earned`.

## D. Test hộp đen (`tests/test_p2_quan_shop.py`)
- AC-P2-10/11: hai bếp, người đứng cách B1 và T1 bằng nhau ⇒ chọn bếp; hai đơn reserved ⇒ bếp nấu đơn `order_tick` nhỏ hơn.
- AC-P2-12: khách thứ 2 đến `phase_tick` 1020; 4 bàn đầy ⇒ lượt 5 bỏ qua.
- AC-P2-13: hết giờ khi 1 khách ăn + 1 khách chờ ⇒ tiền khách ăn cộng, uy tín không giảm.
- AC-P2-14: `plan_ingredients` khớp cả 5 Ngày trong bảng đề.
- AC-P2-15: `plan_dishes={"goi_bong_sung":3}` với kho đủ cá lóc ⇒ khách chỉ gọi gỏi.
- AC-P2-16: tiền 200 mua `oxygen` ⇒ còn 0; mua `hp` ⇒ `funds`; mua oxygen 3 lần đủ tiền ⇒ lần 3 `max_level`; `buy:"xyz"` ⇒ `unknown`.
- AC-P2-17: `shop_done` + `buy` cùng frame ⇒ `bought` rồi `shop_end(done)`; không bấm ⇒ `shop_end(time)` sau đúng 600 bước.
- Regression P1 quan (`tests/test_quan_customers.py`, test lát 4) chạy với số v1.1; test đổi ghi lý do.
