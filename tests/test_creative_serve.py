"""Lớp sáng tạo (creative.js) chỉ là tệp tĩnh của trình duyệt: phải được phục vụ, và index.html chỉ nạp nó khi ?creative=1."""
import os
import unittest
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer, WEB_DIR


class CreativeServeTest(unittest.TestCase):
    def test_creative_js_served_and_gated(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            with urllib.request.urlopen(base + "/creative.js", timeout=5) as r:
                self.assertEqual(r.status, 200)
                self.assertIn("javascript", r.headers["Content-Type"])
                self.assertIn(b"window.CREATIVE", r.read())
            with urllib.request.urlopen(base + "/", timeout=5) as r:
                html = r.read().decode("utf-8")
            self.assertIn("creative=1", html)  # chỉ nạp khi có cờ
        finally:
            server.stop()

    def test_state_has_no_creative_fields(self):
        """Sáng tạo không được đổi snapshot/headless: /state không chứa trường 'creative'."""
        tuning = load_contract()["tuning"]
        g = LiveGame("gather", tuning, {}, 1)
        self.assertNotIn(b"creative", g.state_json())
        self.assertTrue(os.path.exists(os.path.join(WEB_DIR, "creative.js")))


if __name__ == "__main__":
    unittest.main()
