# Ma trận truy vết Phase 3 (Ticket-03, Test Contract v1.2)

> Bản bàn giao muộn `phase-3` được chuẩn bị từ `0701271`. [Tiêu chí Phase 3](../spec/phase-3/README.md)

> Kiểm lại lát hồi quy thủy quái theo Phase 2. Quái ở bước lùi cuối chỉ xét chạm từ bước tiếp theo. Test hồi quy liên quan nằm trong `test_p2_gather.py`.

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-3/...`) | Kết quả |
|---|---|---|---|
| AC-P3-01 manifest 1.2 + `freshness` | unittest contract | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-02 file kho cá thể, từ chối kho đếm (mã 2) | `tests/test_p3_inventory.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-03 ghi một lần, nguyên tử, ngất rỗng, `--ticks` | `tests/test_p3_inventory.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-04 smoke bàn giao file | `handoff.md`, `handoff-*.jsonl`, `kho.json` | [handoff.md](../proof/phase-3/handoff.md), [kho.json](../proof/phase-3/kho.json), [gather](../proof/phase-3/handoff-gather.jsonl.txt), [quan](../proof/phase-3/handoff-quan.jsonl.txt) | Đạt |
| AC-P3-05 hàng mới 100, hao giỏ, id theo thứ tự | `tests/test_p3_gather.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-06 `spoiled` hold, mẫu đề tick 1 | `tests/test_p3_gather.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-07 `lost` LIFO cá thể, ngất | `tests/test_p3_gather.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-08 kho quán nguyên vẹn, hao 0.25/s, pause | `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-09 `spoiled` stock, ươn không nấu | `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-10 giữ theo id tươi nhất | `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-11 giữ lại một lần, `unfulfillable` | `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-12 `base_price`, boa, `cook_started.items` | `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-13 day bàn giao cùng tick, id xuyên Ngày, Shop không hao | `tests/test_p3_quan.py`, `day-2.jsonl` | [unittest.txt](../proof/phase-3/unittest.txt), [handoff.md](../proof/phase-3/handoff.md), [day-2-events](../proof/phase-3/day-2-events.jsonl.txt) | Đạt, sau khi sửa lỗi làm tròn độ tươi lúc bàn giao |
| AC-P3-14 scenario v1.2, mã 2 | `tests/test_p3_inventory.py`, `tests/test_p3_quan.py` | [unittest.txt](../proof/phase-3/unittest.txt) | Đạt |
| AC-P3-15 HUD độ tươi/ươn | ảnh chụp 1280×720 | [giỏ](../proof/phase-3/hud-gio-do-tuoi.png), [kho quán](../proof/phase-3/hud-kho-do-tuoi.png) | Đạt trên scenario dựng sẵn; chưa có người chơi kiểm tra |
| AC-P3-16 regression P1–P2, CHANGELOG, tag | `unittest.txt`, `CHANGELOG.md` | [unittest.txt](../proof/phase-3/unittest.txt), [CHANGELOG](../../CHANGELOG.md) | Hồi quy đạt. Bàn giao sau mốc giờ lab. |

## Test đổi vì luật mới (Ticket-03 thay schema kho)
| Test | Vì sao đổi | Commit |
|---|---|---|
| `test_quan_rules`, `test_quan_customers`, `test_quan_kitchen` | Fixture kho và `reserved` đổi từ dạng đếm sang cá thể; điều kiện kiểm giữ nguyên | nhánh `feature/p3-adapter-hud` |
| `test_quan_kitchen.test_contract_v11_standard_data` | Manifest đã bật `1.2` | nhánh `feature/p3-adapter-hud` |
| `test_gather_rules`, `test_p2_gather`, `test_smoke_p1`, `test_day`, `test_p2_live_day`, `test_p3_quan` | `hold` và file kho là cá thể; kho đếm nay bị từ chối | nhánh `feature/p3-adapter-hud` |

## Đánh giá ngắn
- Hồ sơ HUD dùng scenario dựng sẵn. Mốc giờ `phase-3` đã qua trước khi đóng gói bản bàn giao.
- Bài học từ lần đổi kho (cũng ghi vào `docs/retro.md`): dữ liệu làm tròn để xuất JSONL không được dùng lại cho luật; lỗi này chỉ lộ ra ở đúng ngưỡng ươn nên cần test sát ngưỡng khi bàn giao giữa các pha.
