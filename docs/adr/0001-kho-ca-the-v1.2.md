# ADR 0001 — Kho cá thể có độ tươi (Test Contract v1.2)

- Trạng thái: **Đề xuất**, cả nhóm gật ở phút 0–7 của Phase 3
- Bối cảnh: Ticket-03 "Mùa Nước Nổi" thay kho đếm `{"items":{kind:n}}` bằng kho cá thể `{"items":[{id,kind,fresh}]}`, thêm hao tươi, hàng ươn, giữ chỗ theo id và giá theo độ tươi. Mọi module (gather, quan, day, file kho, scenario, HUD, test) đều chạm kho.

## Quyết định

1. **Một kiểu cá thể dùng chung** ở `chonoi/inventory.py`: dict `{"id": str, "kind": str, "fresh": Fraction}`. Mọi module dùng hàm của adapter (`new_item`, `decay`, `is_spoiled`, `item_out`, `read_inventory`, `write_inventory`, `validate_item_list`), không tự dựng dict.
2. **Độ tươi lưu bằng `fractions.Fraction`** để chính xác ở ngưỡng 30 và phép `floor`:
   - Đọc số từ JSON bằng `Fraction(str(x))` (giữ đúng số thập phân trong file).
   - Hao mỗi tick: gather `0.5/60 = 1/120`, quán `0.25/60 = 1/240` (tương đương 240 đơn vị/điểm, −2 và −1 đơn vị/tick như đề gợi ý). Kẹp đáy 0.
   - Ươn: `fresh < spoiled_below` so trên giá trị **chưa làm tròn**.
   - Ra JSONL: `round(float(fresh), 3)`. Ra file kho: `float(fresh)` dạng `repr` (đủ số để đọc lại cùng nhánh ngưỡng).
3. **Id cá thể** họ `I`, cấp bằng một `IdAllocator` **riêng cho cá thể**, sống suốt lượt (xuyên pha và Ngày). Id khách/cá/đơn vẫn theo clarify #26 (allocator mới mỗi pha). Id có sẵn trong scenario/file được `reserve()` trước, id mới nối tiếp hậu tố lớn nhất. Không cấp lại id đã dùng/bỏ.
4. **Chuyển phiên bản an toàn:** adapter đọc/ghi **cả hai** schema theo `contract_version` (`"1.1"` → đếm, `"1.2"` → cá thể). Các lát code theo cá thể trong bộ nhớ ngay; manifest chỉ bật `"1.2"` ở bước tích hợp cuối (phút 25) khi gather, quán, day đều xanh. Khi `"1.2"`: file kho đếm, sai schema, kind lạ, id trùng/rỗng, fresh ngoài [0,100] hoặc không hữu hạn ⇒ mã 2.
5. **Thứ tự tích hợp vào `main`:** (0) gather P2 còn dở → (1) adapter + test migration → (2) gather độ tươi → (3) quán + day độ tươi → (4) HUD → (5) bật v1.2 + CHANGELOG + tag. Sau mỗi bước `main` phải chạy được và test xanh.

## Hệ quả
- Test dùng kho đếm (`hold` mảng kind, `stock`/`reserved` dạng map, file kho đếm) phải đổi fixture; ghi lý do "Ticket-03 thay schema kho" trong commit và [CHANGELOG.md](../../CHANGELOG.md).
- `Fraction` chậm hơn float; hàng trong giỏ ≤ 12 và kho quán nhỏ nên không ảnh hưởng mốc ≤ 20 s/Ngày (đo lại ở phút 25).

## Phương án đã loại
- Float thuần: sai ở ngưỡng 30 sau hàng nghìn phép trừ 1/120.
- Số nguyên 240 đơn vị/điểm: không biểu diễn chính xác mọi `fresh` đọc từ file (vd 33.333).
