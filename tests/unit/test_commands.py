"""Tests for command classes."""

import os

import pytest
from unittest.mock import Mock, patch, AsyncMock
from application.commands import RefineCommand



class TestRefineCommand:
    """Tests for RefineCommand."""
    
    def test_initialization(self):
        """Test command initialization."""
        cmd = RefineCommand(input_path="test.json")
        
        assert "test.json" in cmd.input_path
        assert cmd.processor is not None
    
    def test_validate_missing_path(self):
        """Test validation fails for missing path."""
        cmd = RefineCommand(input_path="/nonexistent/path")
        
        with pytest.raises(ValueError, match="Path not found"):
            cmd.validate()
    
    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=False)
    def test_find_json_files_single(self, mock_isdir, mock_exists):
        """Test finding single JSON file."""
        cmd = RefineCommand(input_path="test.json")
        
        files = cmd._find_json_files()
        
        assert len(files) == 1
        assert files[0][0].endswith("test.json")
        assert files[0][1].endswith("test_refined.json")

    def test_find_json_files_directory_filters_refined_outputs(self, tmp_path):
        """Directory mode should ignore already refined JSON files."""
        (tmp_path / "deck.json").write_text("{}", encoding="utf-8")
        (tmp_path / "deck_refined.json").write_text("{}", encoding="utf-8")
        (tmp_path / "other.JSON").write_text("{}", encoding="utf-8")

        cmd = RefineCommand(input_path=str(tmp_path))

        files = cmd._find_json_files()

        assert sorted(os.path.basename(src) for src, _ in files) == ["deck.json", "other.JSON"]
        assert all("_refined." in os.path.basename(dest) for _, dest in files)

    @pytest.mark.asyncio
    async def test_execute_processes_each_discovered_file(self, tmp_path):
        """Execute should refine each discovered JSON file."""
        input_file = tmp_path / "deck.json"
        input_file.write_text("{}", encoding="utf-8")
        cmd = RefineCommand(input_path=str(input_file))
        cmd.processor.refine = AsyncMock()

        await cmd.execute()

        cmd.processor.refine.assert_awaited_once()
        args = cmd.processor.refine.await_args.args
        assert args[0].endswith("deck.json")
        assert args[1].endswith("deck_refined.json")

    @pytest.mark.asyncio
    async def test_execute_continues_after_individual_failures(self, tmp_path):
        """Execute should continue processing remaining files after one failure."""
        for name in ("a.json", "b.json"):
            (tmp_path / name).write_text("{}", encoding="utf-8")

        cmd = RefineCommand(input_path=str(tmp_path))
        cmd.processor.refine = AsyncMock(side_effect=[RuntimeError("boom"), None])

        await cmd.execute()

        assert cmd.processor.refine.await_count == 2
