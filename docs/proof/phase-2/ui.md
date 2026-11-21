# Kiểm chứng giao diện vòng Ngày

Mã nguồn `330dde9`, Windows x64, Python 3.13.18 và Chrome 158.0.8127.37 headless ở viewport 1280×720. Mở `python -m chonoi.live --mode day --days 5 --scenario <file>` với scenario trong [log](ui-run.json). Fixture rút ngắn timer Gather và Quán để kiểm cả năm Ngày. Chrome chạy ngoài sandbox vì lần chạy trong sandbox lỗi khởi tạo GPU.

- Mở [menu](ui-menu.png), bấm Thoát, quay lại menu rồi bấm Chơi.
- Đi qua [DayIntro](ui-day-intro.png), [Lặn](ui-gather-hud.png), [EveningIntro](ui-evening-intro.png), [Quán](ui-quan-hud.png), [DayResult](ui-day-result.png) và [Shop](ui-shop.png) bằng các nút trên giao diện. Lặp đến [Summary](ui-summary.png) sau Ngày 5 và quay về menu. Bộ test `test_p2_live_day` còn kiểm các màn chờ giữ sim và không nhận thao tác cũ.
- Mở [pause](ui-pause.png) trong Shop bằng Esc sau khoảng chặn phím khi vừa mở màn. Hai lần đọc `/state` cách 600 ms giữ nguyên `phase_tick` và `time_left_ticks` (559). Nút Tiếp tục mở lại Shop.
- Đo nhịp `requestAnimationFrame` trong 1,2 giây mỗi cảnh. Lặn 60,00 FPS, Quán 60,00 FPS và không có ngoại lệ JavaScript. HUD dùng chữ sans-serif, cỡ tối thiểu 18 px theo `MIN_TEXT` và CSS. Ảnh Quán chụp đầu ca nên chưa hiện khách hay bếp đang nấu. Đã rà hàm vẽ HUD để kiểm nhãn món, kiên nhẫn và tiến độ bếp.

Đây là kiểm chứng sau hạn lab. Các ảnh lấy trực tiếp từ trình duyệt trong cùng lần chạy với log.
