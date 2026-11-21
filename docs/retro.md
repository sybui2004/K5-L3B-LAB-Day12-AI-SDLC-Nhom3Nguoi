# Retro nhóm

> Điều phối: TV2 (lit1numyt). Bản nháp dựng từ bằng chứng trong repo (PR #1–#16, `docs/standup.md`, `docs/ai-usage-log.md`, `git shortlog`); cả nhóm đọc và sửa trước khi gắn tag.

## Phase 2 (nhanh)
- Điều tốt: spec + plan Phase 2 gộp trước khi code (PR #4); quán v1.1, day, Shop, pause có test hộp đen (PR #6, #10).
- Điều tệ: TV2 code day/Shop trước khi đọc hợp đồng chuyển pha của nhóm ⇒ phải sửa lại (PR #10, clarify #25–27 bị hủy); không có tag `phase-2`.
- 1 hành động cho Phase 3: *không được chốt lúc đó* (mục này để trống trong P2).

## Phase 4 (cuối)

### Rà lại hành động Phase 2
- P2 **chưa chốt** hành động nào (mục trên trống). Hành động thực tế nhóm đã làm ở P3–P4:
  - Viết ADR + bảng tác động + plan **trước** khi code: ADR 0001, `docs/spec/phase-3/README.md` mục 3 (PR #9), plan P4 (PR #15).
  - TV2 đọc plan/spec nhóm trước khi giao việc cho AI (P3 PR #13 khớp spec ngay, không phải làm lại như P2).
  - Gắn tag `phase-1` muộn, có ghi trung thực (PR #11).
- Còn vướng: tag `phase-2`, `phase-3` vẫn chưa có; Phase 3 lát A (file kho v1.2, bật `1.2`) và lát B (giỏ có độ tươi) chưa gộp ⇒ manifest còn `1.1`. Lý do: một người (TV1) ôm gather + tích hợp + tag, lát A phụ thuộc chéo.

### Điều làm tốt
- Mỗi phase có spec + plan + phân lát rõ người trước khi code (PR #4, #9, #15) ⇒ ba người làm song song ít đụng file.
- Hợp đồng chuyển pha (`ctx`, một `Streams`/`IdAllocator`) giúp ghép gather của TV1 (PR #12) với day/quán của TV2 (PR #10, #13) mà không sửa chéo.
- Test hộp đen theo từng lát, regression luôn xanh trước khi gộp (158 test ở `feature/p4-soak-spec`); test đổi đều ghi lý do trong commit.
- `docs/clarify.md` được dùng thật: #1–#41, có người quyết và dẫn chữ đề.

### Điều cần sửa
- Tag không đúng hạn: chỉ có `phase-1` (gắn muộn); `phase-2`, `phase-3` thiếu.
- Trùng/nhận việc của nhau do lát trễ: TV2 viết bếp lát 4 (TV1) và day/pause (plan TV3) — PR #8 phải gộp "lấy bản quan lát 4 của TV2"; TV2 viết hàm cá thể khi lát A chưa có (`b93b4f3`).
- Lát P3 chưa gộp ⇒ v1.3 phải đứng trên gameplay v1.2 chưa đủ.

### Số liệu
- Commit theo người (không tính merge, không tính commit khung của giảng viên "Hai Duong"): lit1numyt 21+, sybui2004 15, Doan Sy Hung 14, Sang Phan (admin) 0 — `git shortlog -sn --no-merges main`.
- Cách đọc code của nhau: mọi thay đổi qua PR vào repo của TV1 (sybui2004), TV1 gộp sau khi chạy test; PO đối chiếu spec/clarify với code của mỗi lát.
- Token theo người: **không đo** (cột token trong `docs/ai-usage-log.md` để "—").

### Một lần AI sai và cách nhóm phát hiện
- P2: AI viết test pause kỳ vọng `quan_end` ở tick `10800 + 4`; test đỏ (thực tế `+5`). Đọc lại ticket 4.2 ("bước vào pause chỉ tăng tick ngoài") ⇒ bước bấm pause cũng không chạy gameplay ⇒ luật đúng, sửa test (`docs/ai-usage-log.md` P2, commit `daa20a0`).
- P3: AI cho rằng hàng 31 điểm ươn ở tick 240; test đỏ ⇒ đúng 30 chưa "< 30" nên là tick 241 — kiểm bằng phép tính `Fraction` (commit `e64eca5`).

### Hành động tiếp theo (đề xuất — cả nhóm gật, có người nhận)
1. Gắn tag ngay khi hết giờ phase, kể cả khi lát chưa xong, rồi ghi "chưa đạt" — **TV1** (Integrator).
2. Không mở phase mới khi lát của phase trước chưa gộp: phút 0 mỗi phase rà lát trễ, người xong sớm nhận — **TV2** (điều phối).
3. Verification điền trên đúng commit tag, có sha — **TV3** (QA).
4. Giao việc cho AI kèm link spec/plan nhóm, không chỉ ticket — **mọi người**.

### Nếu làm lại, đổi gì
- Chốt adapter/hợp đồng dữ liệu (kho cá thể) thành commit nền ở phút 0–7, trước mọi lát.
- Chia gather cho hai người (cá/sinh và Cá Sấu) thay vì một người ôm cả gather + tích hợp.
