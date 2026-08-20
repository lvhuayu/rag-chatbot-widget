import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentContractTests(unittest.TestCase):
    def test_release_is_immutable_and_has_rollback_gates(self):
        workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("workflow_run:", workflow)
        self.assertIn("ref: ${{ env.RELEASE_SHA }}", workflow)
        self.assertIn("EXPECTED_HEAD_SHA", workflow)
        self.assertIn("head_repository", workflow)
        self.assertIn("sha256sum --check", workflow)
        self.assertIn("requirements.lock", workflow)
        self.assertIn("rollback()", workflow)
        self.assertIn("/health/ready", workflow)
        self.assertIn("https://lingwenai.cn/chatbot.js", workflow)
        self.assertIn("':(exclude)backend/rag_database.db'", workflow)
        self.assertNotIn("git pull", workflow)
        self.assertNotIn("apt-get", workflow)

    def test_production_dependencies_are_fully_pinned(self):
        lock_lines = (ROOT / "backend" / "requirements.lock").read_text(
            encoding="utf-8"
        ).splitlines()
        requirements = [
            line
            for line in lock_lines
            if line and not line.startswith((" ", "#", "-"))
        ]

        self.assertGreater(len(requirements), 20)
        self.assertTrue(all("==" in requirement for requirement in requirements))

    def test_health_contract_exposes_live_and_ready_endpoints(self):
        source = (ROOT / "backend" / "rag_server_prisma.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        paths = {
            decorator.args[0].value
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
        }

        self.assertIn("/health/live", paths)
        self.assertIn("/health/ready", paths)


if __name__ == "__main__":
    unittest.main()
