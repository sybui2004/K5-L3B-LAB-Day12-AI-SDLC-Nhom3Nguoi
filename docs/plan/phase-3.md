# Kế hoạch Phase 3 — Ticket-03 "Mùa Nước Nổi" (≤ 1 trang)

- **Mục tiêu:** Test Contract v1.2 — kho cá thể có độ tươi, qua file và trong `day`; HUD độ tươi; CHANGELOG breaking change; tag `phase-3` trên `main` trước **2:30**.
- **Spec:** [`docs/spec/phase-3/`](../spec/phase-3/README.md) · **Quyết định schema:** [ADR 0001](../adr/0001-kho-ca-the-v1.2.md) · **Bảng tác động:** spec README mục 3.
- **Không làm Mở rộng** (dòng nước lũ, khách đặt trước).

## Việc / người / phụ thuộc

| # | Việc | Người | Phụ thuộc | Checklist |
|---|---|---|---|---|
| 0 | Gộp gather Phase 2 còn dở (cá bơi/sinh, Cá Sấu) vào `main`; gắn tag `phase-1`, `phase-2` còn thiếu (ghi trễ trung thực) | TV1 | — | mục TV1 |
| A | Adapter kho cá thể + file v1.2 + schema scenario + `freshness` + test migration | TV3 | — | mục TV3 |
| B | Lặn: giỏ cá thể, hao, `spoiled`, LIFO | TV1 | 0, A | mục TV1 |
| C | Quán + day: hao, giữ theo id, giữ lại, giá theo tươi, bàn giao, id xuyên Ngày | TV2 | A | mục TV2 |
| D | HUD độ tươi | TV3 | A | mục TV3 |
| E | Smoke kho phút 20, bật v1.2, CHANGELOG, verification, tag | TV3 + TV1 | B, C | mục TV3 |

## Mốc giờ

| Phút | Giờ | Việc |
|---|---|---|
| 0–7 | 1:55–2:02 | Đọc bảng tác động + ADR, **gật**; TV1 làm bước 0; PO mở clarify #28–31 |
| 7–10 | 2:02–2:05 | TV3 đẩy adapter (lát A) lên `main`; TV1, TV2 rebase |
| 10–20 | 2:05–2:15 | Song song B, C, D trên schema đã chốt (manifest vẫn 1.1, bộ nhớ dùng cá thể) |
| **20** | **2:15** | **Smoke bàn giao kho** (TV3 + TV1), standup 2–3 phút ghi `docs/standup.md`, ai xong sang lát trễ |
| 20–25 | 2:15–2:20 | Gộp theo thứ tự: B → C → D, test xanh mỗi lần |
| 25–32 | 2:20–2:27 | **Bật `contract_version:"1.2"`**, smoke file + `day --days 2`, regression, CHANGELOG, verification, retro nhanh |
| 32–35 | 2:27–2:30 | Dự phòng; TV1 đẩy `phase-3` **chậm nhất 2:30** |

## Checklist theo người

### TV1 (sybui2004) — bước 0, lát B, Integrator
- [ ] Commit + gộp gather P2 (đang dở trên `feature/gather-fish-monsters`); tag `phase-1`/`phase-2` nếu nhóm thống nhất commit nào.
- [ ] Lát B theo [gather.md](../spec/phase-3/gather.md): hao đầu bước, `spoiled`, LIFO cá thể, `inventory_items()` trả list.
- [ ] `tests/test_p3_gather.py` + đổi `test_gather_rules.py` (ghi lý do).
- [ ] Phút 20 smoke cùng TV3; phút 32 gắn tag.

### TV2 (lit1numyt, Khoa) — lát C, PO
- [ ] Ghi clarify #28–31, hỏi trợ giảng nếu cần.
- [ ] Lát C theo [quan-day.md](../spec/phase-3/quan-day.md): thứ tự bước, giữ theo id, giữ lại một lần, `unfulfillable`, `base_price`, `cook_started.items`; day dùng một `IdAllocator`, bàn giao cùng tick, Shop không hao, id mới cho mẫu Ngày 2+.
- [ ] `tests/test_p3_quan.py` + đổi `test_quan_*.py`, `test_day.py` (ghi lý do).

### TV3 (hgmdz1210, Hưng) — lát A, D, QA
- [ ] Lát A theo [adapter-hud-qa.md](../spec/phase-3/adapter-hud-qa.md) mục A, đẩy `main` **trước phút 10**.
- [ ] HUD mục B; ảnh chụp vào `docs/proof/phase-3/`.
- [ ] Smoke mục C, bật v1.2, CHANGELOG, `docs/verification/phase-3.md`, `docs/ai-usage-log.md`.

## Rủi ro
- **Gather P2 chưa gộp + chưa có tag nào trên remote** ⇒ TV1 làm bước 0 trước mọi thứ; nếu tới phút 10 chưa gộp được, lát B làm trên nhánh gather P2 và gộp chung.
- Nhiều file test đổi fixture cùng lúc ⇒ mỗi người chỉ đổi test thuộc module mình (bảng tác động), commit riêng với lý do.
- `Fraction` chậm ⇒ đo `day --days 1` ≤ 20 s ở phút 25.
- Bật v1.2 làm vỡ test còn dùng kho đếm ⇒ chạy toàn bộ unittest ngay sau khi bật, sửa trước khi tag.
