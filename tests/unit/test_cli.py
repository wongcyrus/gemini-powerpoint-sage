"""Tests for CLI interface."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from application.cli import CLI


class TestCLI:
    """Tests for CLI class."""
    
    def test_parser_creation(self):
        """Test that parser is created with all arguments."""
        cli = CLI()
        
        assert cli.parser is not None
        
        # Check that key arguments exist
        args = cli.parser.parse_args(['--pptx', 'test.pptx', '--pdf', 'test.pdf'])
        assert args.pptx == 'test.pptx'
        assert args.pdf == 'test.pdf'
    
    def test_parser_refine_mode(self):
        """Test parser handles refine mode."""
        cli = CLI()
        args = cli.parser.parse_args(['--refine', 'test.json'])
        
        assert args.refine == 'test.json'
    
    def test_parser_batch_mode(self):
        """Test parser handles batch mode."""
        cli = CLI()
        args = cli.parser.parse_args(['--folder', '/path/to/folder'])
        
        assert args.folder == '/path/to/folder'
    
    def test_parser_style_argument(self):
        """Test parser handles style argument."""
        cli = CLI()
        args = cli.parser.parse_args([
            '--pptx', 'test.pptx',
            '--pdf', 'test.pdf',
            '--style', 'Cyberpunk'
        ])
        
        assert args.style == 'Cyberpunk'
    
    def test_parser_language_argument(self):
        """Test parser handles language argument."""
        cli = CLI()
        args = cli.parser.parse_args([
            '--pptx', 'test.pptx',
            '--pdf', 'test.pdf',
            '--language', 'en,zh-CN'
        ])
        
        assert args.language == 'en,zh-CN'
    
    @patch('application.cli.load_dotenv')
    def test_run_missing_input(self, mock_load_dotenv):
        """Test that run fails when no input is provided."""
        cli = CLI()
        
        # Should fail without --pptx or --folder
        exit_code = cli.run([])
        assert exit_code == 1
    
    @patch('application.cli.load_dotenv')
    @patch('application.commands.refine.RefinementProcessor')
    @patch('os.path.exists', return_value=True)
    def test_run_refine_mode(self, mock_exists, mock_processor, mock_load_dotenv):
        """Test run in refine mode."""
        cli = CLI()
        
        # Mock the processor
        mock_proc_instance = Mock()
        mock_proc_instance.refine = AsyncMock()
        mock_processor.return_value = mock_proc_instance
        
        exit_code = cli.run(['--refine', 'test.json'])
        
        assert exit_code == 0
