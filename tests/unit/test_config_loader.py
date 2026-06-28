"""Tests for config loading and processor config routing."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.input_scanner import FileSet
from application.unified_processor import UnifiedProcessor
from config.config_loader import ConfigFileLoader


class TestConfigFileLoader:
    """Tests for config path resolution and CLI merges."""

    def test_load_from_file_resolves_style_config_relative_to_repo_root(self, tmp_path):
        """Style configs under styles/ should resolve paths relative to the repo root."""
        repo_root = tmp_path / "repo"
        styles_dir = repo_root / "styles"
        notes_dir = repo_root / "notes"
        styles_dir.mkdir(parents=True)
        notes_dir.mkdir()

        config_path = styles_dir / "config.demo.yaml"
        config_path.write_text(
            'input_folder: "notes"\noutput_dir: "notes/demo/generate"\n',
            encoding="utf-8",
        )

        loaded = ConfigFileLoader.load_from_file(str(config_path))

        assert loaded["input_folder"] == str(notes_dir.resolve())
        assert loaded["output_dir"] == str((repo_root / "notes" / "demo" / "generate").resolve())

    def test_load_from_file_resolves_custom_config_relative_to_config_dir(self, tmp_path):
        """Custom config files outside styles/ should resolve relative to their own folder."""
        config_dir = tmp_path / "custom"
        input_dir = config_dir / "input"
        config_dir.mkdir()
        input_dir.mkdir()

        config_path = config_dir / "config.yaml"
        config_path.write_text(
            'input_folder: "input"\noutput_dir: "out"\n',
            encoding="utf-8",
        )

        loaded = ConfigFileLoader.load_from_file(str(config_path))

        assert loaded["input_folder"] == str(input_dir.resolve())
        assert loaded["output_dir"] == str((config_dir / "out").resolve())

    def test_validate_config_rejects_multiple_input_methods(self):
        """Configs should not define multiple processing inputs."""
        with pytest.raises(ValueError, match="multiple input methods"):
            ConfigFileLoader.validate_config(
                {"pptx": "/tmp/demo.pptx", "input_folder": "/tmp/input"}
            )

    def test_validate_config_requires_at_least_one_input_method(self):
        """Configs should define one YAML-owned input source."""
        with pytest.raises(ValueError, match="must specify either 'pptx', 'folder', or 'input_folder'"):
            ConfigFileLoader.validate_config({"output_dir": "/tmp/out"})


class TestUnifiedProcessor:
    """Tests for unified processor config behavior."""

    @pytest.mark.asyncio
    async def test_process_styles_directory_uses_yaml_configs(self):
        """All-styles processing should iterate config files, not style subfolders."""
        processor = UnifiedProcessor()

        with patch.object(
            processor.scanner,
            "get_style_config_paths",
            return_value=["/tmp/styles/config.alpha.yaml", "/tmp/styles/config.beta.yaml"],
        ), patch.object(
            processor,
            "process_single_style",
            AsyncMock(side_effect=[{"deck": [("notes-a", None)]}, {"deck": [("notes-b", None)]}]),
        ) as mock_process:
            results = await processor.process_styles_directory()

        assert results == {
            "alpha": {"deck": [("notes-a", None)]},
            "beta": {"deck": [("notes-b", None)]},
        }
        assert mock_process.await_count == 2

    @pytest.mark.asyncio
    async def test_process_single_style_delegates_to_config_processing(self):
        """Style processing should resolve the config path then run process_config."""
        processor = UnifiedProcessor()

        with patch.object(
            processor,
            "_resolve_style_config_path",
            return_value="/tmp/styles/config.alpha.yaml",
        ), patch.object(
            processor,
            "process_config",
            AsyncMock(return_value={"deck": [("notes", None)]}),
        ) as mock_process:
            result = await processor.process_single_style("alpha")

        assert result == {"deck": [("notes", None)]}
        mock_process.assert_awaited_once_with("/tmp/styles/config.alpha.yaml")

    def test_get_file_sets_from_config_with_pptx_uses_matching_pdf(self, tmp_path):
        """Single-file configs should build a FileSet from YAML-owned PPTX/PDF paths."""
        processor = UnifiedProcessor()
        pptx_path = tmp_path / "deck.pptx"
        pdf_path = tmp_path / "deck.pdf"
        pptx_path.write_text("pptx", encoding="utf-8")
        pdf_path.write_text("pdf", encoding="utf-8")

        file_sets = processor._get_file_sets_from_config(
            {"pptx": str(pptx_path), "pdf": str(pdf_path)},
            "alpha",
        )

        assert file_sets == [
            FileSet(
                pptx_path=str(pptx_path),
                pdf_path=str(pdf_path),
                base_name="deck",
                directory=str(tmp_path),
                style="alpha",
                category="style/alpha",
            )
        ]

    def test_get_file_sets_from_config_rejects_missing_inputs(self):
        """Config processing should fail fast if YAML defines no input source."""
        processor = UnifiedProcessor()

        with pytest.raises(ValueError, match="must specify 'pptx', 'folder', or 'input_folder'"):
            processor._get_file_sets_from_config({"language": "en"})

    @pytest.mark.asyncio
    async def test_process_config_returns_empty_when_no_matching_file_sets(self):
        """Config runs should return an empty result when scanning finds nothing."""
        processor = UnifiedProcessor()

        with patch.object(
            processor,
            "_resolve_style_config_path",
            return_value="/tmp/styles/config.alpha.yaml",
        ), patch(
            "application.unified_processor.ConfigFileLoader.load_from_file",
            return_value={"input_folder": "/tmp/input"},
        ), patch.object(
            processor,
            "_get_file_sets_from_config",
            return_value=[],
        ):
            result = await processor.process_config("alpha")

        assert result == {}

    @pytest.mark.asyncio
    async def test_process_file_sets_with_config_keeps_successful_languages(self):
        """Per-language failures should not erase successful YAML-driven results."""
        processor = UnifiedProcessor()
        file_set = FileSet(
            pptx_path="/tmp/deck.pptx",
            pdf_path="/tmp/deck.pdf",
            base_name="deck",
            directory="/tmp",
        )

        with patch.object(
            processor,
            "_process_file_set_with_config",
            AsyncMock(side_effect=[("notes-en", "visuals-en"), RuntimeError("tts failed")]),
        ) as mock_process:
            results = await processor._process_file_sets_with_config(
                [file_set],
                {"language": "en,zh-CN", "style": "cyberpunk", "output_dir": "/tmp/out"},
            )

        assert results == {"deck": [("notes-en", "visuals-en")]}
        assert mock_process.await_count == 2

    @pytest.mark.asyncio
    async def test_process_file_set_with_config_uses_yaml_settings(self):
        """Single file-set processing should construct Config and processor from YAML values."""
        processor = UnifiedProcessor()
        file_set = FileSet(
            pptx_path="/tmp/deck.pptx",
            pdf_path="/tmp/deck.pdf",
            base_name="deck",
            directory="/tmp",
            style="fallback-style",
        )
        agents = {
            "supervisor": object(),
            "analyst": object(),
            "writer": object(),
            "auditor": object(),
            "overviewer": object(),
            "designer": object(),
            "translator": object(),
            "image_translator": object(),
            "video_generator": object(),
        }
        mock_processor_instance = Mock()
        mock_processor_instance.process = AsyncMock(return_value=("notes-out", "visuals-out"))

        with patch("application.unified_processor.Config.validate", return_value=True), patch(
            "application.unified_processor.create_all_agents",
            AsyncMock(return_value=agents),
        ) as mock_create_agents, patch(
            "application.unified_processor.PresentationProcessor",
            return_value=mock_processor_instance,
        ) as mock_presentation_processor:
            result = await processor._process_file_set_with_config(
                file_set,
                "zh-CN",
                config_style={"visual_style": "cyberpunk", "speaker_style": "teacher"},
                config_output_dir="/tmp/output",
                config_skip_visuals=True,
                config_generate_videos=True,
                config_retry_errors=True,
                config_region="us-central1",
                config_course_id="course-123",
                config_progress_file="/tmp/progress.json",
            )

        assert result == ("notes-out", "visuals-out")
        mock_create_agents.assert_awaited_once_with(
            visual_style="cyberpunk",
            speaker_style="teacher",
        )
        config_obj = mock_presentation_processor.call_args.kwargs["config"]
        assert config_obj.language == "zh-CN"
        assert config_obj.style == "cyberpunk"
        assert config_obj.output_dir == "/tmp/output"
        assert config_obj.skip_visuals is True
        assert config_obj.generate_videos is True
        assert config_obj.retry_errors is True
        assert config_obj.region == "us-central1"
        assert config_obj.course_id == "course-123"
        assert config_obj.progress_file == "/tmp/progress.json"
