"""Tests for CLI interface."""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.cli import CLI


class TestCLI:
    """Tests for CLI class."""

    def test_parser_creation(self):
        """Test that parser is created with YAML processing arguments."""
        cli = CLI()

        assert cli.parser is not None

        args = cli.parser.parse_args(["--config", "config.yaml"])
        assert args.config == "config.yaml"

    def test_parser_style_config_argument(self):
        """Test parser handles style-config mode."""
        cli = CLI()
        args = cli.parser.parse_args(["--style-config", "Cyberpunk"])

        assert args.style_config == "Cyberpunk"

    def test_parser_refine_mode(self):
        """Test parser handles refine mode."""
        cli = CLI()
        args = cli.parser.parse_args(["--refine", "test.json"])

        assert args.refine == "test.json"

    def test_parser_tts_utility_arguments(self):
        """Test parser keeps utility-mode arguments."""
        cli = CLI()
        args = cli.parser.parse_args(
            ["--tts-only", "--progress-file", "test.json", "--language", "en"]
        )

        assert args.tts_only is True
        assert args.progress_file == "test.json"
        assert args.language == "en"

    @patch("application.cli.load_dotenv")
    def test_run_defaults_to_styles_mode(self, mock_load_dotenv):
        """Test that run defaults to styles mode when no input is provided."""
        cli = CLI()

        with patch.object(cli, "_handle_processing", AsyncMock()) as mock_handle:
            exit_code = cli.run([])

        assert exit_code == 0
        mock_handle.assert_awaited_once()

    @patch("application.cli.load_dotenv")
    @patch("application.commands.refine.RefinementProcessor")
    @patch("os.path.exists", return_value=True)
    def test_run_refine_mode(self, mock_exists, mock_processor, mock_load_dotenv):
        """Test run in refine mode."""
        cli = CLI()

        mock_proc_instance = Mock()
        mock_proc_instance.refine = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        exit_code = cli.run(["--refine", "test.json"])

        assert exit_code == 0

    @patch("application.cli.load_dotenv")
    def test_run_accepts_config_as_processing_method(self, mock_load_dotenv):
        """Test that --config is treated as a primary processing entrypoint."""
        cli = CLI()

        with patch.object(cli, "_handle_processing", AsyncMock()) as mock_handle:
            exit_code = cli.run(["--config", "settings.yaml"])

        assert exit_code == 0
        mock_handle.assert_awaited_once()

    @patch("application.cli.load_dotenv")
    def test_run_rejects_multiple_input_methods(self, mock_load_dotenv, capsys):
        """Test that mutually exclusive processing entrypoints are rejected."""
        cli = CLI()

        exit_code = cli.run(["--config", "settings.yaml", "--styles"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Cannot use multiple input methods" in captured.out

    @patch("application.cli.load_dotenv")
    def test_run_returns_error_when_processing_fails(self, mock_load_dotenv):
        """Test run returns non-zero if processing raises an exception."""
        cli = CLI()

        with patch.object(cli, "_handle_processing", AsyncMock(side_effect=RuntimeError("boom"))):
            exit_code = cli.run(["--config", "settings.yaml"])

        assert exit_code == 1

    @patch("application.cli.load_dotenv")
    def test_run_allows_style_config_for_synthesis_mode(self, mock_load_dotenv):
        """Test style-config can be paired with synthesize-style-videos mode."""
        cli = CLI()

        with patch.object(cli, "_handle_processing", AsyncMock()) as mock_handle:
            exit_code = cli.run(["--synthesize-style-videos", "--style-config", "cyberpunk"])

        assert exit_code == 0
        mock_handle.assert_awaited_once()

    def test_setup_environment_resolves_relative_progress_file(self):
        """Test progress file paths are resolved against the current working directory."""
        cli = CLI()
        args = cli.parser.parse_args(["--tts-only", "--progress-file", "data/progress.json"])

        with patch("application.cli.os.getcwd", return_value="/workspace"), patch.dict(os.environ, {}, clear=True):
            cli._setup_environment(args)
            assert os.environ["SPEAKER_NOTE_PROGRESS_FILE"] == "/workspace/data/progress.json"

    @pytest.mark.asyncio
    @patch("application.cli.UnifiedProcessor")
    async def test_handle_processing_dispatches_config_mode(self, mock_processor_cls):
        """Test config mode dispatches to UnifiedProcessor.process_config."""
        cli = CLI()
        args = cli.parser.parse_args(["--config", "settings.yaml"])
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_config = AsyncMock()

        await cli._handle_processing(args)

        mock_processor.process_config.assert_awaited_once_with("settings.yaml")

    @pytest.mark.asyncio
    @patch("application.cli.UnifiedProcessor")
    async def test_handle_processing_dispatches_style_mode(self, mock_processor_cls):
        """Test style-config mode dispatches to UnifiedProcessor.process_single_style."""
        cli = CLI()
        args = cli.parser.parse_args(["--style-config", "cyberpunk"])
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_single_style = AsyncMock()

        await cli._handle_processing(args)

        mock_processor.process_single_style.assert_awaited_once_with("cyberpunk")

    @pytest.mark.asyncio
    @patch("application.cli.UnifiedProcessor")
    async def test_handle_processing_dispatches_styles_mode(self, mock_processor_cls):
        """Test styles mode dispatches to UnifiedProcessor.process_styles_directory."""
        cli = CLI()
        args = cli.parser.parse_args(["--styles"])
        mock_processor = mock_processor_cls.return_value
        mock_processor.process_styles_directory = AsyncMock()

        await cli._handle_processing(args)

        mock_processor.process_styles_directory.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("utils.tts_cli_utils.TTSCLIUtility")
    async def test_handle_tts_only_requires_json_progress_file(self, mock_tts_cls, capsys):
        """Test TTS-only mode rejects non-JSON progress files."""
        cli = CLI()
        args = cli.parser.parse_args(["--tts-only", "--progress-file", "progress.txt"])

        await cli._handle_tts_only(args)

        captured = capsys.readouterr()
        assert "requires a JSON progress file" in captured.out
        mock_tts_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch("utils.tts_cli_utils.TTSCLIUtility")
    async def test_handle_tts_only_runs_generation(self, mock_tts_cls, capsys):
        """Test TTS-only mode delegates to the TTS utility with parsed arguments."""
        cli = CLI()
        args = cli.parser.parse_args(
            ["--tts-only", "--progress-file", "progress.json", "--language", "zh-CN", "--output-dir", "tts-out"]
        )
        mock_tts = mock_tts_cls.return_value
        mock_tts.generate_tts_for_presentation = AsyncMock(return_value={"successful": 2})

        await cli._handle_tts_only(args)

        mock_tts.generate_tts_for_presentation.assert_awaited_once_with(
            "progress.json",
            "zh-CN",
            "tts-out",
        )
        assert '"successful": 2' in capsys.readouterr().out
