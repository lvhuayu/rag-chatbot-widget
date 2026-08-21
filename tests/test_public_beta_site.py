from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicBetaSiteTests(unittest.TestCase):
    def test_homepage_publishes_beta_and_future_pricing(self):
        homepage = (ROOT / "public" / "index.html").read_text(encoding="utf-8")

        self.assertIn("公测免费，价格透明", homepage)
        self.assertIn("2026 年 10 月 31 日前免费", homepage)
        self.assertIn("创始用户首年 ¥49/月", homepage)
        self.assertIn("pricing_free_name:'基础版'", homepage)
        self.assertIn("pricing_pro_name:'专业版'", homepage)
        self.assertIn("pricing_enterprise_name:'企业版'", homepage)
        self.assertIn("<strong>¥99</strong>", homepage)
        self.assertIn("<strong>¥0</strong>", homepage)
        self.assertEqual(homepage.count('<article class="pricing-card'), 3)
        self.assertNotIn("模拟支付", homepage)
        self.assertNotIn("立即升级", homepage)

        pricing_section = homepage.split("<!-- Pricing -->", 1)[1].split(
            "<!-- CTA -->", 1
        )[0]
        for english_label in (
            "PUBLIC BETA",
            "Beta",
            "Free",
            "Professional",
            "Enterprise",
            "RAG",
            "SLA",
        ):
            self.assertNotIn(english_label, pricing_section)

    def test_public_beta_chat_usage_is_not_plan_limited(self):
        backend = (ROOT / "backend" / "rag_server_prisma.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('"public-beta": None', backend)


if __name__ == "__main__":
    unittest.main()
