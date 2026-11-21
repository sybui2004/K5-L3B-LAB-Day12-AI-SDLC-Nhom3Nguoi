# Ma trận truy vết Phase 3 (Ticket-03, Test Contract v1.2)

> Commit bàn giao (tag `phase-3`): `<điền sha>` · AC: [`docs/spec/phase-3/README.md`](../spec/phase-3/README.md) mục 2 · Kết quả ghi **trung thực** trên đúng commit tag.

| AC | Cách kiểm chứng | Bằng chứng (`docs/proof/phase-3/...`) | Kết quả |
|---|---|---|---|
| AC-P3-01 manifest 1.2 + `freshness` | unittest contract | | |
| AC-P3-02 file kho cá thể, từ chối kho đếm (mã 2) | `tests/test_p3_inventory.py` | | |
| AC-P3-03 ghi một lần, nguyên tử, ngất rỗng, `--ticks` | `tests/test_p3_inventory.py` | | |
| AC-P3-04 smoke bàn giao file | `handoff.md`, `handoff-*.jsonl`, `kho.json` | | |
| AC-P3-05 hàng mới 100, hao giỏ, id theo thứ tự | `tests/test_p3_gather.py` | | |
| AC-P3-06 `spoiled` hold, mẫu đề tick 1 | `tests/test_p3_gather.py` | | |
| AC-P3-07 `lost` LIFO cá thể, ngất | `tests/test_p3_gather.py` | | |
| AC-P3-08 kho quán nguyên vẹn, hao 0.25/s, pause | `tests/test_p3_quan.py` | | |
| AC-P3-09 `spoiled` stock, ươn không nấu | `tests/test_p3_quan.py` | | |
| AC-P3-10 giữ theo id tươi nhất | `tests/test_p3_quan.py` | | |
| AC-P3-11 giữ lại một lần, `unfulfillable` | `tests/test_p3_quan.py` | | |
| AC-P3-12 `base_price`, boa, `cook_started.items` | `tests/test_p3_quan.py` | | |
| AC-P3-13 day bàn giao cùng tick, id xuyên Ngày, Shop không hao | `tests/test_p3_quan.py`, `day-2.jsonl` | | |
| AC-P3-14 scenario v1.2, mã 2 | `tests/test_p3_inventory.py`, `tests/test_p3_quan.py` | | |
| AC-P3-15 HUD độ tươi/ươn | ảnh chụp 1280×720 | | |
| AC-P3-16 regression P1–P2, CHANGELOG, tag | `unittest.txt`, `CHANGELOG.md` | | |

## Test đổi vì luật mới (Ticket-03 thay schema kho)
| Test | Vì sao đổi | Commit |
|---|---|---|

## Đánh giá ngắn
- Đạt / chưa đạt:
- Bài học từ lần đổi kho (cũng ghi vào `docs/retro.md`):
