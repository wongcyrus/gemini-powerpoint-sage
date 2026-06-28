"""Tests for repository verification scripts."""

from io import StringIO
from types import ModuleType
import builtins
import sys

import utils.verify_dependencies as verify_dependencies
import utils.verify_tests as verify_tests


class TestVerifyDependencies:
    """Tests for dependency verification helpers."""

    def test_check_imports_reports_core_and_optional_packages(self, monkeypatch, capsys):
        """Import checks should report installed and missing packages."""
        original_import = builtins.__import__
        installed = {
            "google.adk.agents",
            "google.genai",
            "pptx",
            "fitz",
            "PIL",
            "dotenv",
            "yaml",
            "fastmcp",
        }

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "pydantic":
                raise ImportError("No module named pydantic")
            if name in installed:
                return ModuleType(name.split(".")[0])
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        results = verify_dependencies.check_imports()
        output = capsys.readouterr().out

        assert len(results) == 9
        assert results[0] == ("google-adk", True, "OK")
        assert results[1] == ("google-genai", True, "OK")
        assert results[-2] == ("fastmcp", True, "OK")
        assert results[-1] == ("pydantic", False, "Not installed (optional)")
        assert "Checking core dependencies" in output
        assert "Checking optional dependencies" in output

    def test_check_versions_reports_installed_and_missing_packages(self, monkeypatch, capsys):
        """Version reporting should print installed and missing distributions."""
        fake_pkg_resources = ModuleType("pkg_resources")

        class DistributionNotFound(Exception):
            pass

        class FakeDistribution:
            def __init__(self, version):
                self.version = version

        versions = {
            "google-adk": "1.2.3",
            "python-pptx": "0.6.23",
        }

        def get_distribution(package):
            if package not in versions:
                raise DistributionNotFound(package)
            return FakeDistribution(versions[package])

        fake_pkg_resources.DistributionNotFound = DistributionNotFound
        fake_pkg_resources.get_distribution = get_distribution
        monkeypatch.setitem(sys.modules, "pkg_resources", fake_pkg_resources)

        verify_dependencies.check_versions()
        output = capsys.readouterr().out

        assert "google-adk" in output
        assert "1.2.3" in output
        assert "python-pptx" in output
        assert "NOT INSTALLED" in output

    def test_main_returns_zero_when_all_core_dependencies_are_present(self, monkeypatch, capsys):
        """Main should succeed when all core dependencies are available."""
        monkeypatch.setattr(
            verify_dependencies,
            "check_imports",
            lambda: [
                ("google-adk", True, "OK"),
                ("google-genai", True, "OK"),
                ("python-pptx", True, "OK"),
                ("pymupdf", True, "OK"),
                ("Pillow", True, "OK"),
                ("python-dotenv", True, "OK"),
                ("pyyaml", True, "OK"),
                ("fastmcp", False, "Not installed (optional)"),
                ("pydantic", True, "OK"),
            ],
        )
        monkeypatch.setattr(verify_dependencies, "check_versions", lambda: None)

        assert verify_dependencies.main() == 0
        output = capsys.readouterr().out

        assert "Core dependencies: 7/7 installed" in output
        assert "Optional dependencies: 1/2 installed" in output
        assert "All core dependencies are installed" in output

    def test_main_returns_one_when_core_dependencies_are_missing(self, monkeypatch, capsys):
        """Main should fail when any core dependency is missing."""
        monkeypatch.setattr(
            verify_dependencies,
            "check_imports",
            lambda: [
                ("google-adk", True, "OK"),
                ("google-genai", True, "OK"),
                ("python-pptx", False, "missing"),
                ("pymupdf", True, "OK"),
                ("Pillow", True, "OK"),
                ("python-dotenv", True, "OK"),
                ("pyyaml", True, "OK"),
                ("fastmcp", True, "OK"),
                ("pydantic", True, "OK"),
            ],
        )
        monkeypatch.setattr(verify_dependencies, "check_versions", lambda: None)

        assert verify_dependencies.main() == 1
        output = capsys.readouterr().out

        assert "Core dependencies: 6/7 installed" in output
        assert "Some core dependencies are missing" in output


class TestVerifyTests:
    """Tests for test verification helpers."""

    def test_check_module_returns_syntax_ok_for_valid_file(self, tmp_path):
        """Valid Python files should report syntax success."""
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("def test_example():\n    return True\n", encoding="utf-8")

        success, message = verify_tests.check_module("sample", str(test_file))

        assert success is True
        assert message == "Syntax OK"

    def test_check_module_reports_syntax_error_for_invalid_file(self, tmp_path):
        """Invalid Python files should report syntax errors."""
        test_file = tmp_path / "test_broken.py"
        test_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

        success, message = verify_tests.check_module("broken", str(test_file))

        assert success is False
        assert "Syntax error" in message

    def test_main_reports_successful_verification(self, monkeypatch, capsys):
        """Main should report a fully passing verification run."""
        contents = {
            "tests/unit/test_constants.py": "def test_one():\n    pass\n",
            "tests/unit/test_error_handling.py": "def test_two():\n    pass\n",
            "tests/unit/test_agent_manager.py": "def test_three():\n    pass\n",
            "tests/unit/test_translation_service.py": "def test_four():\n    pass\n",
            "tests/unit/test_video_service.py": "def test_five():\n    pass\n",
            "tests/unit/test_context_service.py": "def test_six():\n    pass\n",
            "tests/unit/test_file_service.py": "def test_seven():\n    pass\n",
            "tests/unit/test_notes_generator.py": "def test_eight():\n    pass\n",
            "tests/integration/test_workflow.py": "def test_nine():\n    pass\n",
        }

        def fake_check_module(module_name, file_path):
            return True, "Syntax OK"

        def fake_open(file_path, mode="r", encoding=None):
            return StringIO(contents[file_path])

        monkeypatch.setattr(verify_tests, "check_module", fake_check_module)
        monkeypatch.setattr(builtins, "open", fake_open)

        assert verify_tests.main() == 0
        output = capsys.readouterr().out

        assert "Results: 9 passed, 0 failed" in output
        assert "Total test functions: 9" in output

    def test_main_reports_failures(self, monkeypatch, capsys):
        """Main should fail when any file verification fails."""
        contents = {
            "tests/unit/test_constants.py": "def test_one():\n    pass\n",
            "tests/unit/test_error_handling.py": "def test_two():\n    pass\n",
            "tests/unit/test_agent_manager.py": "def test_three():\n    pass\n",
            "tests/unit/test_translation_service.py": "def test_four():\n    pass\n",
            "tests/unit/test_video_service.py": "def test_five():\n    pass\n",
            "tests/unit/test_context_service.py": "def test_six():\n    pass\n",
            "tests/unit/test_file_service.py": "def test_seven():\n    pass\n",
            "tests/unit/test_notes_generator.py": "def test_eight():\n    pass\n",
            "tests/integration/test_workflow.py": "def test_nine():\n    pass\n",
        }

        def fake_check_module(module_name, file_path):
            return file_path != "tests/unit/test_video_service.py", "Syntax OK"

        def fake_open(file_path, mode="r", encoding=None):
            return StringIO(contents[file_path])

        monkeypatch.setattr(verify_tests, "check_module", fake_check_module)
        monkeypatch.setattr(builtins, "open", fake_open)

        assert verify_tests.main() == 1
        output = capsys.readouterr().out

        assert "Results: 8 passed, 1 failed" in output
        assert "Total test functions: 9" in output
