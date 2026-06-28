"""Tests for Google Cloud project rotation utilities."""

from utils.project_rotation import ProjectRotator


class TestProjectRotator:
    """Tests for project rotation behavior."""

    def test_load_projects_prefers_multi_project_env(self, monkeypatch):
        """Comma-separated projects should be parsed into the rotation pool."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECTS", "proj-a, proj-b ,proj-c")
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        rotator = ProjectRotator()

        assert rotator.get_project_count() == 3
        assert rotator.get_next_project() == "proj-a"
        assert rotator.get_next_project() == "proj-b"
        assert rotator.get_next_project() == "proj-c"

    def test_load_projects_falls_back_to_single_project_env(self, monkeypatch):
        """A single project env var should still provide a one-item rotation pool."""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECTS", raising=False)
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "solo-project")
        rotator = ProjectRotator()

        assert rotator.get_project_count() == 1
        assert rotator.get_next_project() == "solo-project"
        assert rotator.get_current_project() == "solo-project"

    def test_get_next_project_returns_none_when_unconfigured(self, monkeypatch):
        """No configuration should yield no active project."""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECTS", raising=False)
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        rotator = ProjectRotator()

        assert rotator.get_project_count() == 0
        assert rotator.get_next_project() is None

    def test_reset_rotation_restarts_from_first_project(self, monkeypatch):
        """Reset should move the rotation pointer back to the first project."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECTS", "proj-a,proj-b")
        rotator = ProjectRotator()
        rotator.get_next_project()
        rotator.get_next_project()

        rotator.reset_rotation()

        assert rotator.get_current_project() == "proj-a"
        assert rotator.get_next_project() == "proj-a"

    def test_reload_projects_picks_up_environment_changes(self, monkeypatch):
        """Reload should re-read the current environment and replace the project list."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECTS", "one,two")
        rotator = ProjectRotator()
        assert rotator.get_project_count() == 2

        monkeypatch.setenv("GOOGLE_CLOUD_PROJECTS", "three")
        rotator._initialized = False
        rotator._ensure_initialized()

        assert rotator.get_project_count() == 1
        assert rotator.get_next_project() == "three"
