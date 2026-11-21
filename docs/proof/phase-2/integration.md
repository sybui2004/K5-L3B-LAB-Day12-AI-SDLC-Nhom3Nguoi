# Smoke tích hợp Phase 2: gather `--inventory-out` → quan `--inventory`

> Chạy lại trên `main` @ `26ab801` bởi TV1 (kết quả ngày 2026-11-21). Bản cũ của TV2 (`integration.txt`) chạy trên `0302397` (trước contract v1.1 đầy đủ); file này thay thế cho việc truy vết commit tag.
> Fixture: [smoke-scenario.json](smoke-scenario.json) (giỏ 6 món gồm cá kèo và kèo nèo, `random_fish:false`) · [smoke-inputs.json](smoke-inputs.json) (`interact` tick 0, đang ở bến nên cập bến ngay).

## Lệnh
```bash
python -m chonoi.headless --mode gather --seed 1 --ticks 10800 --scenario docs/proof/phase-2/smoke-scenario.json --inputs docs/proof/phase-2/smoke-inputs.json --out g.jsonl --inventory-out kho.json
python -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory kho.json --out q.jsonl
```
Cả hai thoát mã 0.

## Kết quả ([integration-result.txt](integration-result.txt))
```
gather_end: {"reason": "docked", "inventory": {"items": {"bong_sung": 2, "ca_keo": 2, "ca_loc": 1, "keo_neo": 1}}}
kho.json  : {"bong_sung": 2, "ca_keo": 2, "ca_loc": 1, "keo_neo": 1}
quan tick0 stock: {"bong_sung": 2, "ca_keo": 2, "ca_loc": 1, "keo_neo": 1}
KHỚP
```
- `stock` ở snapshot tick 0 của quan khớp từng loại với `kho.json`, gồm `keo_neo` và `ca_keo` mới của v1.1 (6 loại nguyên liệu).
- Cá kèo 2 + cá lọc 1 + bông súng 2 + kèo nèo 1: đúng giỏ trong fixture, không mất, không thêm.
- Kho rỗng và kho bị bỏ khi ngất: được test ở `tests/test_gather_rules.py` (`faint_empties_hold_and_writes_empty_inventory`) và `test_smoke_p1.py` (`test_inv_01_*`).

## Phạm vi và hạn chế
- Đây là smoke **headless**, chưa bao gồm giao diện (`live.py` chưa có mode `day`).
- Kho hiện là kho **đếm** (`{"items": {kind: n}}`), đúng v1.1. Phase 3 (v1.2) đổi sang cá thể có độ tươi, khi đó smoke này phải chạy lại.
