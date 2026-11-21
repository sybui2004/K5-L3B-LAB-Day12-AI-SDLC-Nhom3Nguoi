# Spec lát A + D — Adapter kho v1.2, HUD độ tươi, QA (TV3)

> Nguồn: Ticket-03 mục 1 (schema kho, file, scenario, contract v1.2), mục 3 (quy trình, CHANGELOG, bằng chứng). Quyết định: [ADR 0001](../../adr/0001-kho-ca-the-v1.2.md).
> Lát A là **nền**: đẩy `main` trước **phút 10** để TV1, TV2 code theo.

## A. Adapter (`chonoi/inventory.py` + khung liên quan)

### A1. Hàm
Đúng bảng [README.md](README.md) mục 4.2. `Fraction` cho `fresh`; `item_out` làm tròn 3 chữ số.

### A2. File kho
| Phiên bản | Đọc | Ghi |
|---|---|---|
| `1.1` | map đếm (như hiện tại) | map đếm |
| `1.2` | đúng khóa gốc `items`, mảng `{id,kind,fresh}`; id chuỗi khác rỗng, duy nhất; kind thuộc 6 loại; fresh số hữu hạn trong [0,100]; map đếm hoặc sai ⇒ **mã 2** | `{"items":[…]}` sắp theo id, `fresh` là `float(Fraction)` đầy đủ; rỗng `{"items":[]}` |

- Ghi **đúng một lần** khi có `gather_end` (runner), qua file tạm cùng thư mục rồi `os.replace` (giữ cơ chế hiện có). Ngất ⇒ `{"items":[]}`. Hết `--ticks` trước `gather_end` ⇒ không đụng file đích.
- `headless.py`, `live.py`: `read_inventory(path, contract_version)`.

### A3. `game.contract.json` + `contract.py`
- Thêm `tuning.freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}` ngay (không ảnh hưởng v1.1).
- `contract.py` kiểm khối `freshness` (số dương, `0 < spoiled_below < initial ≤ 100`).
- Đổi `contract_version` sang `"1.2"` **chỉ ở bước tích hợp cuối** (phút 25) — xem ADR mục 4.

### A4. Scenario (`chonoi/scenario.py`, phần schema)
- `gather.hold`, `quan.stock`: mảng cá thể (dùng `validate_item_list`); `hold` không vượt `hold_capacity`.
- `customers[].reserved`: mảng id chuỗi (kiểm trên kho thực do TV2 làm trong `quan.py`).
- Id duy nhất giữa mọi nơi chứa trong cùng scenario ⇒ trùng ⇒ mã 2.
- Đăng ký mọi id có sẵn vào `IdAllocator` (`reserve`) để id mới nối tiếp.

### A5. Test migration (`tests/test_p3_inventory.py`)
- Đọc/ghi vòng tròn: ghi rồi đọc lại giữ nguyên id, kind, fresh (kể cả 29.999 và 30).
- v1.2 từ chối: map đếm, thiếu `items`, khóa gốc thừa, kind lạ, id trùng, id rỗng, fresh −1 / 100.5 / `NaN` ⇒ mã 2 qua headless.
- Hết `--ticks` trước `gather_end` ⇒ file đích không tồn tại / giữ nguyên.
- Đổi `test_python_starter_units.py`, `test_smoke_p1.py` phần kho (ghi lý do).

## B. HUD độ tươi (`chonoi/web/index.html`) (AC-P3-15)
- Giỏ (sáng): mỗi ô có thanh độ tươi nhỏ; hàng ươn tô xám + biểu tượng/nhãn "ươn".
- Kho quán: theo loại hiển thị `khả dụng / ươn`, và độ tươi thấp nhất của loại; khách có món: giá dự kiến khi đã nấu (`base_price`).
- Toast `spoiled`: "<tên nguyên liệu> đã ươn!".
- Chữ ≥ 18 px ở 1280×720 như Phase 2. Ảnh chụp lưu `docs/proof/phase-3/`.

## C. QA và bằng chứng (phút 20 và 25–32)
- **Smoke bàn giao (phút 20, AC-P3-04)**, theo đúng đề:
  ```bash
  # smoke-scenario.json: {"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}
  # smoke-inputs.json: interact:true ở frame 0
  python -m chonoi.headless --mode gather --seed 1 --ticks 600 --scenario docs/proof/phase-3/smoke-scenario.json --inputs docs/proof/phase-3/smoke-inputs.json --out docs/proof/phase-3/handoff-gather.jsonl --inventory-out docs/proof/phase-3/kho.json
  python -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/kho.json --out docs/proof/phase-3/handoff-quan.jsonl
  ```
  Kỳ vọng: `kho.json` có I1 `fresh = 100 − 1/120 ≈ 99.99167`; snapshot quán tick 0 có đúng id/kind/fresh đó. Ghi kết quả vào `docs/proof/phase-3/handoff.md`.
- Smoke `day --days 2` (id xuyên Ngày, bàn giao cùng tick) → `docs/proof/phase-3/day-2.jsonl`.
- Regression toàn bộ unittest trên commit bàn giao → `docs/proof/phase-3/unittest.txt`.
- Chốt `CHANGELOG.md` từ bản nháp ở [README.md](README.md) mục 5.
- Điền `docs/verification/phase-3.md`; cập nhật `docs/ai-usage-log.md`, `AGENTS.md` nếu lệnh đổi.
