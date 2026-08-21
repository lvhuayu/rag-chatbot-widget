from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicBetaSiteTests(unittest.TestCase):
    def test_homepage_has_one_free_beta_offer(self):
        homepage = (ROOT / "public" / "index.html").read_text(encoding="utf-8")

        self.assertIn("公开 Beta，现有功能全部免费", homepage)
        self.assertIn("Public Beta — all current features are free", homepage)
        self.assertEqual(homepage.count('<article class="pricing-card'), 1)
        self.assertNotIn("¥99", homepage)
        self.assertNotIn("pricing_pro_name", homepage)
        self.assertNotIn("pricing_enterprise_name", homepage)
        self.assertNotIn("模拟支付", homepage)

    def test_public_beta_chat_usage_is_not_plan_limited(self):
        backend = (ROOT / "backend" / "rag_server_prisma.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('"public-beta": None', backend)


if __name__ == "__main__":
    unittest.main()
