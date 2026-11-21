# Spec Phase 3 (Ticket-03 — Change Request "Mùa Nước Nổi") — phần chung

> Nguồn: lab board tab **Phase 3 — Ticket-03** (35 phút, 1:55–2:30, Test Contract v1.2). Quyết định schema: [ADR 0001](../../adr/0001-kho-ca-the-v1.2.md). Kế hoạch: [`docs/plan/phase-3.md`](../../plan/phase-3.md).
> Chỗ đề chưa rõ ghi **[clarify #n]** ở [`docs/clarify.md`](../../clarify.md). Không làm mục Mở rộng (dòng nước lũ, khách đặt trước): nhóm 4 người không bắt buộc.

## Spec theo lát

| Lát | Nội dung | Spec | Chủ |
|---|---|---|---|
| A | Adapter kho cá thể, file kho v1.2, scenario `hold`/`stock`/`reserved`, contract `freshness`, test migration | [adapter-hud-qa.md](adapter-hud-qa.md) mục A | TV3 (Hưng) |
| B | Lặn: giỏ cá thể, hao 0.5/s, `spoiled`, LIFO theo cá thể | [gather.md](gather.md) | TV1 (sybui2004) |
| C | Quán: kho cá thể, hao 0.25/s, giữ theo id, thử giữ lại, giá theo tươi · Day: bàn giao cùng tick, id xuyên Ngày | [quan-day.md](quan-day.md) | TV2 (Khoa) |
| D | HUD độ tươi/ươn, smoke, CHANGELOG, verification | [adapter-hud-qa.md](adapter-hud-qa.md) mục B, C | TV3 |

## 1. DoD (Ticket-03)
1. Contract v1.2 bàn giao kho cá thể qua file và trong `day`; kho đếm ⇒ mã 2. Id, độ tươi, hàng ươn, giữ chỗ, giá và JSONL đúng luật.
2. HUD cho thấy độ tươi hoặc hàng ươn. Có test qua ngưỡng, thử giữ lại khi hàng vừa ươn, chốt giá, bàn giao.
3. Có bảng tác động (mục 3), quyết định schema (ADR 0001), thứ tự tích hợp giữ `main` chạy được; mỗi người có commit.
4. `CHANGELOG.md` ghi breaking change; regression P1–P2 còn hiệu lực đạt, test đổi có lý do; `docs/verification/phase-3.md` + `docs/proof/phase-3/` khớp commit tag; clarify, nhật ký AI cập nhật.
5. Tag `phase-3` trên `main` trước **2:30**.

## 2. AC-P3

| AC | Nội dung | Chủ |
|---|---|---|
| AC-P3-01 | Manifest `contract_version:"1.2"`, `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}` | TV3 |
| AC-P3-02 | File kho `{"items":[{id,kind,fresh}]}`, rỗng `{"items":[]}`, xuất sắp theo id; v1.2 từ chối kho đếm / sai schema / kind lạ / id trùng hoặc rỗng / fresh ngoài [0,100] ⇒ mã 2 | TV3 |
| AC-P3-03 | `--inventory-out` ghi đúng một lần khi `gather_end`, file tạm + thay nguyên tử; ngất ghi kho rỗng; chạm `--ticks` trước ⇒ không đụng file đích | TV3 |
| AC-P3-04 | Smoke bàn giao: gather `fresh:100` + `interact` frame 0 → `quan --inventory --ticks 0` ⇒ id, kind, fresh khớp chính xác | TV3 + TV1 |
| AC-P3-05 | Hàng mới `fresh=100`, hao từ bước sau; giỏ −0.5/s; id `I1, I2…` theo thứ tự vào giỏ | TV1 |
| AC-P3-06 | `spoiled {item_id, kind, location:"hold"}` đúng một lần khi qua ngưỡng; nhiều cái cùng bước phát theo id; scenario mẫu đề ⇒ event ở `tick:1` | TV1 |
| AC-P3-07 | `lost` trong `monster_hit`/`faint` là mảng cá thể theo thứ tự bỏ LIFO; ngất bỏ hết theo LIFO rồi `faint`, `gather_end(fainted)` | TV1 |
| AC-P3-08 | Kho quán nhận nguyên số lượng, id, độ tươi (kể cả hàng ươn); hao −0.25/s kể cả hàng đang giữ; pause dừng hao; món chín không hao | TV2 |
| AC-P3-09 | `spoiled{location:"stock"}`; hàng ươn chiếm chỗ nhưng không dùng nấu | TV2 |
| AC-P3-10 | Giữ chỗ theo id: mỗi loại lấy cá thể khả dụng tươi nhất, hòa theo id; `customers[].reserved` là mảng id | TV2 |
| AC-P3-11 | Phần giữ có cá thể vừa ươn ⇒ nhả cả đơn, thử giữ lại **đúng một lần** (theo `order_tick` rồi id bàn); thiếu ⇒ `unfulfillable`, khách chờ tới hạn | TV2 |
| AC-P3-12 | Bắt đầu nấu tiêu đúng các id đang giữ; `base_price = floor(giá × TB fresh / 100)`; boa `floor(base_price × 0.2)`; `cook_started.data.items` sắp theo kind rồi id | TV2 |
| AC-P3-13 | Day: bàn giao cùng tick đổi pha, không hao thêm; Shop/hàng chờ không hao; id tăng xuyên pha/Ngày; Ngày kế cấp id mới cho mẫu `gather.hold` | TV2 |
| AC-P3-14 | Scenario v1.2: `hold`/`stock` mảng cá thể, `reserved` mảng id; id duy nhất giữa các nơi chứa; giữ chỗ phải trỏ hàng chưa ươn, đủ công thức, không dùng chung; thiếu `reserved` thì tự cấp; sai ⇒ mã 2 | TV3 (kiểm schema) + TV2 (kiểm trên kho thực) |
| AC-P3-15 | HUD: đọc được độ tươi hoặc nhận ra hàng ươn (số/thanh/nhãn/biểu tượng) ở giỏ và kho quán | TV3 |
| AC-P3-16 | Regression P1–P2 với schema mới; test đổi ghi lý do; `CHANGELOG.md`; verification + proof; tag `phase-3` | Cả nhóm (TV1 gắn tag) |

## 3. Bảng tác động (Ticket-03 yêu cầu ghi)

| Module | File cần đổi | Test giữ / đổi / thêm | Người |
|---|---|---|---|
| Adapter kho + contract | `chonoi/inventory.py`, `chonoi/contract.py`, `game.contract.json`, `chonoi/headless.py`, `chonoi/live.py`, `chonoi/runner.py` (ghi kho) | đổi `tests/test_python_starter_units.py` (inventory), `tests/test_smoke_p1.py` (file kho); thêm `tests/test_p3_inventory.py` | TV3 |
| Scenario | `chonoi/scenario.py`: schema `hold`/`stock`/`reserved` (TV3); kiểm trên kho thực + tự cấp `reserved` trong `quan.py` (TV2) | thêm vào `test_p3_inventory.py` | TV3 + TV2 |
| Lặn | `chonoi/sim/gather.py`, `chonoi/sim/monsters.py` | đổi `tests/test_gather_rules.py` (hold là cá thể, `lost` mảng); thêm `tests/test_p3_gather.py` | TV1 |
| Quán | `chonoi/sim/quan.py` | đổi `tests/test_quan_customers.py`, `test_quan_kitchen.py`, `test_quan_rules.py` (`stock`/`reserved`, giá); thêm `tests/test_p3_quan.py` | TV2 |
| Day / Shop | `chonoi/sim/day.py` | đổi `tests/test_day.py` (kho bàn giao, `stock` Shop); thêm ca id xuyên Ngày vào `test_p3_quan.py` | TV2 |
| HUD | `chonoi/web/index.html` | `tests/test_live.py` giữ nguyên; ảnh chụp làm bằng chứng | TV3 |
| QA / docs | `CHANGELOG.md`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md` | chạy toàn bộ regression | TV3 (+ mọi người ghi phần mình) |

## 4. Schema và quy ước dùng chung (theo ADR 0001)

### 4.1 Cá thể
```json
{"id": "I1", "kind": "ca_linh", "fresh": 100}
```
- `fresh` trong bộ nhớ là `Fraction`; JSONL làm tròn 3 chữ số (dung sai quan sát ±0.01); file kho ghi `float` đầy đủ.
- Ươn khi `fresh < 30` (so giá trị chưa làm tròn). Hàng ươn vẫn chiếm ô giỏ, vẫn nằm trong kho quán, không được giữ chỗ/nấu.

### 4.2 Hàm adapter (`chonoi/inventory.py`) — TV3 đẩy **trước phút 10**, mọi lát dùng
| Hàm | Việc |
|---|---|
| `new_item(item_ids, kind, tuning)` | cấp `I<n>` từ allocator riêng cho cá thể (sống suốt lượt), `fresh = initial` |
| `decay(items, per_tick, spoiled_below) -> [item…]` | trừ, kẹp 0, trả các cá thể **vừa** qua ngưỡng, sắp theo id |
| `is_spoiled(item, spoiled_below)` | `fresh < spoiled_below` |
| `item_out(item)` | dict JSONL (`fresh` làm tròn 3) |
| `read_inventory(path, version)` / `write_inventory(path, items, version)` | v1.1 đếm, v1.2 cá thể; ghi nguyên tử, sắp theo id |
| `validate_item_list(raw, kinds)` | kiểm schema cá thể, trả list cá thể (`Fraction`) |

### 4.3 Sự kiện / payload đổi
| Sự kiện | `data` v1.2 |
|---|---|
| `spoiled` (mới) | `{item_id, kind, location: "hold" \| "stock"}` |
| `monster_hit`, `faint` | `lost` = mảng cá thể theo thứ tự bỏ LIFO |
| `gather_end` | `inventory` = `{"items":[…]}` cá thể, sắp theo id |
| `cook_started` | thêm `items` = mảng cá thể đã tiêu, sắp theo kind rồi id |
| món (bếp/tay/khách) | giữ cấu trúc cũ, `base_price` = giá đã chốt theo fresh |

### 4.4 Thứ tự trong tick (đề mục 1)
- **Gather:** đồng hồ, cooldown, hồi nút **và hao tươi hàng có sẵn** → bơi, oxy, ngạt → quái/hit → bến trước hái → bắt cá → hết giờ → (còn giờ) cá bơi, sinh. Ngất: bỏ hết theo LIFO rồi `faint`, `gather_end(fainted)`.
- **Quán:** đồng hồ, timer → **hao tươi kho thô, phát hết `spoiled` theo id, rồi xử lý giữ chỗ bị ươn** → món chín (theo id bếp) → di chuyển + tối đa một tương tác → thanh toán, kiên nhẫn/đóng ca → (còn giờ) khách mới. Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ; giao đúng tick hết ca được trả ngay.

## 5. Bản nháp CHANGELOG (TV3 chốt ở phút 25–32)
```markdown
## [phase-3] Test Contract v1.2 — BREAKING
- File kho: `{"items":{kind:n}}` → `{"items":[{"id","kind","fresh"}]}`; kho đếm bị từ chối (mã 2).
- Scenario: `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id.
- JSONL: `hold`, `stock`, `reserved`, `lost`, `gather_end.inventory` theo schema mới; thêm event `spoiled`; `cook_started.items`; giá món theo độ tươi.
- Cập nhật fixture: `{"ca_loc":2}` → `[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"ca_loc","fresh":100}]`.
```
