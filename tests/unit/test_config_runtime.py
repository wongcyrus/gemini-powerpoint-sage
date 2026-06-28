"""Tests for runtime configuration behavior."""

import os
import sys
import types
from unittest.mock import Mock, patch

import pytest

from config.config import Config
from config.constants import EnvironmentVars


class TestConfig:
    """Tests for runtime Config behavior."""

    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create a valid PPTX/PDF pair."""
        pptx_path = tmp_path / "deck.pptx"
        pdf_path = tmp_path / "deck.pdf"
        pptx_path.touch()
        pdf_path.touch()
        return pptx_path, pdf_path

    def test_style_dict_sets_visual_and_speaker_styles(self, temp_files):
        """Config should support separate visual and speaker style definitions."""
        pptx_path, pdf_path = temp_files

        config = Config(
            pptx_path=str(pptx_path),
            pdf_path=str(pdf_path),
            style={"visual_style": "cyberpunk", "speaker_style": "teacher"},
        )

        assert config.visual_style == "cyberpunk"
        assert config.speaker_style == "teacher"
        assert config.style == "cyberpunk"

    def test_apply_env_overrides_sets_progress_retry_and_region(self, temp_files):
        """Config initialization should publish runtime env overrides."""
        pptx_path, pdf_path = temp_files

        with patch.dict(os.environ, {}, clear=True):
            Config(
                pptx_path=str(pptx_path),
                pdf_path=str(pdf_path),
                progress_file="/tmp/progress.json",
                retry_errors=True,
                region="asia-east1",
            )

            assert os.environ[EnvironmentVars.PROGRESS_FILE] == "/tmp/progress.json"
            assert os.environ[EnvironmentVars.RETRY_ERRORS] == "true"
            assert os.environ[EnvironmentVars.GOOGLE_CLOUD_LOCATION] == "asia-east1"

    def test_get_output_dir_uses_custom_output_dir(self, temp_files, tmp_path):
        """Custom output directories should be used directly and created if needed."""
        pptx_path, pdf_path = temp_files
        output_dir = tmp_path / "custom-output"
        config = Config(str(pptx_path), str(pdf_path), output_dir=str(output_dir))

        resolved = config._get_output_dir()

        assert resolved == str(output_dir)
        assert output_dir.exists()

    def test_get_output_dir_uses_style_folder_for_non_professional_styles(self, temp_files):
        """Non-default styles should get their own subfolder under generate/."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path), style="Cyber Punk")

        resolved = config._get_output_dir()

        assert resolved == str(pptx_path.parent / "generate" / "cyber_punk")

    def test_output_paths_and_asset_directories_follow_language_naming(self, temp_files, tmp_path):
        """Derived output names should consistently encode language and artifact type."""
        pptx_path, pdf_path = temp_files
        config = Config(
            str(pptx_path),
            str(pdf_path),
            language="zh-CN",
            output_dir=str(tmp_path / "generated"),
        )

        assert config.output_path.endswith("deck_zh-CN_notes.pptx")
        assert config.output_path_with_visuals.endswith("deck_zh-CN_visuals.pptx")
        assert config.visuals_dir.endswith("deck_zh-CN_visuals")
        assert config.speech_dir.endswith("deck_zh-CN_speech")
        assert config.videos_dir.endswith("deck_zh-CN_videos")
        assert config.video_synthesis_dir.endswith("deck_zh-CN_video_synthesis")

    def test_validate_rejects_missing_pptx(self, temp_files):
        """Validation should fail if the PPTX disappears."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path))
        pptx_path.unlink()

        with pytest.raises(ValueError, match="PPTX file not found"):
            config.validate()

    def test_get_presentation_theme_without_course_id_returns_general_theme(self, temp_files):
        """Configs without a course should use the generic presentation theme."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path))

        assert config.get_presentation_theme() == "General Presentation"

    def test_get_presentation_theme_uses_course_metadata_when_available(self, temp_files):
        """Course metadata should be preferred when the helper module is available."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path), course_id="course-1")

        package = types.ModuleType("presentation_preloader")
        utils_pkg = types.ModuleType("presentation_preloader.utils")
        course_utils = types.ModuleType("presentation_preloader.utils.course_utils")
        course_utils.get_course_config = lambda course_id: {"description": f"Theme for {course_id}"}
        utils_pkg.course_utils = course_utils
        package.utils = utils_pkg

        with patch.dict(
            sys.modules,
            {
                "presentation_preloader": package,
                "presentation_preloader.utils": utils_pkg,
                "presentation_preloader.utils.course_utils": course_utils,
            },
        ):
            assert config.get_presentation_theme() == "Theme for course-1"

    def test_get_presentation_theme_falls_back_when_lookup_fails(self, temp_files):
        """Course IDs should still produce a stable fallback theme on import errors."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path), course_id="course-2")

        import builtins

        real_import = builtins.__import__

        def raising_import(name, *args, **kwargs):
            if name.startswith("presentation_preloader"):
                raise ImportError("boom")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=raising_import):
            assert config.get_presentation_theme() == "Course course-2"

    def test_get_video_synthesis_config_uses_default_and_custom_manager_paths(self, temp_files):
        """Video synthesis config should delegate to the manager for both default and custom dictionaries."""
        pptx_path, pdf_path = temp_files
        video_module = types.ModuleType("core.domain.video_synthesis")
        video_module.VideoConfig = object
        manager_module = types.ModuleType("services.video_synthesis.video_config_manager")
        manager = Mock()
        manager.create_default_config.return_value = {"mode": "default"}
        manager.create_config_from_dict.return_value = {"mode": "custom"}
        manager_module.VideoConfigManager = Mock(return_value=manager)

        with patch.dict(
            sys.modules,
            {
                "core.domain.video_synthesis": video_module,
                "services.video_synthesis.video_config_manager": manager_module,
            },
        ):
            default_config = Config(str(pptx_path), str(pdf_path)).get_video_synthesis_config()
            custom_config = Config(
                str(pptx_path),
                str(pdf_path),
                video_synthesis_config={"fps": 30},
            ).get_video_synthesis_config()

        assert default_config == {"mode": "default"}
        assert custom_config == {"mode": "custom"}

    def test_repr_includes_key_runtime_fields(self, temp_files):
        """repr should summarize the main runtime configuration knobs."""
        pptx_path, pdf_path = temp_files
        config = Config(str(pptx_path), str(pdf_path), language="ja", style="minimalist")

        rendered = repr(config)

        assert "language=ja" in rendered
        assert "visual_style=minimalist" in rendered
        assert "enable_video_synthesis=False" in rendered
