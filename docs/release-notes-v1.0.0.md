# Quán Ăn Chợ Nổi v1.0.0

- Phase 1 mở hai chế độ Lặn và Quán. Út Sen hái rau, bắt cá, nấu món và phục vụ khách.
- Phase 2 nối Lặn → Quán → Shop, thêm sáu nguyên liệu, cá bơi và Cá Sấu Năm Chèo.
- Phase 3 chuyển sang kho cá thể có độ tươi. Độ tươi nguyên liệu ảnh hưởng giá món và hàng ươn không dùng để nấu. File kho kiểu đếm cần được xuất lại.
- Phase 4 thêm ba cảnh báo, tương phản cao, đo hiệu năng trình duyệt và mô phỏng độ bền qua Test Contract v1.3.

## Chạy game

```bash
git clone https://github.com/sybui2004/K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom3Nguoi
python3 -m chonoi.live --mode day
```

Mở địa chỉ in trên terminal. Nhấn **C** để bật tương phản cao. Cần Python 3.10 trở lên và một trình duyệt hiện đại.

```bash
PYTHONPATH=tests:. python -m unittest discover -s tests -v
python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl
python -m chonoi.bench --seed 42 --duration 30 --out bench.json
python -m chonoi.soak --seed 7 --days 10 --out soak.json
```

## Giới hạn đã biết

Bench cần Chrome, Chromium hoặc Edge. FPS phụ thuộc máy và trình duyệt. Các lệnh kiểm thử cần `python` trên PATH. Trên Linux hoặc macOS chỉ có `python3`, chạy `python3 -m venv --without-pip .venv` rồi `source .venv/bin/activate` trước khi chạy test.

## Thành viên

Bùi Thái Sỹ (Integrator/Release), Đồng Hữu Nguyên Khoa (PO), Đoàn Sỹ Hưng (QA lead) và Sang Phan (quản trị repo).
