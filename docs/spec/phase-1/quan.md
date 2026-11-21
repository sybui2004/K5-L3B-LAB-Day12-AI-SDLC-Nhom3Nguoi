# Spec `sim/quan` — Buổi tối: Mở Quán (lát 3 + lát 4)

**File:** `chonoi/sim/quan.py` (+ `chonoi/scenario.py` phần `_validate_quan`)
**Lát 3 (mục A) — Thành viên 2** · plan: [../../plan/phase-1/quan-customers.md](../../plan/phase-1/quan-customers.md)
**Lát 4 (mục B) — Thành viên 1** · plan: [../../plan/phase-1/quan-kitchen.md](../../plan/phase-1/quan-kitchen.md)

> Khung đã có: đi lại (`walk_speed 4.0`, ramp, chặn biên `x ∈ [0,16]`, `z ∈ [0,10]`), đồng hồ (`duration_s 180`), nạp kho, `quan_end` khi hết giờ, snapshot.
> Mọi tên trường/sự kiện/thứ tự xử lý đánh dấu **[đối chiếu PRD-0]** phải được PO so với tab Phase 1 trên lab board **trước khi code** (mục F "Quán", mục E sự kiện, mục D scenario). Khác ⇒ sửa spec này, ghi `docs/clarify.md`.

## 0. Chia file giữa hai người (tránh xung đột)

TV2 đẩy commit **khung `step()`** đầu tiên (≤ 10 phút sau kickoff), các hàm rỗng trả `None`:

```python
def step(self, inp):
    events = []
    self.time_left_ticks = max(0, self.time_left_ticks - 1)
    self._tick_customers(events)   # TV2: kiên nhẫn, bỏ đi        [đối chiếu thứ tự PRD-0 mục F]
    self._tick_stoves(events)      # TV1: nấu -> dish_ready
    self._tick_eating(events)      # TV1: ăn xong -> paid
    self._move(inp)                # khung
    if inp.pressed("interact"):
        self._interact(events)     # TV1: tối đa MỘT đối tượng
    self._spawn_customer(events)   # TV2: khách mới theo lịch, no_dish
    if self.time_left_ticks <= 0: ...  # khung: quan_end
    return events
```

- TV2 sở hữu: `_tick_customers`, `_spawn_customer`, `_pick_dish`, `_reserve`, `_release`, phần khách trong `__init__`, `_validate_quan`.
- TV1 sở hữu: `_tick_stoves`, `_tick_eating`, `_interact`, `_cook`, `_pick_up`, `_serve`, `_pay`, `_change_reputation`.
- Hàm dùng chung (TV2 viết, TV1 gọi): `_can_cook(dish, stock_free) -> bool`, `_reserve(customer, dish)`, `_release(customer)`.

## Dữ liệu (từ `game.contract.json`)
- Bếp `B1 [2,8]`, bàn `T1 [9,2]`, `interact_radius 1.5`, `carry_limit 1`.
- Khách: `first_customer_tick 120`, `customer_interval_s 15` (900 tick), `patience_s 60` (3600 tick), `eat_s 10` (600 tick).
- Menu: `ca_loc_nuong_trui {ca_loc:1} 6s 60đ`, `goi_bong_sung {bong_sung:2} 4s 40đ`, `lau_ca_linh_dien_dien {ca_linh:3, bong_dien_dien:1} 10s 120đ`. `burn_s: null` ⇒ Phase 1 **không** cháy món.
- Tiền/uy tín: `tip_rate 0.2`, `tip_min_patience_ratio 0.5`, `tip_reputation +0.2`, `left_reputation_delta -0.5`, uy tín đầu ca 3.0, kẹp `[0, 5]`.

## A. Lát 3 — Khách (TV2)

### A1. Vòng đời khách **[đối chiếu PRD-0 mục F]**
`waiting` (đã ngồi, chờ món) → `eating` (đã được phục vụ) → rời bàn khi `paid`; hoặc `waiting` → hết kiên nhẫn ⇒ `customer_left`.

Trường khách trong snapshot (sắp theo id): `id, table_id, dish, state, patience_ticks, reserved {kind: n}` (+ `eat_ticks`, `price`, `tip` khi `eating`). **[đối chiếu PRD-0 mục D/F: tên trường scenario `customers[]`]**

### A2. Khách đến
- Tick lịch: `first_customer_tick`, rồi mỗi `customer_interval_s × 60` tick. Cấp id bằng `self.ids` (`IdAllocator`).
- Chọn bàn trống có id nhỏ nhất; không có bàn trống ⇒ **[đối chiếu: bỏ lượt hay xếp hàng]**.
- Chọn món: các món **nấu được** từ phần kho **chưa bị giữ chỗ**; chọn ngẫu nhiên qua `self.rng` (stream riêng cho khách, `self.rng.get("customers")` — xem `chonoi/rng.py`). Thứ tự ứng viên: tên món sắp tăng dần để tất định.
- Không món nào nấu được ⇒ `no_dish` (khách không ngồi). **[đối chiếu data]**
- Có món ⇒ giữ chỗ nguyên liệu (`reserved` = recipe), phát `customer_arrived {customer_id, table_id, dish}` **[đối chiếu tên sự kiện]**.
- `random_customers: false` trong scenario ⇒ tắt khách theo lịch (chỉ dùng khách dựng sẵn).

### A3. Kiên nhẫn
- Khách `waiting`: `patience_ticks -= 1` mỗi bước. Về 0 ⇒ nhả giữ chỗ, bàn trống, `reputation += left_reputation_delta` (kẹp), phát `customer_left {customer_id, table_id}`.
- Bàn đang được TV1 phục vụ ở cùng tick: thứ tự xử lý theo PRD-0 mục F **[đối chiếu]**.

### A4. Scenario quan (`chonoi/scenario.py::_validate_quan`) — mâu thuẫn ⇒ mã 2
Đã có: id trùng, bàn không tồn tại, hai khách cùng bàn. Cần thêm (theo docstring khung):
- Tổng `reserved` của khách > kho tương ứng.
- Khách có món không thuộc menu / `reserved` khác recipe của món.
- Khách `eating` thiếu `price`/`tip`; khách `waiting` có `patience_ticks` ngoài `[1, patience_s×60]`.
- `hand` không phải món thuộc menu (hoặc null); bếp `state` ngoài tập cho phép.
Mỗi luật một test exit 2 trong `tests/test_quan_rules.py`.

### AC lát 3
| AC | Nội dung |
|---|---|
| AC-Q-01 | Không có input: khách đầu tiên đến đúng tick 120 (nếu kho nấu được ít nhất một món) |
| AC-Q-02 | Kho rỗng ⇒ `no_dish`, không bàn nào có khách |
| AC-Q-03 | Món được chọn luôn nấu được từ kho chưa giữ chỗ; giữ chỗ trừ đúng recipe |
| AC-Q-04 | Hết kiên nhẫn ⇒ `customer_left`, uy tín -0.5, nhả giữ chỗ |
| AC-Q-05 | Cùng seed ⇒ cùng chuỗi món (byte-identical) |
| AC-Q-06 | Scenario mâu thuẫn (mục A4) ⇒ mã thoát 2 |

## B. Lát 4 — Bếp, bưng, phục vụ, tiền (TV1)

### B1. Chọn đối tượng `interact`
Tối đa **một** đối tượng mỗi bước: lọc bếp/bàn trong `interact_radius`, sắp theo `(khoảng cách, bếp trước bàn, id)`, lấy đầu tiên, làm hành động hợp lệ của nó; không hợp lệ thì thôi (không thử đối tượng kế). **[đối chiếu PRD-0 mục F]**

### B2. Bếp
- Bếp `idle` + tay không + có khách `waiting` có món chưa nấu ⇒ nấu món của khách **id nhỏ nhất** đang chờ **[đối chiếu: món nào được nấu]**: trừ nguyên liệu đã giữ chỗ khỏi kho, `state = cooking`, `cook_ticks_left = cook_s × 60`, `cook_started {stove_id, dish}`.
- `_tick_stoves`: `cooking` giảm `cook_ticks_left`; về 0 ⇒ `state = ready`, `dish_ready {stove_id, dish}`. (`burn_s` null ⇒ `ready_ticks` chỉ đếm, không cháy.)
- Bếp `ready` + tay trống (`carry_limit 1`) ⇒ `hand = dish`, bếp `idle`, `dish_picked {stove_id, dish}`.

### B3. Bàn
- Bàn có khách `waiting` đúng món đang cầm ⇒ `hand = None`, khách `eating`, `eat_ticks = eat_s × 60`, chốt `price` (menu) và `tip = round(price × tip_rate)` nếu `patience_ticks / (patience_s×60) >= tip_min_patience_ratio`, ngược lại 0; `served {customer_id, table_id, dish}`.
- Cầm sai món ⇒ không làm gì **[đối chiếu]**.

### B4. Ăn xong, trả tiền
`_tick_eating`: `eat_ticks` về 0 ⇒ `money += price + tip`, `earned += price + tip`, `shift_earned += ...`, nếu có tip thì `reputation += tip_reputation` (kẹp `[0,5]`), khách rời bàn, `paid {customer_id, amount, tip}`. **[đối chiếu PRD-0: earned vs shift_earned, làm tròn]**

### AC lát 4
| AC | Nội dung |
|---|---|
| AC-Q-07 | Đứng cạnh bếp, `interact` ⇒ `cook_started`; sau `cook_s×60` tick ⇒ `dish_ready` |
| AC-Q-08 | `interact` ở bếp chín ⇒ `dish_picked`, tay cầm món; tay đầy thì không nhặt |
| AC-Q-09 | Bưng đúng món tới bàn ⇒ `served`; sau `eat_s×60` tick ⇒ `paid`, tiền tăng đúng giá + boa |
| AC-Q-10 | Phục vụ khi kiên nhẫn ≥ 50% ⇒ có boa và uy tín +0.2; < 50% ⇒ không boa |
| AC-Q-11 | Một `interact` chỉ tác động một đối tượng, ưu tiên (khoảng cách, bếp, id) |
| AC-Q-12 | Hết giờ ⇒ `quan_end` với `money, earned, shift_earned, reputation` khớp snapshot |

## Câu hỏi mở (PO ghi vào `docs/clarify.md` nếu PRD-0 không trả lời)
1. Thứ tự xử lý trong một bước quan (kiên nhẫn trước hay sau interact? khách mới trước hay sau?).
2. Bàn đầy khi tới lịch khách: bỏ lượt hay dời?
3. Nấu món của khách nào khi có nhiều khách chờ (id nhỏ nhất? đến trước?).
4. Tên/`data` chính xác của `customer_arrived`, `no_dish`, `customer_left`, `paid`.
5. Cách làm tròn tiền boa; `earned` khác `shift_earned` thế nào.
