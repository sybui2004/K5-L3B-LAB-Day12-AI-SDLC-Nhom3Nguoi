# Smoke bàn giao kho v1.2 (AC-P3-04, AC-P3-13)

## Qua file
```bash
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --scenario docs/proof/phase-3/smoke-scenario.json --inputs docs/proof/phase-3/smoke-inputs.json --out handoff-gather.jsonl --inventory-out docs/proof/phase-3/kho.json
python -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/kho.json --out handoff-quan.jsonl
```

- `kho.json`: `[{"id": "I1", "kind": "ca_linh", "fresh": 99.99166666666666}]`
- Kỳ vọng `fresh = 100 − 1/120 ≈ 99.99167`.
- Snapshot quán tick 0: `[{"id": "I1", "kind": "ca_linh", "fresh": 99.992}]`
- Kết quả: **đạt**. File JSONL lưu đuôi `.jsonl.txt` vì `.gitignore` chặn `*.jsonl`.

## Mode day, 2 Ngày
- Id bàn giao Ngày 1: `['I1', 'I2', 'I3']`. Ngày 2: `['I4', 'I5', 'I6']`.
- Dòng end: `reason = days_complete`, `days_completed = 2`.
- Hai lần chạy cùng seed giống từng byte: **có**. Một lần chạy mất 0.78 giây.
- Kết quả: **đạt**. Sự kiện chính ở `day-2-events.jsonl.txt`.
