# Ma trận truy vết Phase 2 (Ticket-02, Test Contract v1.1)

> Commit bàn giao (tag `phase-2`): `<điền sha>` · Danh sách AC: [`docs/spec/phase-2/README.md`](../spec/phase-2/README.md) mục 2.
> Kết quả ghi **trung thực** trên đúng commit gắn tag.

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-2/...`) | Kết quả |
|---|---|---|---|
| AC-P2-01 manifest v1.1, 6 nguyên liệu | unittest `contract`, đọc manifest | | |
| AC-P2-02 gather số chuẩn | `tests/test_p2_gather.py` | | |
| AC-P2-03 cá bơi | `tests/test_p2_gather.py` | | |
| AC-P2-04 sinh cá | `tests/test_p2_gather.py`, headless seed 1 | | |
| AC-P2-05 bắt theo vị trí trước khi bơi | `tests/test_p2_gather.py` | | |
| AC-P2-06 Cá Sấu patrol/chase, M2 từ Ngày 3 | `tests/test_p2_gather.py`, `day --days 3` | | |
| AC-P2-07 chạm, LIFO, bất tử, recoil | `tests/test_p2_gather.py` | | |
| AC-P2-08 ngất do quái | `tests/test_p2_gather.py` | | |
| AC-P2-09 thứ tự bước gather | `tests/test_p2_gather.py` | | |
| AC-P2-10 2 bếp/4 bàn/6 món | `tests/test_p2_quan_shop.py` | | |
| AC-P2-11 tương tác, đơn cũ nhất | `tests/test_p2_quan_shop.py` | | |
| AC-P2-12 lịch khách, boa, uy tín | `tests/test_p2_quan_shop.py` | | |
| AC-P2-13 đóng ca | `tests/test_p2_quan_shop.py` | | |
| AC-P2-14 `day_plan` = Σ công thức | `tests/test_p2_quan_shop.py` | | |
| AC-P2-15 chọn món theo kế hoạch | `tests/test_p2_quan_shop.py` | | |
| AC-P2-16 mua nâng cấp | `tests/test_p2_quan_shop.py` | | |
| AC-P2-17 đóng Shop | `tests/test_p2_quan_shop.py` | | |
| AC-P2-18 chuỗi pha `day` | `tests/test_p2_day.py`, `day-1.jsonl` | | |
| AC-P2-19 xuyên Ngày, `active_upgrades` | `tests/test_p2_day.py`, `day-3.jsonl` | | |
| AC-P2-20 pause | `tests/test_p2_day.py` | | |
| AC-P2-21 scenario `day`, mã 2 | `tests/test_p2_day.py` | | |
| AC-P2-22 snapshot/event/end mới | `tests/test_p2_day.py` | | |
| AC-P2-23 1 Ngày ≤ 20 s, tất định | `time` + `cmp` | | |
| AC-P2-24 menu và các màn | ảnh chụp 1280×720 | | |
| AC-P2-25 pause UI | ảnh chụp / gif | | |
| AC-P2-26 HUD, chữ ≥ 18 px, ≥ 30 FPS | ảnh chụp, đo FPS | | |
| AC-P2-27 smoke tích hợp phút 20 | `integration.md` | | |
| AC-P2-28 regression P1, tài liệu, tag | `unittest.txt` | | |

## Test đổi vì số chuẩn (ghi lý do)
| Test | Vì sao đổi | Commit |
|---|---|---|

## Đánh giá ngắn
- Đạt / chưa đạt:
- Điều cần chỉnh cho Phase 3:
