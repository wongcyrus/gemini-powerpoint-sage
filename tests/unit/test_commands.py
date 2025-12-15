"""Tests for command classes."""

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
