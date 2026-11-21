# Spec `client/ui` — Cửa sổ chơi trên trình duyệt

**Chủ:** Thành viên 3 · **File:** `chonoi/web/index.html` (+ `chonoi/live.py` chỉ khi thật cần, báo cả nhóm vì là file khung) · **Plan:** [../../plan/phase-1/ui-qa.md](../../plan/phase-1/ui-qa.md)
**Chạy:** `python3 -m chonoi.live --mode gather|quan [--seed N] [--inventory-out kho.json | --inventory kho.json]` → mở địa chỉ in ra. Phím: WASD/mũi tên, **E** = `interact`, **Space** = `catch`, **R** = chơi lại.

## Nguyên tắc
- UI chạy **cùng lớp sim** với headless; UI chỉ đọc snapshot (`GET` state) và gửi input (`POST`), không chứa luật.
- Trường chưa có trong snapshot thì bỏ qua, không lỗi (sim viết tới đâu hiện tới đó).
- Phần sáng tạo (âm thanh, hiệu ứng, sprite) phải tắt được và **không** ảnh hưởng headless.

## HUD cần có trong Phase 1

### Gather (đọc từ snapshot)
| Thành phần | Trường snapshot |
|---|---|
| Thanh oxy | `player.oxygen_ticks / player.oxygen_max_ticks` |
| Máu | `player.hp / player.hp_max` |
| Cảnh báo ngạt | `player.zero_oxy_ticks > 0` (nhấp nháy) |
| Giỏ | `hold` (thứ tự nhặt), `hold_count / hold_capacity` |
| Nút hái | `nodes[].pos, kind, ready, regrow_ticks` (mờ khi chưa ready) |
| Đàn cá | `fish[].pos, kind` |
| Hồi chiêu bắt cá | `player.catch_cd_ticks` |
| Đồng hồ | `time_left_ticks` (đổi ra mm:ss) |

### Quan
| Thành phần | Trường snapshot |
|---|---|
| Kho | `stock` |
| Tay cầm | `hand` |
| Bếp | `stoves[].state, dish, cook_ticks_left` (thanh tiến độ nấu) |
| Bàn + khách | `tables[].customer_id`, `customers[].dish_id, state, patience_ticks_left` (thanh kiên nhẫn) |
| Tiền / uy tín / điểm | `money`, `earned`, `reputation`, `score` |
| Đồng hồ | `time_left_ticks` |

### Sự kiện → phản hồi (toast ngắn)
`gather`, `fish_caught`, `hold_full`, `choke`, `faint`, `gather_end`, `cook_started`, `dish_ready`, `served`, `paid`, `customer_left`, `no_dish`, `quan_end`. Nếu `live.py` chưa trả event cho trang thì suy ra từ thay đổi snapshot (vd `hold_count` tăng) — không sửa khung chỉ vì toast.

## AC
| AC | Nội dung |
|---|---|
| AC-UI-01 | Chơi gather từ bến → hái → lặn bắt cá → về bến; HUD oxy/Máu/giỏ đổi đúng |
| AC-UI-02 | Chơi quan với `--inventory kho.json` từ lượt gather; thấy khách, bếp, tiền, uy tín |
| AC-UI-03 | `test_live.py` vẫn xanh |
| AC-UI-04 | Ảnh chụp/GIF hai chế độ lưu ở `docs/proof/phase-1/` |
