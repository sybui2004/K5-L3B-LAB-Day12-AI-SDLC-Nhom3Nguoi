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
| AC-P2-10 2 bếp/4 bàn/6 món | `tests/test_quan_kitchen.py` Data + `test_quan_customers` (4 bàn) | [integration.txt](../proof/phase-2/integration.txt) §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-11 tương tác, đơn cũ nhất | `test_quan_kitchen.Stove.*` (đơn cũ nhất theo order_tick rồi id bàn, hòa bếp trước bàn rồi id) | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-12 lịch khách, boa, uy tín | `test_quan_customers.*`, `test_quan_kitchen.Serve.*` (lịch 120+900k, boa floor, uy tín ±) | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-13 đóng ca | `test_quan_kitchen.CloseShift.*` | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-14 `day_plan` = Σ công thức | `test_quan_kitchen.Data.test_contract_v11_standard_data`; `contract.py` kiểm khi nạp | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-15 chọn món theo kế hoạch | `test_day.DayLoop.test_handoff_inventory_to_quan_and_plan_filter`, `test_quan_kitchen.Ctx.*` | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-16 mua nâng cấp | `test_day.Shop.*` (bought, funds, max_level, unknown, đúng giá, mở rộng bỏ qua) | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-17 đóng Shop | `test_day.Shop.test_buy_and_shop_done_same_frame`, `DayLoop.test_one_day_phase_order_and_end` (shop_end time sau 600) | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-18 chuỗi pha `day` | `test_day.DayLoop.*` | [day1-events.jsonl.txt](../proof/phase-2/day1-events.jsonl.txt) | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-19 xuyên Ngày, `active_upgrades` | `test_day.Shop.test_buy_upgrade_applies_from_next_day`, `DayLoop.test_money_carries_and_deterministic_two_days` | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-20 pause | `test_day.Pause.*` | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-21 scenario `day`, mã 2 | `test_day.BadInput.*` | §4 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-22 snapshot/event/end mới | `test_day.DayLoop.test_snapshot_fields_and_phase_change_snapshot` | §2–3 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-23 1 Ngày ≤ 20 s, tất định | `time` + `cmp` (1 Ngày 0.14 s; 5 Ngày 0.6 s; cùng seed giống từng byte) | §2–3 | đạt trên `feature/p2-quan-shop` (TV2); QA chạy lại trên commit tag |
| AC-P2-24 menu và các màn | ảnh chụp 1280×720 | | |
| AC-P2-25 pause UI | ảnh chụp / gif | | |
| AC-P2-26 HUD, chữ ≥ 18 px, ≥ 30 FPS | ảnh chụp, đo FPS | | |
| AC-P2-27 smoke tích hợp phút 20 | `integration.md` | | |
| AC-P2-28 regression P1, tài liệu, tag | `unittest.txt` | | |

## Test đổi vì số chuẩn (ghi lý do)
| Test | Vì sao đổi | Commit |
|---|---|---|
| `test_smoke_p1.test_con_03_old_and_future_modes_rejected` | v1.1 mở `--mode day`, chỉ còn mode cũ bị từ chối | `daa20a0` |
| `test_quan_customers` (3 test) | P1 có 1 bàn, v1.1 có 4 bàn; `customer_left` thêm `reason` | `55051ff` |
| `test_day` (tick 0, lệnh `weapon`) | PO chốt #19 (snapshot tick 0 trước) và #18 (lệnh mở rộng bỏ qua) thay #25/#27 | `feature/p2-quan-shop` |

## Đánh giá ngắn
- Đạt / chưa đạt:
- Điều cần chỉnh cho Phase 3:
