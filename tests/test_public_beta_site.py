from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicBetaSiteTests(unittest.TestCase):
    def test_homepage_publishes_beta_and_future_pricing(self):
        homepage = (ROOT / "public" / "index.html").read_text(encoding="utf-8")

        self.assertIn("2026 年 10 月 31 日前现有功能全部免费", homepage)
        self.assertIn("创始用户首年 ¥49/月", homepage)
        self.assertIn("<strong>¥99</strong>", homepage)
        self.assertIn("<strong>¥0</strong>", homepage)
        self.assertEqual(homepage.count('<article class="pricing-card'), 3)
        self.assertNotIn("模拟支付", homepage)
        self.assertNotIn("立即升级", homepage)

    def test_public_beta_chat_usage_is_not_plan_limited(self):
        backend = (ROOT / "backend" / "rag_server_prisma.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('"public-beta": None', backend)


if __name__ == "__main__":
    unittest.main()
