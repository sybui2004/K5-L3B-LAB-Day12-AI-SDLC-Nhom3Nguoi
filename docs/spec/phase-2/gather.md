# Spec lát 1 + 2 — `sim/gather` v1.1 (TV1)

> Nguồn: Ticket-02 mục 1.1, 1.2, 4.3 (scenario gather), 4.4, 4.5. Số liệu đọc từ `self.t` ([contract-v1.1.md](contract-v1.1.md)), không hard-code.
> File: `chonoi/sim/gather.py`; Cá Sấu tách sang `chonoi/sim/monsters.py` (gather gọi vào) để diff gọn.

## 0. Thứ tự một bước gather (AC-P2-09)

1. Đồng hồ (`time_left_ticks -= 1`), hồi bắt cá, giảm `invuln_ticks`, hồi nút hái.
2. Bơi người chơi → oxy → ngạt (`choke`). Máu = 0 ⇒ `faint` + `gather_end(fainted)`, **dừng bước**.
3. Cập nhật quái theo id (mục B) → xét **tối đa một** hit (`monster_hit`). Máu = 0 ⇒ `faint{cause:"monster"}` + `gather_end(fainted)`, dừng bước.
4. Tương tác: **bến trước hái** (`gather_end(docked)` nếu trong bán kính bến).
5. Bắt cá theo **vị trí cá trước khi bơi** ở bước này.
6. Xét hết giờ ⇒ `gather_end(time)`.
7. Nếu còn giờ: cá bơi → sinh cá theo lịch.

Cùng tick: ngạt có thể đi trước hit rồi mới xét hết giờ. Cập bến vẫn thắng bắt cá và hết giờ khi còn Máu.

## A. Lát 1 — số chuẩn, cá bơi, sinh cá

### A1. Giỏ (đổi so với v1.0)
- Giỏ là **danh sách có thứ tự nhặt** (cần cho rơi LIFO ở mục B). `inventory_items()` vẫn trả map đếm.
- Cá kèo cho 2 ô; cần đủ chỗ cho **cả đàn** (giữ luật v1.0: thiếu chỗ ⇒ `hold_full`, không bắt).

### A2. Cá bơi (AC-P2-03)
- Mỗi đàn: `id, kind, pos [x,d], heading_deg, age_ticks`. `age_ticks` = số bước đã bơi.
- Tốc độ `fish_speed / tick_hz` m mỗi bước. x giới hạn `fish_x` [4,96]; d giới hạn `fish_depths[kind]`.
- Ở bước bơi thứ `fish_turn_ticks·k` (120, 240…, theo `age_ticks + 1`) đổi hướng theo seed (`Streams.get("fish")`) **trước** khi di chuyển. Phân phối hướng: góc đều [0°, 360°) **[clarify #16]**.
- Chạm mép: phần quãng đường còn lại phản xạ lại, đảo thành phần hướng vuông góc với mép đó; chạm góc đảo cả hai.

### A3. Sinh cá (AC-P2-04)
- Điểm sinh = mọi cặp (loài, x ∈ `fish_spawn_x`, d ∈ `fish_spawn_depths[loài]`) — 36 cặp.
- **Đầu ca:** `fish_initial` = 8 đàn ở 8 điểm hình học khác nhau, mỗi đàn chọn bằng đúng thủ tục sinh dưới đây **[clarify #15]**.
- **Theo lịch:** tại `phase_tick = fish_spawn_ticks·k` (k ≥ 1), **sau khi cá bơi**, nếu số đàn sống < `fish_max` (12):
  1. Điểm hợp lệ = điểm cách **mọi** đàn đang sống > `fish_spawn_clearance` (1 m).
  2. Không còn điểm ⇒ bỏ lượt, không phát event.
  3. Chọn loài theo `fish_weights`, chuẩn hóa lại trên các loài còn điểm hợp lệ.
  4. Chọn đều một điểm hợp lệ của loài; hướng ban đầu theo seed; `age_ticks = 0`.
  5. Phát `fish_spawned {id, kind, pos}`; cá mới bơi **từ bước sau**.
- Id cá cấp qua `IdAllocator` (tiền tố `F`).

### A4. Scenario gather (phần TV1)
- `gather.fish[]` nhận thêm `age_ticks` (mặc định 0).
- `random_fish: false` ⇒ tắt cá mặc định, tắt bơi và sinh; cá fixture đứng yên. Có `fish` khi cờ bật ⇒ thay đàn đầu ca, vẫn bơi/sinh.
- `gather.player.invuln_ticks` (mặc định 0).

## B. Lát 2 — Cá Sấu Năm Chèo, Máu, ngất

### B1. Bố trí (AC-P2-06)
- Lấy `monsters.spawns` có `from_day ≤ day` (gather độc lập: Ngày 1 ⇒ chỉ M1). Vị trí đầu = `pos` = waypoint 0; `target_idx = 1`, `state = "patrol"`.
- `gather.monsters[]` trong scenario **thay** danh sách mặc định: `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}`. `recoil`/`stunned` cần timer dương.
- `hp_max` lấy từ `ctx` (cấp hp) hoặc tuning; Máu đầy đầu mỗi Ngày.

### B2. Di chuyển mỗi bước (cập nhật theo id)
| Trạng thái | Hành vi | Chuyển |
|---|---|---|
| `patrol` | đi `patrol_speed` (1.0 m/s) tới waypoint đích; tới nơi ⇒ đổi đích cho **bước sau** | người chơi d ≥ 10 và cách ≤ `detect_radius` (10) ⇒ `chase` |
| `chase` | bơi về phía người chơi `chase_speed` (3.0 m/s) | cách > `exit_radius` (16) hoặc người chơi d < 10 ⇒ `patrol` |
| `recoil` | lùi theo `recoil_dir` `recoil_dist/recoil_ticks` m/bước (2/60), không gây hit | hết `state_ticks_left` ⇒ `patrol`, xét phát hiện/chạm từ bước kế |

- Sau mỗi lần di chuyển, chặn trong biên map và `depths` của loài ([10,30]).
- Ngưỡng "d ≥ 10" = `depths[0]` của loài **[clarify #17]**.

### B3. Chạm (AC-P2-07)
Sau khi người chơi **và** quái đã di chuyển:
- Ứng viên: quái không ở `recoil`, cách người chơi ≤ `hit_radius` (1.5); người chơi d ≥ 10; `invuln_ticks == 0`.
- Chọn con gần nhất, hòa theo id. **Tối đa một hit mỗi bước.**
- Hiệu ứng: Máu −1; bỏ `floor(số đang mang × loss_ratio)` món theo **LIFO** (nhặt sau mất trước); `invuln_ticks = 90`.
- Con gây hit vào `recoil` 60 bước **tính từ bước sau**; `recoil_dir` = vector đơn vị từ người chơi tới quái lúc chạm (trùng tâm ⇒ `[1,0]`).
- Trong bất tử: không hit, không chuyển quái sang recoil do chạm.
- Phát `monster_hit {monster_id, hp, lost:[kind…], pos}`.

### B4. Ngất (AC-P2-08)
- Ngạt **xuyên bất tử** và **không** làm rơi hàng (giữ luật v1.0).
- Máu = 0 (do ngạt hoặc chạm) ⇒ `faint {pos, lost, hp:0}` (+ `cause:"monster"` nếu do chạm; `lost` = phần giỏ còn lại) rồi `gather_end(fainted)` ngay; giỏ rỗng.
- Trong `day`: quán vẫn mở với kho rỗng.

### B5. Snapshot gather thêm
`monsters[]` (sắp theo id: `id, kind, pos, state, target_idx, state_ticks_left, recoil_dir`), `player.invuln_ticks`, `fish[].age_ticks`. Số làm tròn 3 chữ số.

## C. Test hộp đen (`tests/test_p2_gather.py`)
Dùng scenario `random_fish:false` + `monsters[]` cố định để kiểm từng luật một:
- AC-P2-02: N5/N6 hái ra `keo_neo`; cá kèo cho 2.
- AC-P2-03: 1 đàn bơi 120 bước ⇒ quãng = 120×1.5/60 = 3 m; phản xạ ở x = 96.
- AC-P2-04: seed 1 có 8 đàn ở tick 0, các vị trí khác nhau; `fish_spawned` chỉ ở `phase_tick` chia hết 360; không quá 12.
- AC-P2-05: cá cạnh người chơi, bước đó cá bơi ra xa ⇒ vẫn bắt được.
- AC-P2-06: người chơi d = 5 cách 3 m ⇒ quái vẫn patrol; d = 15 ⇒ chase.
- AC-P2-07: giỏ 5 món ⇒ mất 2 món cuối; 90 tick sau mới hit lại được.
- AC-P2-08: Máu 1 + chạm ⇒ `faint{cause:"monster"}` rồi `gather_end(fainted)` cùng tick, kho `{}`.
- Tất định: headless gather seed 1 chạy 2 lần, `cmp` giống nhau.
