# Kế hoạch Phase 2 — Ticket-02 (≤ 1 trang)

- **Mục tiêu:** Số chuẩn Test Contract v1.1 + vòng ngày `day` (gather → quan → Shop, D1–D5), pause, menu, HUD; tag `phase-2` trên `main` trước **1:55**. Spec: [`docs/spec/phase-2/`](../spec/phase-2/README.md).
- **Phân vai:** 3 người làm (Sang Phan admin, không nhận lát). Mỗi người lái agent AI cho lát của mình, đọc lại diff trước khi gộp.

## Việc / người / phụ thuộc

| # | Việc | Người | Phụ thuộc | Plan |
|---|---|---|---|---|
| 0a | Gộp `feature/gather-quan-kitchen` (gather + quan lát 4 của P1) vào `main`; gắn tag `phase-1` muộn, ghi trung thực | TV1 | — | [gather.md](phase-2/gather.md) bước 0 |
| 0b | Lát 0: `game.contract.json` v1.1 + 6 nguyên liệu (commit nền) | TV1 | 0a | [gather.md](phase-2/gather.md) bước 0 |
| 1 | Lát 1: số chuẩn gather, cá bơi, sinh cá | TV1 | 0b | [gather.md](phase-2/gather.md) |
| 2 | Lát 2: Cá Sấu, Máu, ngất (LIFO, bất tử, recoil) | TV1 | 1 (giỏ LIFO) | [gather.md](phase-2/gather.md) |
| 3 | Lát 3: 2 bếp/4 bàn/6 món, `plan_ingredients`, chọn món theo kế hoạch | TV2 | 0a, 0b | [quan-shop.md](phase-2/quan-shop.md) |
| 4 | Shop sim (`buy`, `shop_done`, 600 tick) | TV2 | 0b | [quan-shop.md](phase-2/quan-shop.md) |
| 5 | Lát 4: `--mode day`, `DaySim`, pause, scenario `day`, snapshot/end mới | TV3 | 0b; fixture trước, thật sau 3, 4 | [day-ui-qa.md](phase-2/day-ui-qa.md) |
| 6 | Menu, Intro/Result/Shop/Summary, pause UI, HUD | TV3 | 5 | [day-ui-qa.md](phase-2/day-ui-qa.md) |
| 7 | PO: clarify #13–19, giữ `docs/clarify.md`, đối chiếu đề | TV2 | — | [quan-shop.md](phase-2/quan-shop.md) bước 0 |
| 8 | Smoke tích hợp phút 20, smoke `day`, verification, retro, tag | TV1 + TV3 | 1–6 | [day-ui-qa.md](phase-2/day-ui-qa.md) bước cuối |

## Mốc giờ (phút trong phase · giờ lab)

| Phút | Giờ | Việc |
|---|---|---|
| 0–5 | 1:00–1:05 | Cả nhóm đọc [spec README](../spec/phase-2/README.md) mục 3 (hợp đồng chuyển pha) và **gật**; TV1 làm 0a; PO mở clarify #13–19 |
| 5–8 | 1:05–1:08 | TV1 đẩy lát 0 (contract v1.1) lên `main`; TV2, TV3 rebase |
| 8–20 | 1:08–1:20 | Làm song song lát 1/2, 3/4, 5. TV3 dựng `DaySim` bằng fixture |
| **20** | **1:20** | **Smoke tích hợp** `gather --inventory-out` → `quan --inventory`, lưu `docs/proof/phase-2/integration.*`. Standup 2–3 phút ghi `docs/standup.md`, ai xong thì sang lát trễ |
| 20–35 | 1:20–1:35 | Build tiếp; gộp `main` từng lát khi xanh; TV3 thay fixture bằng sim thật |
| 35 | 1:35 | **Đóng băng tính năng** |
| 35–45 | 1:35–1:45 | Smoke `day --days 1` và `--days 3`, regression P1, điền verification; TV1 gắn tag |
| 45–50 | 1:45–1:50 | Retro nhanh (`docs/retro.md`, 1 hành động có người nhận) |
| 50–55 | 1:50–1:55 | Dự phòng; đẩy `phase-2` **chậm nhất 1:55** |

## Thứ tự gộp vào `main`
lát 0 → lát 3 (quan) → lát 1 → Shop → lát 2 → day/pause → UI. Mỗi lần gộp: chạy toàn bộ unittest.

## Rủi ro
- **Tag `phase-1` chưa có, lát 4 P1 chưa gộp** ⇒ làm 0a ngay phút 0, ghi trễ vào `docs/verification/phase-1.md`.
- Số chuẩn làm vỡ test P1 ⇒ sửa test, ghi `Đổi test: <lý do>` trong commit; không sửa test cho xanh khi luật sai.
- TV1 ôm 2 lát gather ⇒ ưu tiên lát 1 (số chuẩn, cá) trước; nếu phút 35 lát 2 chưa xong ⇒ gắn tag với phần đã xanh, ghi "chưa đạt" trong verification. TV2 xong Shop sớm thì nhận viết test lát 2.
- TV3 phụ thuộc 3 lát ⇒ dùng fixture + giao diện `ctx` đã chốt, không chờ.
- Nhiều người sửa `chonoi/scenario.py` ⇒ chia theo hàm (gather: TV1, quan: TV2, khối `day`: TV3), gộp sớm.
- Headless 1 Ngày > 20 s ⇒ đo ở phút 35; chậm thì tối ưu vòng cá/quái (tránh tính khoảng cách O(n²) mỗi bước).
