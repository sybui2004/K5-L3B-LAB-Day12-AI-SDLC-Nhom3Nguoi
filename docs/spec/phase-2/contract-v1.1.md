# Lát 0 — `game.contract.json` v1.1 (số chuẩn Ticket-02)

> Chủ: TV1. Đây là **commit đầu tiên** của Phase 2 (phút 0–8), mọi lát khác dựa vào nó. Giá trị dưới chép từ Ticket-02 mục 1–2 và 4.1; khóa đặt tên theo bảng 4.1 của đề. Chỗ tên khóa do nhóm đặt (đề không ghi) đánh dấu ✱.

## 1. Gốc manifest
- `"contract_version": "1.1"` · giữ `team`, `team_size: 4`, `headless_cmd`.
- `"extensions": []` (không làm mở rộng).

## 2. `tuning.gather` — đổi / thêm so với v1.0

Giữ nguyên: `duration_s 180`, `bounds`, `dock_pos [2,0]`, `dock_radius 3`, `start_pos`, `start_heading_deg 0`, `swim_speed 4.0`, `ramp_max_ticks 6`, `surface_depth 0.5`, `oxygen_max_s 30`, `oxygen_refill_per_tick 6`, `choke_interval_ticks 60`, `hp_max 3`, `hold_capacity 12`, `interact_radius 2.0`, `node_yield 1`, `regrow_s 20`, `catch_radius 2.0`, `catch_cooldown_s 0.5`.

```json
"fish_yield": {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
"nodes": [
  {"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]},
  {"id": "N2", "kind": "bong_dien_dien", "pos": [28, 0]},
  {"id": "N3", "kind": "bong_sung", "pos": [44, 0]},
  {"id": "N4", "kind": "bong_sung", "pos": [60, 0]},
  {"id": "N5", "kind": "keo_neo", "pos": [76, 0]},
  {"id": "N6", "kind": "keo_neo", "pos": [90, 0]}
],
"fish_initial": 8,
"fish_speed": 1.5,
"fish_turn_ticks": 120,
"fish_max": 12,
"fish_spawn_ticks": 360,
"fish_spawn_clearance": 1.0,
"fish_x": [4, 96],
"fish_depths": {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]},
"fish_spawn_x": [15, 30, 45, 60, 75, 90],
"fish_spawn_depths": {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]},
"fish_weights": {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3},
"monsters": {
  "species": {
    "ca_sau": {"patrol_speed": 1.0, "chase_speed": 3.0, "detect_radius": 10, "exit_radius": 16,
               "depths": [10, 30], "hit_radius": 1.5, "recoil_ticks": 60, "recoil_dist": 2.0}
  },
  "spawns": [
    {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1},
    {"id": "M2", "kind": "ca_sau", "pos": [85, 18], "waypoints": [[85, 18], [89, 18]], "from_day": 3}
  ],
  "invuln_ticks": 90,
  "loss_ratio": 0.5
}
```

Kiểm nhanh: 6 x × 6 độ sâu sinh (5,10 · 10,16 · 24,27) = 36 cặp loài–vị trí; độ sâu khác nhau là {5,10,16,24,27} ⇒ 30 vị trí hình học (khớp đề). `recoil_dist` là **tổng** quãng lùi (60 bước × 2/60 m = 2 m) **[clarify #14]**.

## 3. `tuning.quan` — đổi
```json
"stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}],
"tables": [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]},
           {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [13, 6]}],
"customer_interval_s": 15,
"burn_s": null
```
Giữ nguyên các khóa còn lại (`first_customer_tick 120`, `patience_s 60`, `eat_s 10`, boa, uy tín 3.0 kẹp [0,5], `carry_limit 1`).

## 4. `tuning.menu` — thêm 3 món
```json
"canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
"ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
"lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200}
```

## 5. `tuning.day_plan` ✱ (vị trí trong `tuning`)
```json
"day_plan": [
  {"day": 1, "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
   "ingredients": {"ca_loc": 3, "bong_sung": 6}},
  {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
   "ingredients": {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}},
  {"day": 3, "dishes": {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
   "ingredients": {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}},
  {"day": 4, "dishes": {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
   "ingredients": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}},
  {"day": 5, "dishes": {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
   "ingredients": {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}}
]
```
`contract.py` phải kiểm `ingredients == Σ recipe × suất` cho mọi Ngày (đã tính tay khớp bảng đề).

## 6. `tuning.shop`
```json
"shop": {
  "max_ticks": 600,
  "upgrades": {
    "oxygen": [{"level": 1, "price": 200, "oxygen_max_s": 45}, {"level": 2, "price": 400, "oxygen_max_s": 60}],
    "hp":     [{"level": 1, "price": 250, "hp_max": 4},         {"level": 2, "price": 500, "hp_max": 5}]
  }
}
```

## 7. Code khung đi kèm (cùng commit)
- `chonoi/inventory.py`: `KINDS` = 6 loại (`ca_loc, ca_linh, ca_keo, bong_dien_dien, bong_sung, keo_neo`).
- `chonoi/scenario.py`: `NODE_KINDS` thêm `keo_neo`, `FISH_KINDS` thêm `ca_keo`.
- `chonoi/contract.py`: kiểm `kinds` nút = 3 loại; `fish_initial` là số nguyên; kiểm `day_plan`, `shop` như trên.
- Chạy toàn bộ unittest; test v1.0 vỡ vì số mới ⇒ sửa và ghi lý do.
