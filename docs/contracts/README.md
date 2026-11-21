# Hợp đồng tích hợp

> Ghi theo code đang chạy trên `main` (`b3b654f`, Test Contract v1.1). Phần `--mode day`, Shop và pause xem [`docs/spec/phase-2/`](../spec/phase-2/README.md). Số liệu cân bằng nằm trong [`game.contract.json`](../../game.contract.json).

## 1. File kho

```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```

- Gốc chỉ có khóa `items`. Mỗi mục là `id nguyên liệu: số nguyên >= 0`. Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json).
- Id hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`, `ca_keo`, `keo_neo`.
- `gather --inventory-out` ghi **một lần** khi có `gather_end`. Mục bằng 0 bị bỏ, khóa sắp tăng dần, ghi qua file tạm rồi thay thế. Hết `--ticks` trước khi kết thúc buổi thì không ghi.
- `quan` nhận kho qua `--inventory` **hoặc** `scenario.quan.stock`, không dùng cả hai.
- Sai schema, id lạ, số âm hoặc dùng cả hai nguồn kho: mã thoát 2.

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
| Gather | `player {pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, invuln_ticks, catch_cd_ticks, at_surface}`, `hold, hold_count, hold_capacity`, `nodes[] {id, pos, kind, ready, regrow_ticks}`, `fish[] {id, pos, kind, heading_deg}` |
| Quán | `player {pos, vel}`, `stock, hand, shift_earned`, `stoves[] {id, pos, state, dish, order_id, cook_ticks_left, ready_ticks}`, `tables[] {id, pos, customer_id}` |
| Khách | `customers[] {id, table_id, dish_id, state, patience_ticks_left, order_tick, order_status, reserved}`, thêm `eat_ticks_left, price, tip` khi `state = eating` |

Sim muốn UI hiện thêm gì thì thêm trường vào `snapshot()` và cập nhật bảng này.

## 3. Danh sách sự kiện

Dòng JSONL: `{"type": "event", "tick": k + 1, "phase": ..., "name": ..., "data": {...}}`.
Người nghe: `client/ui` (toast, nhật ký sự kiện), lớp sáng tạo `?creative=1`, và test hộp đen của `qa`.

### Gather (`chonoi/sim/gather.py`)

| Sự kiện | `data` |
|---|---|
| `dive`, `surface`, `oxygen_empty` | `{pos}` |
| `choke` | `{hp}` |
| `faint` | `{pos, lost: {items}}` |
| `gather` | `{node_id, kind, count}` |
| `node_regrown` | `{node_id}` |
| `fish_caught` | `{fish_id, kind, count}` |
| `hold_full` | `{source, kind}` |
| `gather_end` | `{reason: docked \| time \| fainted, inventory: {items}}` |

### Quán (`chonoi/sim/quan.py`)

| Sự kiện | `data` |
|---|---|
| `customer_arrived` | `{customer_id, table_id, dish_id}` |
| `no_dish` | `{table_id}` |
| `customer_left` | `{customer_id, table_id, dish_id, reason: patience \| closing}` |
| `cook_started`, `dish_ready`, `dish_picked` | `{stove_id, order_id, dish_id}` |
| `served` | `{customer_id, table_id, dish_id, price, tip}` |
| `paid` | `{customer_id, table_id, dish_id, price, tip, amount}` |
| `quan_end` | `{reason: time, money, earned, shift_earned, reputation}` |

Khi đổi hợp đồng: báo cả nhóm và ghi lại lý do (ADR hoặc ghi chú).
