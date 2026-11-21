# Spec lát B — Lặn có độ tươi (TV1)

> Nguồn: Ticket-03 mục 1 (độ tươi, thứ tự tick gather, JSONL). Dùng hàm adapter ở [README.md](README.md) mục 4.2, không tự dựng dict cá thể.
> **Điều kiện trước:** gather Phase 2 (cá bơi/sinh, Cá Sấu, `monsters.py`) phải gộp `main` trước khi bắt đầu lát này.

## 1. Giỏ
- `self.hold` = list cá thể theo **thứ tự vào giỏ** (cuối list = mới nhất). Sức chứa `hold_capacity` đếm số cá thể, tính cả hàng ươn.
- Hái 1 / bắt đàn n con ⇒ gọi `new_item` n lần theo thứ tự, mỗi con `fresh = 100`, id `I<n>` từ allocator cá thể `item_ids` (tham số mới; chạy độc lập thì tự tạo, trong `day` do `DaySim` truyền vào).
- `inventory_items()` đổi thành trả **list cá thể** sắp theo id (bàn giao); giữ một hàm đếm theo loại riêng cho HUD/kế hoạch (`hold_counts()`).

## 2. Hao tươi (AC-P3-05, 06)
- Ở **đầu bước** (cùng nhóm đồng hồ/cooldown/hồi nút): `decay(self.hold, 1/120, 30)` cho hàng **đã có trước bước này**. Hàng nhặt trong bước chưa hao (bắt đầu hao từ bước sau).
- Mỗi cá thể vừa qua ngưỡng ⇒ `spoiled {item_id, kind, location:"hold"}`, theo id, đúng một lần (đã ươn thì không phát lại).
- Pause: runner không gọi `step` ⇒ tự dừng hao.

Kiểm theo mẫu đề:
```json
{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}
```
chạy 1 bước không input ⇒ `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}`.

## 3. Mất hàng (AC-P3-07)
- Bị chạm: bỏ `floor(len(hold) × loss_ratio)` cá thể từ **cuối** list; `lost` = mảng cá thể theo thứ tự bỏ (mới nhất trước).
- Ngất: bỏ **toàn bộ** phần còn lại theo LIFO; `faint.lost` = mảng đó; rồi `gather_end(fainted)` với `inventory: {"items": []}`.
- Cá thể đã bỏ không quay lại; id của nó không được cấp lại.

## 4. Kết thúc
`gather_end.data.inventory = {"items": [item_out(i) for i in sort_by_id(hold)]}`. Runner ghi file qua adapter (TV3).

## 5. Snapshot
`hold` = mảng `item_out` theo thứ tự vào giỏ; giữ `hold_count`, `hold_capacity`.

## 6. Test (`tests/test_p3_gather.py`)
- Mẫu đề ⇒ `spoiled` ở tick 1; fresh 30.01 ⇒ ươn ở bước thứ 2 (30.01 − 1/120 = 30.00167 ≥ 30, rồi 29.993 < 30).
- Hái ở bước k ⇒ snapshot tick k có fresh 100, tick k+1 có 99.992.
- Hai cá thể cùng qua ngưỡng ⇒ hai `spoiled` theo id.
- Bị chạm với giỏ `[I1..I5]` ⇒ `lost` = `[I5, I4]`.
- Ngất với giỏ 3 món ⇒ `faint.lost` = 3 cá thể LIFO, kho rỗng.
- Bắt cá linh (3 con) ⇒ id liên tiếp, tiếp sau id lớn nhất có trong scenario.
- Đổi `tests/test_gather_rules.py` sang cá thể (ghi lý do trong commit).
