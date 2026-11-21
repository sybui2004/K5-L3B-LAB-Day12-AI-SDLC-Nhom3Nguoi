# Retro nhóm

> Điều phối: TV2 (lit1numyt). Tổng hợp từ lịch sử Git, PR, `docs/standup.md` và `docs/ai-usage-log.md`. Các hành động đề xuất bên dưới chờ nhóm xác nhận.

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
- Việc gộp adapter kho và HUD v1.2 hoàn tất sau đó ở PR #19. Đợt tích hợp v1.3 sau lab chốt hai nhánh ứng viên ở `bffd2e5`. [Verification Phase 3](verification/phase-3.md) · [Verification Phase 4](verification/phase-4.md)

### Điều làm tốt
- Mỗi phase có spec + plan + phân lát rõ người trước khi code (PR #4, #9, #15) ⇒ ba người làm song song ít đụng file.
- Hợp đồng chuyển pha (`ctx`, một `Streams`/`IdAllocator`) giúp ghép gather của TV1 (PR #12) với day/quán của TV2 (PR #10, #13) mà không sửa chéo.
- Có test hộp đen theo từng lát. Nhánh `feature/p4-soak-spec` ghi nhận 158 test đạt. Lý do đổi test được ghi trong các ma trận verification.
- Nhóm ghi các điểm cần chốt trong `docs/clarify.md`, gồm thay đổi kho v1.2 và vấn đề máy chỉ có `python3` ở #42.

### Điều cần sửa
- `phase-1` gắn muộn so với 1:00. Tại thời điểm rà soát sau lab, chưa có `phase-2` (hạn 1:55), `phase-3` (hạn 2:30), `phase-4` và Release `v1.0.0` (hạn 3:00). Tag hoặc Release tạo sau đợt rà soát là bàn giao muộn.
- Trùng/nhận việc của nhau do lát trễ: TV2 viết bếp lát 4 (TV1) và day/pause (plan TV3) — PR #8 phải gộp "lấy bản quan lát 4 của TV2"; TV2 viết hàm cá thể khi lát A chưa có (`b93b4f3`).
- Adapter v1.2 gộp chậm khiến các nhánh dùng schema kho khác nhau dù có lúc cùng khai manifest v1.1. Cần khóa mốc hợp đồng và chạy smoke bàn giao kho trước khi làm lát phụ thuộc.

### Số liệu
- Commit đến mốc `bffd2e5`, bỏ commit merge và khung giảng viên (`git shortlog -sn --no-merges bffd2e5`): Khoa 26, Hưng 24, Sỹ 17. Chưa thấy commit mang tên hoặc handle của Sang trong lịch sử này.
- Nhóm dùng PR để tích hợp, đối chiếu spec và log kiểm chứng. Hai ví dụ là rà adapter và HUD ở PR #19 và tích hợp soak ở PR #20.
- Token theo người: **không đo** (cột token trong `docs/ai-usage-log.md` để "—").

### Một lần AI sai và cách nhóm phát hiện
- P2: AI viết test pause kỳ vọng `quan_end` ở tick `10800 + 4`; test đỏ (thực tế `+5`). Đọc lại ticket 4.2 ("bước vào pause chỉ tăng tick ngoài") ⇒ bước bấm pause cũng không chạy gameplay ⇒ luật đúng, sửa test (`docs/ai-usage-log.md` P2, commit `daa20a0`).
- P3: AI cho rằng hàng 31 điểm ươn ở tick 240; test đỏ ⇒ đúng 30 chưa "< 30" nên là tick 241 — kiểm bằng phép tính `Fraction` (commit `e64eca5`).

### Hành động đề xuất và người phụ trách
1. Gắn tag ngay khi hết giờ phase, kể cả khi lát chưa xong, rồi ghi "chưa đạt" — **TV1** (Integrator).
2. Đầu phase, rà lát trễ và điều phối người hỗ trợ theo thời hạn của lab — **TV2** (điều phối).
3. Verification điền trên đúng commit tag, có sha — **TV3** (QA).
4. Giao việc cho AI kèm link spec/plan nhóm, không chỉ ticket — **mọi người**.

### Nếu làm lại, đổi gì
- Chốt adapter/hợp đồng dữ liệu (kho cá thể) thành commit nền ở phút 0–7, trước mọi lát.
- Chia gather cho hai người (cá/sinh và Cá Sấu) thay vì một người ôm cả gather + tích hợp.
