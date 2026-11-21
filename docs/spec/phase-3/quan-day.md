# Spec lát C — Quán có độ tươi + bàn giao trong `day` (TV2)

> Nguồn: Ticket-03 mục 1 (độ tươi, giữ chỗ, giá, thứ tự tick quán, scenario, JSONL). Hàm adapter: [README.md](README.md) mục 4.2.
> File: `chonoi/sim/quan.py`, `chonoi/sim/day.py`.

## A. Kho quán
- `self.stock` = list cá thể (từ `--inventory`, `quan.stock` scenario hoặc bàn giao của day). Nhận **nguyên** số lượng, id, fresh, kể cả hàng ươn. Không giới hạn sức chứa.
- Snapshot `stock` = mảng `item_out` sắp theo id.

## B. Thứ tự một bước quán (đề mục 1, AC-P3-08 … 12)
1. Đồng hồ, timer.
2. **Hao tươi** mọi cá thể trong `stock` (kể cả đang giữ chỗ): `decay(stock, 1/240, 30)`. Phát hết `spoiled {item_id, kind, location:"stock"}` theo id.
3. **Giữ chỗ bị ươn** (AC-P3-11): lấy các đơn `reserved` có cá thể vừa ươn, xử lý theo `order_tick` rồi id bàn:
   - nhả toàn bộ phần giữ của đơn;
   - thử giữ lại **đúng một lần** bằng luật chọn ở mục C;
   - không đủ ⇒ `order_status = "unfulfillable"`, khách vẫn chờ tới hết kiên nhẫn (rồi rời như thường).
4. Món chín (theo id bếp).
5. Di chuyển + tối đa một tương tác.
6. Thanh toán, kiên nhẫn, đóng ca. Giao đúng tick kiên nhẫn chạm 0 vẫn hợp lệ; giao đúng tick hết ca được trả ngay.
7. Còn giờ ⇒ khách mới.

## C. Giữ chỗ theo id (AC-P3-10)
- Khả dụng = trong `stock`, **chưa ươn**, chưa bị đơn khác giữ.
- Mỗi loại trong công thức: lấy `n` cá thể khả dụng **tươi nhất**, hòa theo id nhỏ. Thiếu một loại ⇒ không giữ được (khách mới: món đó không phải ứng viên).
- `customers[].reserved` = mảng id (sắp theo kind rồi id).
- Chọn món cho khách mới: ứng viên = món trong menu (hoặc kế hoạch khi `day`) giữ được theo luật trên.

## D. Nấu và giá (AC-P3-12)
- Bắt đầu nấu: **tiêu đúng** các id đang giữ (gỡ khỏi `stock`), chốt `base_price = floor(price × mean(fresh) / 100)` với fresh tại thời điểm nấu (sau bước hao của tick này). Tính bằng `Fraction` rồi `floor`.
- `cook_started.data` thêm `items` = mảng `item_out` sắp theo kind rồi id.
- Món (trên bếp, trên tay, của khách) giữ cấu trúc cũ, thêm/đổi `base_price`. Món chín không hao.
- Trả tiền dùng `base_price`; boa `floor(base_price × 0.2)` nếu đủ điều kiện kiên nhẫn. Điểm không đổi công thức.

## E. Scenario quán (phần kiểm trên kho thực — AC-P3-14)
TV3 kiểm **schema** (mảng cá thể, mảng id). TV2 kiểm trên kho thực lúc mở quán (mã 2 nếu sai):
- id trong `reserved` phải có trong `stock`, chưa ươn, đúng công thức của món, không trùng với đơn khác.
- Đơn `reserved` **không khai** `reserved` ⇒ tự cấp theo `order_tick` rồi id bàn, tươi nhất rồi id nhỏ; không đủ ⇒ mã 2.
- Id duy nhất giữa `stock`, `reserved`, món đang có.

## F. Day (AC-P3-13)
- `DaySim` giữ một `item_ids = IdAllocator()` **riêng cho cá thể** suốt lượt, truyền vào GatherSim/QuanSim (tham số mới `item_ids`). Allocator mới mỗi pha cho khách/cá/đơn vẫn giữ như clarify #26.
- `gather_end` ⇒ bàn giao list cá thể của giỏ cho quán **cùng tick**, không hao thêm; quán chạy gameplay từ bước sau. Ngất ⇒ kho rỗng.
- Shop: `stock` = kho dư (mảng cá thể), **không hao** trong Shop. Đóng Shop ⇒ bỏ kho dư.
- Ngày 1 giữ nguyên id trong mẫu `gather.hold`; Ngày 2+ cấp id **mới** cho từng phần tử mẫu theo thứ tự mảng, giữ `kind`/`fresh` ban đầu.

## G. Test (`tests/test_p3_quan.py`)
- `stock` 1 cá thể fresh 30.004 ⇒ `spoiled{location:"stock"}` ở tick 1 (30.004 − 1/240 ≈ 29.9998 < 30); fresh 30.005 ⇒ chưa ươn ở tick 1 (≈ 30.0008), ươn ở tick 2.
- Đơn giữ `[I1]`, I1 vừa ươn, kho còn I2 tươi ⇒ đơn giữ `[I2]`; không còn ⇒ `unfulfillable`.
- Hai đơn cùng mất hàng ⇒ đơn `order_tick` nhỏ hơn được giữ lại trước.
- Cá lóc fresh 50 ⇒ cá lóc nướng trui `base_price = floor(60×50/100) = 30`, boa 6.
- Lẩu cá linh với fresh [100, 90, 80, 70] ⇒ TB 85 ⇒ `floor(120×0.85) = 102`.
- `cook_started.items` sắp đúng; snapshot `reserved` là mảng id.
- Day: id giỏ Ngày 1 là `I1…`, Ngày 2 tiếp tục tăng; kho quán ở tick đổi pha bằng đúng giỏ cuối gather; Shop `stock` không đổi fresh qua 600 tick.
- Đổi `test_quan_*.py`, `test_day.py` sang cá thể (ghi lý do).
