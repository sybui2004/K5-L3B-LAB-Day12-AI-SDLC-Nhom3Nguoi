"""Test bộ đo hiệu năng bench_cmd (Phase 4 Lát A).

Kiểm tra:
- bench_stats(frame_ms): tính avg_fps, p1_low_fps, frames, measured_s (số thô); lỗi khi dãy rỗng.
- find_browser(explicit): ưu tiên explicit -> CHONOI_BROWSER -> PATH (shutil.which) -> chuẩn hệ thống; trả None nếu không tìm thấy.
- main(argv): mã thoát 2 (đối số thiếu/sai), mã 3 (không có trình duyệt, không ghi --out).
- test tích hợp thật: chạy khi có trình duyệt (@unittest.skipUnless(find_browser(), ...)).
"""

import json
import math
import os
import shutil
import tempfile
import unittest
from unittest import mock

from helpers import ROOT, Workdir
from chonoi.bench import bench_stats, find_browser, main


class TestBenchStats(unittest.TestCase):
    def test_formula_with_outlier(self):
        """(a) bench_stats([16.0]*100 + [50.0]): frames=101, k=2, p1_low_fps ~ 30.30, avg_fps = 101/(sum/1000)."""
        frame_ms = [16.0] * 100 + [50.0]
        res = bench_stats(frame_ms)

        expected_keys = {"avg_fps", "p1_low_fps", "frames", "measured_s"}
        self.assertEqual(set(res.keys()), expected_keys)

        self.assertEqual(res["frames"], 101)
        expected_measured_s = sum(frame_ms) / 1000.0  # 1.65 s
        self.assertAlmostEqual(res["measured_s"], expected_measured_s, places=7)

        expected_avg_fps = 101.0 / expected_measured_s  # 101 / 1.65 ~ 61.2121
        self.assertAlmostEqual(res["avg_fps"], expected_avg_fps, places=7)

        # k = max(1, ceil(0.01 * 101)) = 2. Hai khung chậm nhất: 50.0 và 16.0
        mean_top2_s = ((50.0 + 16.0) / 2.0) / 1000.0
        expected_p1_low = 1.0 / mean_top2_s  # ~ 30.3030
        self.assertAlmostEqual(res["p1_low_fps"], expected_p1_low, places=7)

        # Giá trị thô chưa làm tròn (không bằng số đã làm tròn 2 chữ số)
        self.assertNotEqual(res["avg_fps"], round(res["avg_fps"], 2))
        self.assertNotEqual(res["p1_low_fps"], round(res["p1_low_fps"], 2))

    def test_single_frame_k_equals_one(self):
        """(b) frames=1 => k=1."""
        res = bench_stats([20.0])
        self.assertEqual(res["frames"], 1)
        self.assertAlmostEqual(res["measured_s"], 0.02)
        self.assertAlmostEqual(res["avg_fps"], 50.0)
        self.assertAlmostEqual(res["p1_low_fps"], 50.0)

    def test_empty_list_raises_value_error(self):
        """(c) dãy rỗng => ValueError."""
        with self.assertRaises(ValueError):
            bench_stats([])

    def test_k_formula_various_lengths(self):
        """(d) k = max(1, ceil(0.01 * frames)) với độ dài 50, 100, 101, 250."""
        # frames = 50 => ceil(0.5) = 1 => k = 1
        res_50 = bench_stats([10.0] * 49 + [100.0])
        self.assertEqual(res_50["frames"], 50)
        self.assertAlmostEqual(res_50["p1_low_fps"], 1.0 / (100.0 / 1000.0))  # 10.0

        # frames = 100 => ceil(1.0) = 1 => k = 1
        res_100 = bench_stats([10.0] * 99 + [100.0])
        self.assertEqual(res_100["frames"], 100)
        self.assertAlmostEqual(res_100["p1_low_fps"], 1.0 / (100.0 / 1000.0))  # 10.0

        # frames = 101 => ceil(1.01) = 2 => k = 2
        res_101 = bench_stats([10.0] * 99 + [50.0, 100.0])
        self.assertEqual(res_101["frames"], 101)
        mean_101 = ((100.0 + 50.0) / 2.0) / 1000.0
        self.assertAlmostEqual(res_101["p1_low_fps"], 1.0 / mean_101)  # 1000 / 75 ~ 13.333

        # frames = 250 => ceil(2.5) = 3 => k = 3
        res_250 = bench_stats([10.0] * 247 + [60.0, 80.0, 100.0])
        self.assertEqual(res_250["frames"], 250)
        mean_250 = ((100.0 + 80.0 + 60.0) / 3.0) / 1000.0
        self.assertAlmostEqual(res_250["p1_low_fps"], 1.0 / mean_250)  # 1000 / 80 = 12.5


class TestFindBrowser(unittest.TestCase):
    def test_explicit_existing_file(self):
        """explicit trỏ file tồn tại thì được trả về ngay."""
        with tempfile.NamedTemporaryFile() as tmp:
            self.assertEqual(find_browser(explicit=tmp.name), tmp.name)

    def test_env_var_existing_file(self):
        """(e) CHONOI_BROWSER trỏ file tồn tại thì được trả về."""
        with tempfile.NamedTemporaryFile() as tmp:
            with mock.patch.dict(os.environ, {"CHONOI_BROWSER": tmp.name}):
                self.assertEqual(find_browser(), tmp.name)

    def test_browser_not_found_returns_none(self):
        """(e) CHONOI_BROWSER trỏ file không tồn tại + PATH rỗng + which None => None."""
        with mock.patch.dict(os.environ, {"CHONOI_BROWSER": "/nonexistent/browser/binary", "PATH": ""}):
            with mock.patch("shutil.which", return_value=None):
                with mock.patch("os.path.isfile", return_value=False), \
                     mock.patch("os.path.exists", return_value=False):
                    self.assertIsNone(find_browser())

    def test_shutil_which_search_candidates(self):
        """shutil.which tìm theo thứ tự các trình duyệt hỗ trợ."""
        with mock.patch.dict(os.environ, {"CHONOI_BROWSER": ""}):
            with mock.patch("os.path.isfile", return_value=False):
                with mock.patch("shutil.which", side_effect=lambda name: f"/bin/{name}" if name == "chromium" else None):
                    self.assertEqual(find_browser(), "/bin/chromium")


class TestBenchCLI(unittest.TestCase):
    def test_bad_or_missing_arguments_exit_2(self):
        """(f) CLI main: thiếu --seed/--duration/--out, --duration 0 hoặc âm, --seed không phải số => mã 2."""
        cases = [
            [],  # thiếu hết
            ["--duration", "10", "--out", "bench.json"],  # thiếu --seed
            ["--seed", "42", "--out", "bench.json"],  # thiếu --duration
            ["--seed", "42", "--duration", "10"],  # thiếu --out
            ["--seed", "42", "--duration", "0", "--out", "bench.json"],  # duration == 0
            ["--seed", "42", "--duration", "-5", "--out", "bench.json"],  # duration âm
            ["--seed", "not_an_int", "--duration", "10", "--out", "bench.json"],  # seed không phải int
            ["--seed", "42", "--duration", "not_a_num", "--out", "bench.json"],  # duration không phải số
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertEqual(main(argv), 2)

    def test_no_browser_patch_find_browser_exit_3_no_out(self):
        """(g) main khi không có trình duyệt (patch find_browser trả None) => mã 3 và file --out KHÔNG được tạo."""
        with Workdir() as w:
            out_file = w.path("out_nobrowser1.json")
            with mock.patch("chonoi.bench.find_browser", return_value=None):
                code = main(["--seed", "1", "--duration", "2", "--out", out_file])
                self.assertEqual(code, 3)
                self.assertFalse(os.path.exists(out_file), "Không được tạo file --out khi mã 3")

    def test_no_browser_env_and_which_exit_3_no_out(self):
        """(g) main khi CHONOI_BROWSER sai + which None => mã 3 và file --out KHÔNG được tạo."""
        with Workdir() as w:
            out_file = w.path("out_nobrowser2.json")
            with mock.patch.dict(os.environ, {"CHONOI_BROWSER": "/nonexistent/path/browser", "PATH": ""}):
                with mock.patch("shutil.which", return_value=None):
                    with mock.patch("os.path.isfile", return_value=False), \
                         mock.patch("os.path.exists", return_value=False):
                        code = main(["--seed", "1", "--duration", "2", "--out", out_file])
                        self.assertEqual(code, 3)
                        self.assertFalse(os.path.exists(out_file), "Không được tạo file --out khi mã 3")


class TestBenchIntegration(unittest.TestCase):
    @unittest.skipUnless(find_browser(), "Cần trình duyệt để chạy test tích hợp bench")
    def test_real_browser_integration(self):
        """(h) test tích hợp thật (--duration 2 --warmup 1, file đủ đúng 5 khóa số, frames > 0, thoát 0)."""
        with Workdir() as w:
            out_path = w.path("bench.json")
            code = main(["--seed", "42", "--duration", "2", "--warmup", "1", "--out", out_path])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(out_path), "File --out phải được tạo")

            with open(out_path, encoding="utf-8") as f:
                data = json.load(f)

            # Đúng 5 khóa theo thứ tự avg_fps, p1_low_fps, frames, measured_s, load_ms
            expected_keys = ["avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"]
            self.assertEqual(list(data.keys()), expected_keys)

            # Kiểu dữ liệu và định dạng làm tròn
            self.assertIsInstance(data["frames"], int)
            self.assertNotIsInstance(data["frames"], bool)
            self.assertIsInstance(data["load_ms"], int)
            self.assertNotIsInstance(data["load_ms"], bool)

            for k in ("avg_fps", "p1_low_fps", "measured_s"):
                self.assertIsInstance(data[k], (int, float))
                self.assertEqual(round(data[k], 2), data[k], f"{k} phải được làm tròn 2 chữ số")

            # Số liệu hợp lệ
            self.assertGreater(data["frames"], 0)
            self.assertGreater(data["measured_s"], 0)
            self.assertGreater(data["avg_fps"], 0)
            self.assertGreater(data["p1_low_fps"], 0)
            self.assertGreaterEqual(data["load_ms"], 0)


if __name__ == "__main__":
    unittest.main()
