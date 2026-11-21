# Plan Phase 2 — TV2 (lit1numyt, Khoa): lát 3 + Shop + PO

Spec: [quan-shop](../../spec/phase-2/quan-shop.md) · [chung](../../spec/phase-2/README.md)
Nhánh: `feature/p2-quan-shop`

## Bước 0 — PO (phút 0–5)
- [ ] Dẫn nhóm đọc mục 3 spec chung (giao diện `ctx`, ba loại tick) và chốt.
- [ ] Mở clarify #13–19 trong `docs/clarify.md`; hỏi trợ giảng Anh Năm trên lab board những mục còn treo, ghi câu trả lời.

## Bước 1 — Lát 3 (phút 8–25), sau khi lát 0 lên `main`
- [ ] Rebase lên `main` (đã có quan lát 4 của P1 + contract v1.1).
- [ ] Bỏ mọi giả định 1 bếp / 1 bàn; tương tác gần nhất, hòa bếp trước bàn rồi id.
- [ ] Đơn lưu `order_tick`; bếp lấy đơn reserved cũ nhất.
- [ ] Lịch khách theo `phase_tick`, ghế trống id nhỏ nhất.
- [ ] Đóng ca: khách ăn trả ngay, khách chờ rời không trừ uy tín, dọn món/giữ chỗ.
- [ ] `ctx`: `plan_dishes` lọc menu trước nguyên liệu; `money/earned/reputation` mang sang; `stats()`.
- [ ] `chonoi/sim/plan.py`: `plan_ingredients()`; nối vào `contract.py`.
- [ ] Test AC-P2-10…15 trong `tests/test_p2_quan_shop.py`; regression quan P1 với số mới (ghi lý do nếu đổi test).
- [ ] Phút 20: tham gia smoke tích hợp (phần quan).

## Bước 2 — Shop (phút 25–35)
- [ ] `chonoi/sim/shop.py` theo mục C spec: `buy` trước `shop_done`, `bought`/`buy_failed`/`shop_end`, timer 600.
- [ ] Snapshot Shop (`stock`, `time_left_ticks`, `upgrades`).
- [ ] Test AC-P2-16, 17. Báo TV3 để thay ShopSim giả.

## Bước cuối (phút 35–50)
- [ ] Chốt `docs/clarify.md` (ai quyết, trả lời).
- [ ] Ghi `docs/ai-usage-log.md` phần của mình; góp ý retro.

## Dự phòng
Xong sớm ⇒ viết test hộp đen lát 2 (Cá Sấu) giúp TV1, hoặc nhận HUD quán giúp TV3.
