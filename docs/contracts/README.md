# Hợp đồng tích hợp

> Ghi theo code đang chạy trên `main` (Test Contract v1.2). Phần `--mode day`, Shop và pause xem [`docs/spec/phase-2/`](../spec/phase-2/README.md). Số liệu cân bằng nằm trong [`game.contract.json`](../../game.contract.json).

## 1. File kho (v1.2)

```json
{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 99.99166666666666}]}
```

- Gốc chỉ có khóa `items`, là mảng cá thể sắp theo id. Kho rỗng là `{"items": []}`. Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json).
- `id` là chuỗi khác rỗng, duy nhất. `kind` thuộc `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, `ca_keo`, `keo_neo`. `fresh` là số trong `[0, 100]`.
- Hàng **ươn** khi `fresh < spoiled_below` (30). File ghi `fresh` đầy đủ, JSONL làm tròn 3 chữ số.
- `gather --inventory-out` ghi **một lần** khi có `gather_end`, qua file tạm rồi thay thế. Ngất ghi kho rỗng. Hết `--ticks` trước khi kết thúc buổi thì không đụng file đích.
- `quan` nhận kho qua `--inventory` **hoặc** `scenario.quan.stock`, không dùng cả hai.
- Kho đếm kiểu cũ `{"items": {"ca_loc": 2}}`, sai schema, kind lạ, id trùng hoặc rỗng, `fresh` ngoài miền: mã thoát 2.

## 2. Giao diện `sim/*` và `client/ui`

UI chạy cùng lớp sim với headless, chỉ đọc trạng thái và gửi input, không chứa luật.

| API | Nội dung |
|---|---|
| `GET /state` | Snapshot hiện tại + `meta` (tuning của mode), `events` (tối đa 40 dòng gần nhất), `finished`, `reason`, `error` |
| `POST /input` | `{"move": [a, b], "interact": bool, "catch": bool}`, mỗi thành phần `move` trong `[-1, 1]` |
| `POST /restart` | Chơi lại từ đầu với cùng seed và scenario |

Trường snapshot:

| Phạm vi | Trường |
|---|---|
| Chung | `type, tick, sim_tick, mode, phase, phase_tick, state, time_left_ticks, money, earned, reputation, score` |
| Gather | `player {pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface}`, `hold[] {id, kind, fresh}, hold_count, hold_capacity`, `nodes[] {id, pos, kind, ready, regrow_ticks}`, `fish[] {id, pos, kind, heading_deg, age_ticks}`, `monsters[] {id, kind, pos, state, target_idx, state_ticks_left, recoil_dir}` |
| Quán | `player {pos, vel}`, `stock[] {id, kind, fresh}, hand, hand_base_price, shift_earned`, `stoves[] {id, pos, state, dish, order_id, base_price, cook_ticks_left, ready_ticks}`, `tables[] {id, pos, customer_id}` |
| Khách | `customers[] {id, table_id, dish_id, state, patience_ticks_left, order_tick, order_status, reserved[] (id cá thể)}`, thêm `eat_ticks_left, price, tip` khi `state = eating` |

Sim muốn UI hiện thêm gì thì thêm trường vào `snapshot()` và cập nhật bảng này.

## 3. Danh sách sự kiện

Dòng JSONL: `{"type": "event", "tick": k + 1, "phase": ..., "name": ..., "data": {...}}`.
Người nghe: `client/ui` (toast, nhật ký sự kiện), lớp sáng tạo `?creative=1`, và test hộp đen của `qa`.

### Gather (`chonoi/sim/gather.py`)

| Sự kiện | `data` |
|---|---|
| `dive`, `surface`, `oxygen_empty` | `{pos}` |
| `choke` | `{hp}` |
| `monster_hit` | `{monster_id, hp, lost: [cá thể], pos}` |
| `faint` | `{pos, lost: [cá thể], hp}`, thêm `cause` khi do quái |
| `spoiled` | `{item_id, kind, location: hold \| stock}` |
| `gather` | `{node_id, kind, count}` |
| `node_regrown` | `{node_id}` |
| `fish_caught` | `{fish_id, kind, count}` |
| `hold_full` | `{source, kind}` |
| `gather_end` | `{reason: docked \| time \| fainted, inventory: {items: [cá thể]}}` |

### Quán (`chonoi/sim/quan.py`)

| Sự kiện | `data` |
|---|---|
| `customer_arrived` | `{customer_id, table_id, dish_id}` |
| `no_dish` | `{table_id}` |
| `customer_left` | `{customer_id, table_id, dish_id, reason: patience \| closing}` |
| `cook_started` | `{stove_id, order_id, dish_id, items: [cá thể], base_price}` |
| `dish_ready` | `{stove_id, order_id, dish_id}` |
| `dish_picked` | `{stove_id, order_id, dish_id, base_price}` |
| `served` | `{customer_id, table_id, dish_id, price, tip}` |
| `paid` | `{customer_id, table_id, dish_id, price, tip, amount}` |
| `quan_end` | `{reason: time, money, earned, shift_earned, reputation}` |

Khi đổi hợp đồng: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú).
