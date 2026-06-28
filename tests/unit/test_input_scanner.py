"""Tests for input scanning and config discovery."""

from pathlib import Path

from application.input_scanner import FileSet, InputScanner, scan_input_sources


class TestInputScanner:
    """Tests for scanner behavior."""

    def test_scan_directory_finds_valid_pairs_and_ignores_temporary_files(self, tmp_path):
        """Scanner should collect PPTX/PDF pairs while ignoring Office temp files."""
        scanner = InputScanner(str(tmp_path))
        (tmp_path / "deck.pptx").touch()
        (tmp_path / "deck.pdf").touch()
        (tmp_path / "macro.PPTM").touch()
        (tmp_path / "macro.PDF").touch()
        (tmp_path / "~$draft.pptx").touch()

        file_sets = scanner.scan_directory(tmp_path, style="cyberpunk", category="styles")

        assert {(f.base_name, Path(f.pdf_path).suffix) for f in file_sets} == {
            ("deck", ".pdf"),
            ("macro", ".PDF"),
        }
        assert all(not Path(f.pptx_path).name.startswith("~$") for f in file_sets)

    def test_scan_all_collects_styles_notes_and_root_sources(self, tmp_path):
        """scan_all should include every supported input bucket when present."""
        styles_input = tmp_path / "styles" / "cyberpunk" / "input"
        notes_dir = tmp_path / "notes" / "module1"
        styles_input.mkdir(parents=True)
        notes_dir.mkdir(parents=True)
        (tmp_path / "rootdeck.pptx").touch()
        (tmp_path / "rootdeck.pdf").touch()
        (styles_input / "styled.pptx").touch()
        (styles_input / "styled.pdf").touch()
        (notes_dir / "noted.pptx").touch()
        (notes_dir / "noted.pdf").touch()

        results = InputScanner(str(tmp_path)).scan_all()

        assert "styles" in results
        assert "notes" in results
        assert "root" in results
        assert [f.base_name for f in results["root"]] == ["rootdeck"]

    def test_get_style_config_path_supports_multiple_naming_patterns(self, tmp_path):
        """Style config lookup should support first-class and legacy names."""
        styles_dir = tmp_path / "styles"
        styles_dir.mkdir()
        config_path = styles_dir / "cyberpunk.config.yml"
        config_path.touch()

        resolved = InputScanner(str(tmp_path)).get_style_config_path("Cyberpunk")

        assert resolved == str(config_path)

    def test_get_style_config_paths_returns_sorted_yaml_configs(self, tmp_path):
        """Only style YAML configs should be returned, in sorted order."""
        styles_dir = tmp_path / "styles"
        styles_dir.mkdir()
        (styles_dir / "config.beta.yaml").touch()
        (styles_dir / "config.alpha.yml").touch()
        (styles_dir / "notes.txt").touch()

        resolved = InputScanner(str(tmp_path)).get_style_config_paths()

        assert resolved == [
            str(styles_dir / "config.alpha.yml"),
            str(styles_dir / "config.beta.yaml"),
        ]

    def test_organize_by_style_groups_default_when_missing(self):
        """Files without a style should be grouped under the default bucket."""
        scanner = InputScanner(".")
        grouped = scanner.organize_by_style(
            [
                FileSet("a.pptx", "a.pdf", "a", ".", style="cyberpunk"),
                FileSet("b.pptx", "b.pdf", "b", ".", style=None),
            ]
        )

        assert list(grouped) == ["cyberpunk", "default"]
        assert grouped["default"][0].base_name == "b"

    def test_get_output_directory_uses_expected_conventions(self, tmp_path):
        """Output directory selection should follow style and notes conventions."""
        scanner = InputScanner(str(tmp_path))
        style_file = FileSet("a.pptx", "a.pdf", "a", str(tmp_path), style="cyberpunk", category="styles")
        notes_file = FileSet("b.pptx", "b.pdf", "b", str(tmp_path / "notes"), category="notes/module1")
        plain_file = FileSet("c.pptx", "c.pdf", "c", str(tmp_path / "plain"))

        assert scanner.get_output_directory(style_file) == str(tmp_path / "styles" / "cyberpunk" / "generate")
        assert scanner.get_output_directory(notes_file) == str(tmp_path / "notes")
        assert scanner.get_output_directory(plain_file) == str(tmp_path / "plain")
        assert scanner.get_output_directory(plain_file, base_output_dir="/tmp/out") == "/tmp/out"

    def test_scan_input_sources_wraps_scan_all(self, tmp_path):
        """Convenience scanning should delegate to the scanner implementation."""
        (tmp_path / "deck.pptx").touch()
        (tmp_path / "deck.pdf").touch()

        results = scan_input_sources(str(tmp_path))

        assert "root" in results
        assert results["root"][0].base_name == "deck"
