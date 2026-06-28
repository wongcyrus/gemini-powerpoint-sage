"""Tests for config loading and processor config routing."""

import builtins
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.input_scanner import FileSet
from application.unified_processor import UnifiedProcessor
from config.config_loader import ConfigFileLoader, create_example_config


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

    def test_load_from_file_rejects_missing_or_unsupported_files(self, tmp_path):
        """Missing files and wrong extensions should fail fast."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            ConfigFileLoader.load_from_file(str(tmp_path / "missing.yaml"))

        bad = tmp_path / "config.txt"
        bad.write_text("x: 1", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported config file format"):
            ConfigFileLoader.load_from_file(str(bad))

    def test_load_yaml_requires_pyyaml_and_valid_yaml(self, monkeypatch, tmp_path):
        """YAML loading should surface import and parse errors clearly."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("x: 1", encoding="utf-8")

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "yaml":
                raise ImportError("missing yaml")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ImportError, match="PyYAML is required"):
            ConfigFileLoader._load_yaml(config_path)

        fake_yaml = SimpleNamespace(
            YAMLError=ValueError,
            safe_load=lambda data: (_ for _ in ()).throw(ValueError("bad yaml")),
        )
        monkeypatch.setattr(builtins, "__import__", original_import)
        monkeypatch.setitem(sys.modules, "yaml", fake_yaml)
        with pytest.raises(ValueError, match="Invalid YAML"):
            ConfigFileLoader._load_yaml(config_path)

    def test_resolve_paths_and_base_dir_helpers(self, tmp_path):
        """Relative paths should resolve against the inferred config base."""
        styles_config = tmp_path / "styles" / "config.demo.yaml"
        styles_config.parent.mkdir(parents=True)
        resolved = ConfigFileLoader._resolve_paths(
            {"input_folder": "input", "output_dir": "/abs/out", "notes": 1},
            styles_config,
        )

        assert resolved["input_folder"] == str((tmp_path / "input").resolve())
        assert resolved["output_dir"] == "/abs/out"
        assert resolved["__config_base_dir"] == str(tmp_path.resolve())
        assert ConfigFileLoader._get_config_base_dir(styles_config) == tmp_path.resolve()
        assert ConfigFileLoader._get_config_base_dir(tmp_path / "custom.yaml") == tmp_path.resolve()

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

    def test_validate_config_accepts_valid_input_folder_with_pairs(self, tmp_path):
        """Folder-based configs should validate when matching PPTX/PDF pairs exist."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "deck.pptx").write_text("pptx", encoding="utf-8")
        (input_dir / "deck.pdf").write_text("pdf", encoding="utf-8")

        ConfigFileLoader.validate_config({"input_folder": str(input_dir)})

    def test_validate_config_rejects_bad_folder_and_missing_pairs(self, tmp_path):
        """Folder validation should fail for invalid folders or missing PDF matches."""
        with pytest.raises(ValueError, match="Folder not found"):
            ConfigFileLoader.validate_config({"folder": str(tmp_path / "missing")})

        input_dir = tmp_path / "pairs"
        input_dir.mkdir()
        (input_dir / "deck.pptx").write_text("pptx", encoding="utf-8")
        with pytest.raises(ValueError, match="No valid PDF/PPTX pairs found"):
            ConfigFileLoader.validate_config({"input_folder": str(input_dir)})

    def test_validate_file_pairs_requires_pptx_files(self, tmp_path):
        """Pair validation should reject empty folders."""
        with pytest.raises(ValueError, match="No PPTX files found"):
            ConfigFileLoader._validate_file_pairs(str(tmp_path))

    def test_validate_config_rejects_missing_pdf_for_pptx_input(self, tmp_path):
        """Explicit PDF paths should be validated when provided."""
        pptx_path = tmp_path / "deck.pptx"
        pptx_path.write_text("pptx", encoding="utf-8")

        with pytest.raises(ValueError, match="PDF file not found"):
            ConfigFileLoader.validate_config(
                {"pptx": str(pptx_path), "pdf": str(tmp_path / "missing.pdf")}
            )

    def test_get_file_pairs_returns_only_matching_pairs(self, tmp_path):
        """Pair discovery should skip PPTX files that lack a matching PDF."""
        (tmp_path / "deck1.pptx").write_text("pptx", encoding="utf-8")
        (tmp_path / "deck1.pdf").write_text("pdf", encoding="utf-8")
        (tmp_path / "deck2.pptx").write_text("pptx", encoding="utf-8")

        pairs = ConfigFileLoader.get_file_pairs(str(tmp_path))

        assert pairs == [(str(tmp_path / "deck1.pptx"), str(tmp_path / "deck1.pdf"))]

    def test_create_example_config_writes_yaml_template(self, tmp_path):
        """Example config generation should emit the documented YAML template."""
        output_path = tmp_path / "example.yaml"

        create_example_config(str(output_path))

        content = output_path.read_text(encoding="utf-8")
        assert 'pptx: "path/to/presentation.pptx"' in content
        assert 'language: "en"' in content
        assert "retry_errors: false" in content

    def test_create_example_config_requires_pyyaml(self, monkeypatch, tmp_path):
        """The example generator should surface missing PyYAML clearly."""
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "yaml":
                raise ImportError("missing yaml")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(ImportError, match="PyYAML is required"):
            create_example_config(str(tmp_path / "example.yaml"))


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

    def test_resolve_style_config_path_accepts_explicit_file_path(self, tmp_path):
        """Explicit config paths should bypass style lookup."""
        processor = UnifiedProcessor()
        config_path = tmp_path / "config.alpha.yaml"
        config_path.write_text("language: en\n", encoding="utf-8")

        assert processor._resolve_style_config_path(str(config_path)) == str(config_path)

    def test_resolve_style_config_path_raises_for_unknown_style(self):
        """Unknown styles should produce a clear config resolution error."""
        processor = UnifiedProcessor()

        with patch.object(processor.scanner, "get_style_config_path", return_value=None):
            with pytest.raises(ValueError, match="No configuration file found for style"):
                processor._resolve_style_config_path("missing-style")

    def test_get_style_name_handles_first_class_and_legacy_names(self):
        """Style name extraction should normalize both supported config naming schemes."""
        processor = UnifiedProcessor()

        assert processor._get_style_name("/tmp/config.cyberpunk.yaml") == "cyberpunk"
        assert processor._get_style_name("/tmp/cyberpunk.config.yml") == "cyberpunk"

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
    async def test_process_config_wraps_config_load_errors(self):
        """Config loading failures should surface with config path context."""
        processor = UnifiedProcessor()

        with patch.object(
            processor,
            "_resolve_style_config_path",
            return_value="/tmp/styles/config.alpha.yaml",
        ), patch(
            "application.unified_processor.ConfigFileLoader.load_from_file",
            side_effect=ValueError("bad yaml"),
        ):
            with pytest.raises(ValueError, match="Error loading configuration file /tmp/styles/config.alpha.yaml"):
                await processor.process_config("alpha")

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
