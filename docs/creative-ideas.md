# Ý tưởng "Sáng tạo của nhóm" — PO ĐÃ DUYỆT MỘT PHẦN

> Nhánh: `docs/creative-ideas` (worktree riêng). Chưa có code.

## Quyết định của PO (2026-11-21)
| Nhóm | Trạng thái | Ý nghĩa |
|---|---|---|
| **A, B, C, H** | **Đã duyệt — làm trước** | Thuần trình bày (`chonoi/web/`), sau khi lõi đúng + `phase-1` có tag |
| **D, E, F** | **Đã duyệt — giữ trong backlog, làm sau** | Chỉ bắt đầu khi A/B/C/H xong và còn giờ; E/F chạm luật nên vẫn cần cả nhóm đồng ý trước khi sửa hợp đồng |
| **G** | Không làm | Rủi ro lệch determinism |

### Đã chốt thêm (PO đồng ý, 2026-11-21)
- **Số liệu sáng tạo:** KHÔNG sửa `game.contract.json`. Đặt trong file riêng `chonoi/creative.contract.json`, chỉ load khi `creative=on`; headless không bao giờ đọc. Vẫn tuân quy tắc "số liệu chỉ đọc từ dữ liệu, không hard-code trong luật". (Thay cho hướng `tuning.creative.*` ở phần nguyên tắc bên dưới.)
- **Giọng điệu:** vui, dí dỏm kiểu miền Tây, vừa phải (nè, dữ, trời ơi), không viết phương ngữ nặng. Câu ngắn, tối đa khoảng 8 từ để toast không che HUD. Sổ tay H dịu hơn, kiểu nhật ký ("Hôm nay bắt được 5 con cá lóc…").

Không còn câu hỏi mở.

## Ba điều kiện (README, "Tự do sáng tạo")
1. **Không phá phần cố định** → mọi ý tưởng đều nằm sau cờ `creative` (mặc định **tắt**). Headless luôn chạy với `creative=off`: không đổi RNG stream, không đổi số liệu trong `game.contract.json`, không thêm trường bắt buộc vào snapshot/kho.
2. **Ghi mục "Sáng tạo của nhóm"** trong README của nhóm (sau khi duyệt).
3. **Lõi đúng trước** → không bắt đầu ý nào trước khi `phase-1` có tag và test xanh. Chỉ 4 người (1 admin), nên chọn ít, rẻ, thuần phần trình bày trước.

## Nguyên tắc kỹ thuật chung
- Lớp **trình bày** (đồ họa, âm thanh, câu chuyện) chỉ nằm trong `chonoi/web/`, đọc snapshot, không đụng luật. Rủi ro với headless = 0.
- Lớp **luật** (cá/món/cơ chế mới) phải đọc số liệu từ file riêng `chonoi/creative.contract.json` (không đụng `game.contract.json`) và chỉ bật khi `creative=on`.
- Asset ngoài chỉ CC0/CC-BY/MIT hoặc tự vẽ/tự tạo bằng code, ghi `CREDITS.md`.

## Danh sách ý tưởng (xếp theo giá trị/chi phí)

| # | Ý tưởng | Nhóm | Mô tả ngắn | Chạm luật? | Công | Rủi ro |
|---|---|---|---|---|---|---|
| A | **Âm thanh Web Audio** | Âm nhạc | Tiếng nước, "tách" khi hái, "bing" khi có món, nhạc nền chợ nổi bằng oscillator (không cần file). Nút tắt tiếng | Không | S | Rất thấp |
| B | **Hiệu ứng & sprite vẽ bằng canvas** | Đồ họa | Bọt khí theo thanh oxy, gợn sóng mặt nước, cá có đuôi quẫy, hơi nước từ bếp, đổi màu trời theo đồng hồ (chiều → tối) | Không | M | Thấp |
| C | **Lời thoại Út Sen & khách** | Câu chuyện | Toast có giọng miền Tây ("Trời ơi, hết hơi rồi!"), khách có tên + một câu khi tới/rời. Chỉ chuỗi hiển thị theo `event` | Không | S | Thấp |
| D | **Bản đồ "Rạch Bần"** | Bản đồ | Một kịch bản gather phụ (`scenario` riêng, bến thứ hai, bóng sung dày hơn). Dùng cơ chế `--scenario` có sẵn, không sửa map mặc định | Qua scenario | M | Thấp |
| E | **Cá Thòi Lòi / Cá Lòng Tong** | Loài cá | 1–2 loài cá mới trong `tuning.creative.fish` (nhanh hơn, giá cao hơn), kèm món mới | Có (cờ) | M | Trung bình |
| F | **Khách khó tính / Cô Ba "ghe bầu"** | Nhân vật | Loại khách mới: kiên nhẫn thấp nhưng tip cao; gọi món theo sở thích | Có (cờ) | M | Trung bình |
| G | **Sự kiện "Nước lớn"** | Cơ chế | Trong gather, sóng đẩy Út Sen trôi nhẹ; có thể bắt buộc đọc thêm tick từ `Streams` riêng | Có (cờ) | L | Cao (dễ lệch RNG) |
| H | **Sổ tay ký ức Út Sen** | Câu chuyện | Mỗi lượt xong ghi một dòng nhật ký (từ dữ liệu kết quả), xem được ở màn kết | Không | S | Thấp |

## Nhân vật mới (PO yêu cầu thêm, 2026-11-21): vợ chồng Bến Tre

Hai nhân vật **hư cấu**, nhập vào luồng sẵn có (C, F, H), không thêm ý tưởng mới.

| Nhân vật | Vai | Tính cách (để viết lời thoại) |
|---|---|---|
| **Anh Jack Bến Tre** | Chủ ghe chở dừa từ Bến Tre ghé chợ nổi; khách quen của quán | Hiền, nói nhiều, hay khoe dừa xiêm; kiên nhẫn cao, tip ít |
| **Chị Thiên An** | Vợ anh Jack, giữ sổ bán dừa trên ghe | Sắc sảo, nói nhanh, cưng chồng mà hay "dợt"; kiên nhẫn thấp, tip cao nếu được phục vụ kịp |

Chỗ nhập vào luồng:
- **C (lời thoại, làm trước):** cặp vợ chồng xuất hiện bằng lời thoại ở bến/quán, ví dụ Jack: "Dừa Bến Tre nè, ngọt dữ nha!"; Thiên An: "Ổng nói hoài, cho tui miếng cá lẹ giùm." Chỉ chuỗi hiển thị theo event, không chạm luật.
- **H (sổ tay, làm trước):** nhật ký có dòng nhắc, ví dụ "Hôm nay anh Jack ghé, chị Thiên An khen cá lóc nướng."
- **F (backlog):** thành loại khách đôi: Jack (kiên nhẫn cao, tip thấp) và Thiên An (kiên nhẫn thấp, tip cao), số liệu nằm trong `chonoi/creative.contract.json`. Chỉ bật khi `creative=on`.
- **Hình vẽ (B):** tự vẽ bằng canvas (ghe chở dừa, nón lá); không dùng ảnh hay hình người thật.

Lưu ý: đây là nhân vật game hư cấu lấy cảm hứng từ miền Tây. Không gắn với người thật hay chuyện đời tư của ai, không dùng ảnh/giọng người thật. Nếu muốn đổi tên để tránh nhầm với người có thật (vd "anh Hai Dừa"), đổi ở một chỗ trong `creative.contract.json`.

## Đề xuất của tôi
**Làm trước (an toàn, thuần UI):** A + B + C + H.
**Làm sau nếu dư giờ ở Phase 3–4:** D (map phụ qua scenario) và E (một loài cá + một món).
**Không làm:** G (rủi ro lệch determinism lớn so với điểm cộng nhỏ ở hạng mục 10 điểm "chất lượng sản phẩm").

Phân công (đề xuất, chờ Sỹ xác nhận; khớp `TEAM.md`): **Đoàn Sỹ Hưng (`hgmdz1210`, module `client/ui` + `qa`)** nhận toàn bộ phần sáng tạo, vì A/B/C/H đều nằm trong `chonoi/web/`. D/E/F chỉ bắt đầu khi A/B/C/H xong và lõi đã xanh; E/F chạm luật nên phối hợp với chủ module sim. Admin soạn `CREDITS.md`. Vẫn phải tắt ở headless và chạy test trước khi đẩy.

## Tiến độ triển khai (nhánh `feature/creative-ui`)
- **A, C, H đã viết** trong `chonoi/web/creative.js` (A âm thanh Web Audio + phím M tắt tiếng; C toast lời thoại gồm Jack/Thiên An; H sổ tay ở màn kết, lưu `localStorage`). **B chưa làm** (cần snapshot thật từ lõi). D/E/F backlog.
- Bật bằng `?creative=1` (vd `http://127.0.0.1:8000/?creative=1`); không có cờ thì `creative.js` không được nạp.
- **Sửa file khung (báo cả nhóm, theo AGENTS.md):** `chonoi/live.py` thêm route `GET /creative.js` (8 dòng, chỉ phục vụ tệp tĩnh; không đổi `/state`, `/input`, sim). `chonoi/web/index.html` thêm 3 dòng: nạp script có điều kiện + 2 lời gọi `window.CREATIVE` (bỏ qua nếu không có).
- Test: `tests/test_creative_serve.py` (phục vụ + `/state` không chứa trường sáng tạo). Cả bộ test xanh (47 + 3 mới).
- **Chưa kiểm bằng mắt/tai trên trình duyệt**: cần người chạy `python3 -m chonoi.live --mode gather` rồi mở `/?creative=1` để nghe và xem toast.

## Mục README dự kiến sau khi duyệt
```
## Sáng tạo của nhóm
Bật bằng `--creative` (live) hoặc `?creative=1` (trình duyệt); headless luôn tắt.
- Âm thanh Web Audio (tắt tiếng được) — chonoi/web/
- Hiệu ứng nước/bọt/hơi bếp — chonoi/web/
- Lời thoại và sổ tay Út Sen — chonoi/web/
- (tùy duyệt) Bản đồ Rạch Bần, cá & món mới
```

## Câu hỏi cho PO
1. Duyệt nhóm nào: chỉ UI (A/B/C/H), hay thêm D/E/F?
2. Cho phép thêm key `tuning.creative.*` vào `game.contract.json` (cần cả nhóm đồng ý) hay giữ sáng tạo hoàn toàn ngoài hợp đồng?
3. Có chủ đề/giọng điệu bắt buộc (miền Tây vui, hay nhẹ nhàng)?

## Việc ghi lại
- Đã tạo worktree lỗi lần đầu (cảnh báo đường dẫn `d:`/`D:`), đã chuyển vào bằng `path`; nhánh đổi tên `worktree-docs-creative-ideas` → `docs/creative-ideas` theo quy ước tên nhánh.
