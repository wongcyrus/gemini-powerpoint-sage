"""Tests for command classes."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from application.commands import ProcessCommand, BatchCommand, RefineCommand


class TestProcessCommand:
    """Tests for ProcessCommand."""
    
    def test_initialization(self):
        """Test command initialization."""
        cmd = ProcessCommand(
            pptx_path="test.pptx",
            pdf_path="test.pdf",
            language="en",
        )
        
        assert cmd.pptx_path == "test.pptx"
        assert cmd.pdf_path == "test.pdf"
        assert cmd.language == "en"
    
    def test_validate_missing_pptx(self):
        """Test validation fails for missing PPTX."""
        cmd = ProcessCommand(
            pptx_path="nonexistent.pptx",
            pdf_path="test.pdf",
        )
        
        with pytest.raises(ValueError, match="PPTX file not found"):
            cmd.validate()
    
    @patch('os.path.exists')
    def test_validate_missing_pdf(self, mock_exists):
        """Test validation fails for missing PDF."""
        # PPTX exists, PDF doesn't
        mock_exists.side_effect = lambda path: path == "test.pptx"
        
        cmd = ProcessCommand(
            pptx_path="test.pptx",
            pdf_path="nonexistent.pdf",
        )
        
        with pytest.raises(ValueError, match="PDF file not found"):
            cmd.validate()
    
    @patch('os.path.exists', return_value=True)
    @patch('application.commands.process.create_all_agents')
    @patch('application.commands.process.Config')
    @patch('application.commands.process.PresentationProcessor')
    async def test_execute(
        self,
        mock_processor_class,
        mock_config_class,
        mock_create_agents,
        mock_exists
    ):
        """Test command execution."""
        # Setup mocks
        mock_config = Mock()
        mock_config.visual_style = "Professional"
        mock_config.speaker_style = "Professional"
        mock_config_class.return_value = mock_config
        
        mock_agents = {
            "supervisor": Mock(),
            "analyst": Mock(),
            "writer": Mock(),
            "auditor": Mock(),
            "overviewer": Mock(),
            "designer": Mock(),
            "translator": Mock(),
            "image_translator": Mock(),
            "video_generator": Mock(),
        }
        mock_create_agents.return_value = mock_agents
        
        mock_processor = Mock()
        mock_processor.process = AsyncMock(return_value=("notes.pptx", "visuals.pptx"))
        mock_processor_class.return_value = mock_processor
        
        # Execute command
        cmd = ProcessCommand(
            pptx_path="test.pptx",
            pdf_path="test.pdf",
        )
        result = await cmd.execute()
        
        # Verify
        assert result == ("notes.pptx", "visuals.pptx")
        mock_config_class.assert_called_once()
        mock_create_agents.assert_called_once()
        mock_processor.process.assert_called_once()


class TestBatchCommand:
    """Tests for BatchCommand."""
    
    def test_initialization(self):
        """Test command initialization."""
        cmd = BatchCommand(
            folder_path="/path/to/folder",
            languages="en,zh-CN",
        )
        
        assert cmd.folder_path == "/path/to/folder"
        assert cmd.languages == "en,zh-CN"
    
    def test_validate_missing_folder(self):
        """Test validation fails for missing folder."""
        cmd = BatchCommand(folder_path="/nonexistent/folder")
        
        with pytest.raises(ValueError, match="Folder not found"):
            cmd.validate()
    
    def test_parse_languages(self):
        """Test language parsing."""
        cmd = BatchCommand(
            folder_path="/path",
            languages="zh-CN,en,yue-HK"
        )
        
        lang_list = cmd._parse_languages()
        
        # English should be first
        assert lang_list[0] == "en"
        assert "zh-CN" in lang_list
        assert "yue-HK" in lang_list
    
    def test_parse_languages_no_english(self):
        """Test language parsing adds English if missing."""
        cmd = BatchCommand(
            folder_path="/path",
            languages="zh-CN,yue-HK"
        )
        
        lang_list = cmd._parse_languages()
        
        # English should be added and first
        assert lang_list[0] == "en"
        assert len(lang_list) == 3


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
