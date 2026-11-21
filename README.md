# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python -m unittest discover -s tests -v        # smoke test
python -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Chạy game

Cần Python 3.10 trở lên và một trình duyệt hiện đại. Không cần cài gói.

```bash
git clone https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi
python3 -m chonoi.live --mode day   # Windows: python -m chonoi.live --mode day
```

Mở địa chỉ được in ra. Điều khiển: **WASD** hoặc mũi tên để di chuyển, **E** để hái, cập bến, nấu, lấy món và phục vụ, **Space** để bắt cá, **Esc** hoặc **P** để tạm dừng, **C** để bật tương phản cao. Trong Shop: **1**, **2** để mua, **Enter** để rời chợ. Ở chế độ `gather` và `quan`, **R** để chơi lại.

## Kiểm tra và đo hiệu năng

Các ca kiểm tra sử dụng Python và thư viện chuẩn. Trên Windows, đặt `$env:PYTHONPATH = "tests;."` rồi chạy `python -m unittest discover -s tests -v`.

```bash
PYTHONPATH=tests:. python -m unittest discover -s tests -v
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 600 --out quan.jsonl
python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl
python -m chonoi.bench --seed 42 --duration 30 --out bench.json
python -m chonoi.soak --seed 7 --days 10 --out soak.json
```

Bench cần Chrome, Chromium hoặc Edge. Dùng `CHONOI_BROWSER` hoặc `--browser` để chỉ định đường dẫn. FPS phụ thuộc máy, trình duyệt và giới hạn tần số của chế độ headless.

Các lệnh trong manifest gọi `python`. Trên Linux hoặc macOS chỉ có `python3`, chạy `python3 -m venv --without-pip .venv` rồi `source .venv/bin/activate` trước khi chạy bộ test.

## Demo một ngày

1. Mở `--mode day`, chọn **Chơi** và vào ca Lặn. Hái rau bằng **E** hoặc bắt cá bằng **Space**, rồi quay về bến và nhấn **E** để chuyển nguyên liệu sang quán.
2. Khi khách đặt món, đứng gần bếp và nhấn **E** để nấu. Nhấn **E** lần nữa để lấy món, rồi đến bàn đúng khách và nhấn **E** để phục vụ. Có thể dùng **Esc** hoặc **P** để tạm dừng và xem HUD.
3. Sau ca Quán, tiếp tục qua màn kết quả đến Shop. Xem các nâng cấp và nhấn **Enter** để đóng Shop, sang ngày tiếp theo. Nhấn **C** trong lúc chơi để kiểm tra tương phản cao.

## Sáng tạo của nhóm

Chi tiết và trạng thái duyệt: [`docs/creative-ideas.md`](docs/creative-ideas.md). Các mục dưới nằm sau cờ `creative` (mặc định tắt); headless luôn tắt.

- **Giao diện chợ nổi (đã làm):** menu, các màn trong ngày và HUD vẽ theo ghe miền Tây, có cây bẹo treo nguyên liệu. Đây là giao diện bắt buộc của Phase 2 nên luôn bật trên trình duyệt; toàn bộ nằm ở `chonoi/web/`, headless không dùng. Chơi: `python -m chonoi.live --mode day`.
- **Làm trước (đã duyệt):** A âm thanh Web Audio · B hiệu ứng nước/bọt/hơi bếp · C lời thoại Út Sen và khách · H sổ tay ký ức Út Sen (đều chỉ ở `chonoi/web/`).
- **Backlog (đã duyệt, làm sau):** D bản đồ "Rạch Bần" · E cá và món mới · F khách khó tính.
- **Nhân vật Bến Tre (hư cấu):** anh Jack Bến Tre và chị Thiên An (vợ anh), xuất hiện qua lời thoại C, sổ tay H và khách đôi F.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
