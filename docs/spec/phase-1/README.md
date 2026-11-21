# Spec Phase 1 (PRD-0) — phần chung cho cả nhóm

> Nguồn: lab board tab **Phase 1 — PRD-0** (lặn hái nguyên liệu, mở quán buổi tối, file kho, Test Contract v1.0, cách làm nhóm), `game.contract.json`, các `TODO(nhóm)` trong `chonoi/sim/*`, `chonoi/scenario.py`, smoke test `tests/test_smoke_p1.py`.
> Chỗ nào ghi **[đối chiếu PRD-0]** là spec này suy ra từ khung code, chưa trích được nguyên văn PRD: PO đối chiếu với tab Phase 1 trên lab board rồi sửa spec hoặc ghi vào [`docs/clarify.md`](../../clarify.md).

## Spec theo module

| Module | Spec | Plan | Chủ |
|---|---|---|---|
| `sim/gather` | [gather.md](gather.md) | [plan/phase-1/gather.md](../../plan/phase-1/gather.md) | Thành viên 1 |
| `sim/quan` lát 3 (khách) + `scenario` quan | [quan.md](quan.md) mục A | [plan/phase-1/quan-customers.md](../../plan/phase-1/quan-customers.md) | Thành viên 2 |
| `sim/quan` lát 4 (bếp, phục vụ, tiền) | [quan.md](quan.md) mục B | [plan/phase-1/quan-kitchen.md](../../plan/phase-1/quan-kitchen.md) | Thành viên 1 |
| `client/ui` + `qa` + harness | [client-ui.md](client-ui.md), [qa-harness.md](qa-harness.md) | [plan/phase-1/ui-qa.md](../../plan/phase-1/ui-qa.md) | Thành viên 3 |

Kế hoạch tổng (mốc giờ, phụ thuộc, rủi ro): [`docs/plan/phase-1.md`](../../plan/phase-1.md).

## 1. Định nghĩa xong (Definition of Done) của Phase 1

1. `PYTHONPATH=tests:. python -m unittest discover -s tests -v` xanh trên nhánh chính.
2. `python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl` và `--mode quan` chạy, mã thoát 0; cùng seed chạy 2 lần cho file giống từng byte.
3. Luồng `gather --inventory-out kho.json` → `quan --inventory kho.json` chạy thông.
4. `TEAM.md`, `docs/plan/phase-1.md`, `docs/verification/phase-1.md`, `docs/clarify.md`, `docs/ai-usage-log.md` đã điền; mỗi người ≥ 1 commit có nội dung trong phase này.
5. Tag `phase-1` gắn trước mốc **1:00**; chỗ chưa xong ghi trung thực trong `docs/verification/phase-1.md`.

## 2. Test Contract v1.0 (khung đã lo, KHÔNG được làm vỡ)

- CLI: `python -m chonoi.headless --mode gather|quan --seed N --ticks N --out f.jsonl [--inputs i.json] [--scenario s.json] [--inventory kho.json | --inventory-out kho.json]`.
- Mã thoát: 0 chạy xong; 2 đầu vào sai (inputs/scenario/kho sai schema, mâu thuẫn); 1 lỗi khác.
- JSONL theo thứ tự: snapshot tick 0 → mỗi bước: các `event` (theo thứ tự xử lý) rồi snapshot (nếu tới lượt hoặc buổi kết thúc) → dòng `end`. Số làm tròn 3 chữ số, id sắp bằng `ids.sort_by_id`.
- Dòng event: `{"type":"event","tick":k+1,"phase":...,"name":...,"data":{...}}` — luật chỉ trả `(name, data)` từ `step()`.
- Snapshot chung (runner thêm): `tick, mode, phase, state, time_left_ticks, money, earned, reputation, score`; `score = earned + reputation_multiplier * floor(reputation)`.
- Tất định: mọi ngẫu nhiên qua `self.rng` (`Streams`), không `random` toàn cục, không đồng hồ hệ thống; duyệt danh sách luôn qua `sort_by_id`.
- Inputs: `move` chuẩn hóa sẵn; nút `interact`, `catch` tính **cạnh lên** (`inp.pressed(...)`).

## 3. Hợp đồng tích hợp (đề xuất — Integrator chép vào `docs/contracts/` sau khi cả nhóm gật)

### 3.1 File kho (Contract G)
`{"items": {"<kind>": int >= 0}}`, kind ∈ `ca_loc, ca_linh, bong_dien_dien, bong_sung`. Ghi **một lần** khi có `gather_end` (runner lo), bỏ mục 0, ghi nguyên tử. `quan` nhận kho qua `--inventory` **hoặc** `scenario.quan.stock`, không cả hai (mã 2). Mẫu: [`docs/contracts/inventory.sample.json`](../../contracts/inventory.sample.json).

### 3.2 Danh sách sự kiện

| Mode | Sự kiện | `data` | Ai phát |
|---|---|---|---|
| gather | `dive` / `surface` | `{pos}` | gather (TV1) |
| gather | `oxygen_empty` | `{pos}` | gather |
| gather | `choke` | `{hp}` | gather |
| gather | `faint` | `{pos, lost:{items}}` | gather |
| gather | `gather` | `{node_id, kind, count}` | gather |
| gather | `node_regrown` | `{node_id}` | gather (khung) |
| gather | `fish_caught` | `{fish_id, kind, count}` | gather |
| gather | `hold_full` | `{source, kind}` | gather |
| gather | `gather_end` | `{reason: docked\|time\|fainted, inventory:{items}}` | gather (khung) |
| quan | `customer_arrived`, `no_dish`, `customer_left` | xem [quan.md](quan.md) mục A **[đối chiếu PRD-0 mục E]** | quan lát 3 (TV2) |
| quan | `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` | xem [quan.md](quan.md) mục B **[đối chiếu PRD-0 mục E]** | quan lát 4 (TV1) |
| quan | `quan_end` | `{reason, money, earned, shift_earned, reputation}` | quan (khung) |

Người nghe sự kiện: `client/ui` (TV3) hiển thị toast/âm thanh; `qa` (TV3) dùng trong test hộp đen.

### 3.3 Giao diện `sim/*` ↔ `client/ui`
- UI **chỉ đọc** `Session.snapshot()` (cùng dict với JSONL) và danh sách event trả về từ `Session.step()`. UI không sửa state sim.
- UI **chỉ gửi** input qua `LiveInputs.set(move=[x, y], interact=bool, catch=bool)`.
- Sim muốn UI hiện thêm gì ⇒ thêm trường vào `snapshot()` và cập nhật bảng ở [client-ui.md](client-ui.md) (báo TV3).

## 4. Quy ước làm việc cho Phase 1

- Nhánh: `feature/<module>-<việc>` (vd `feature/quan-customers`), gộp vào `main` khi test xanh. Tag do Integrator gắn.
- Commit nhỏ, message tiếng Việt, ghi kết quả test trong mô tả hoặc `docs/proof/phase-1/`.
- `chonoi/sim/quan.py` có **2 người cùng sửa** ⇒ chia theo hàm (xem [quan.md](quan.md) mục 0) và TV2 đẩy commit khung `step()` trước.
- Số liệu chỉ đọc từ `self.t` / `self.menu`; không hard-code.
