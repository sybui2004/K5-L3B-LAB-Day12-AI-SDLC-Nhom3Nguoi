# Plan — Thành viên 1: `sim/gather` + Integrator/Release

Spec: [../../spec/phase-1/gather.md](../../spec/phase-1/gather.md) · Hợp đồng chung: [../../spec/phase-1/README.md](../../spec/phase-1/README.md)
Nhánh: `feature/gather-rules`

## Bước 0 — Kickoff (0:00–0:15)
- [ ] Điền `TEAM.md` (tên, handle, thỏa thuận). `team_size` đã đặt = 3 (clarify #6).
- [ ] Chép mục 3 của spec chung vào `docs/contracts/README.md` sau khi cả nhóm gật (bảng sự kiện, giao diện UI).

## Bước 1 — Hoàn tất gather (0:15–0:30)
- [ ] Đọc lại diff `chonoi/sim/gather.py` theo thứ tự bước trong spec (oxy theo d cuối bước, bến trước hái, hồi chiêu chỉ khi trúng).
- [ ] Nhờ PO (TV2) chốt clarify #1–5; nếu PRD-0 nói khác ⇒ sửa luật, không sửa test cho xanh.
- [ ] Chạy `PYTHONPATH=tests:. python -m unittest tests.test_gather_rules tests.test_smoke_p1 -v`.
- [ ] Chạy headless seed 1 hai lần, `cmp` hai file.
- [ ] Commit `gather.py` + `tests/test_gather_rules.py` + `docs/clarify.md`, ghi kết quả test trong mô tả.

## Bước 2 — Quan lát 4 (0:30–0:45)
Xem [quan-kitchen.md](quan-kitchen.md).

## Bước cuối — Tích hợp & tag (0:45–1:00)
- [ ] Gộp các nhánh vào `main` theo thứ tự: gather → khung quan (TV2) → lát 3 → lát 4 → UI/QA.
- [ ] Chạy skill `phase-check` (TV3 viết) hoặc tay: unittest, `python tools/check_team.py`, headless 2 mode.
- [ ] `git tag phase-1 && git push origin phase-1` trước 1:00.

## Dự phòng
Nếu TV2 vướng > 10 phút ở lát 3: TV1 nhận `_spawn_customer`, TV2 chuyển sang scenario validation.
