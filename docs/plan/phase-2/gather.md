# Plan Phase 2 — TV1 (sybui2004): lát 0, 1, 2 + Integrator

Spec: [lát 0](../../spec/phase-2/contract-v1.1.md) · [gather](../../spec/phase-2/gather.md) · [chung](../../spec/phase-2/README.md)
Nhánh: `feature/p2-gather` (lát 0 đẩy thẳng `main` sau khi test xanh).

## Bước 0 — Nền (phút 0–8)
- [ ] Commit + gộp `feature/gather-quan-kitchen` vào `main` (gather rules + quan lát 4 + test). Chạy unittest.
- [ ] Gắn tag `phase-1` lên commit đó, đẩy; ghi "gắn trễ lúc …" trong `docs/verification/phase-1.md`.
- [ ] Lát 0: sửa `game.contract.json` theo [contract-v1.1.md](../../spec/phase-2/contract-v1.1.md); `inventory.py` 6 loại; `scenario.py` `NODE_KINDS`/`FISH_KINDS`; `contract.py` kiểm khóa mới. Chạy unittest, sửa test vỡ vì số (ghi lý do). Đẩy `main`, báo nhóm.

## Bước 1 — Lát 1 (phút 8–20)
- [ ] Giỏ thành danh sách có thứ tự nhặt; `inventory_items()` vẫn trả map.
- [ ] Cá bơi (A2), sinh đầu ca 8 đàn + sinh theo lịch (A3), `fish_spawned`.
- [ ] Bắt cá theo vị trí trước khi bơi; sắp lại thứ tự bước theo mục 0.
- [ ] Scenario: `age_ticks`, `random_fish`, `player.invuln_ticks`.
- [ ] Test `tests/test_p2_gather.py` phần AC-P2-02…05.
- [ ] Phút 20: chạy smoke tích hợp cùng TV3 (lệnh trong [day-ui-qa.md](day-ui-qa.md)).

## Bước 2 — Lát 2 (phút 20–35)
- [ ] `chonoi/sim/monsters.py`: patrol/chase/recoil, chặn biên + dải độ sâu; lọc `from_day` theo `ctx["day"]`.
- [ ] Hit tối đa 1/bước, rơi LIFO, bất tử 90, `monster_hit`; ngất `cause:"monster"`.
- [ ] `hp_max`/`oxygen_max_s` lấy từ `ctx` nếu có.
- [ ] Scenario `gather.monsters[]`; snapshot `monsters[]`, `player.invuln_ticks`.
- [ ] Test AC-P2-06…09. Headless gather seed 1 chạy 2 lần, `cmp`.

## Bước cuối — Integrator (phút 35–55)
- [ ] Gộp theo thứ tự ở [phase-2.md](../phase-2.md); unittest xanh sau mỗi lần gộp.
- [ ] Cùng TV3 kiểm `docs/verification/phase-2.md` khớp commit bàn giao.
- [ ] `git tag phase-2 <commit>` trên `main` và `git push origin phase-2` **trước 1:55**.

## Dự phòng
Vướng lát 2 quá 10 phút ⇒ báo kênh; TV2 (nếu xong Shop) viết test hộp đen lát 2 để TV1 chỉ lo luật.
