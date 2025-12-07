"""Tests for configuration constants."""

import pytest
from config.constants import (
    ModelConfig,
    ProcessingConfig,
    FilePatterns,
    LanguageConfig,
    SlideConfig,
    EnvironmentVars,
)


class TestModelConfig:
    """Tests for ModelConfig."""
    
    def test_model_names_are_strings(self):
        """Test that all model names are strings."""
        assert isinstance(ModelConfig.SUPERVISOR, str)
        assert isinstance(ModelConfig.ANALYST, str)
        assert isinstance(ModelConfig.WRITER, str)
        assert isinstance(ModelConfig.DESIGNER, str)
    
    def test_model_names_not_empty(self):
        """Test that model names are not empty."""
        assert len(ModelConfig.SUPERVISOR) > 0
        assert len(ModelConfig.ANALYST) > 0
        assert len(ModelConfig.WRITER) > 0


class TestProcessingConfig:
    """Tests for ProcessingConfig."""
    
    def test_retry_settings(self):
        """Test retry configuration values."""
        assert ProcessingConfig.MAX_RETRIES > 0
        assert ProcessingConfig.RETRY_DELAY > 0
        assert ProcessingConfig.RETRY_BACKOFF_MULTIPLIER >= 1.0
    
    def test_concurrency_settings(self):
        """Test concurrency settings."""
        assert ProcessingConfig.MAX_CONCURRENT_SLIDES > 0
        assert ProcessingConfig.PROGRESS_SAVE_INTERVAL > 0
    
    def test_dpi_settings(self):
        """Test DPI settings."""
        assert ProcessingConfig.PDF_DPI_STANDARD > 0
        assert ProcessingConfig.PDF_DPI_LOW > 0
        assert ProcessingConfig.PDF_DPI_STANDARD > ProcessingConfig.PDF_DPI_LOW


class TestFilePatterns:
    """Tests for FilePatterns."""
    
    def test_progress_file_pattern(self):
        """Test progress file pattern formatting."""
        result = FilePatterns.PROGRESS_FILE.format(
            base="test",
            lang="en"
        )
        assert result == "test_en_progress.json"
    
    def test_notes_output_pattern(self):
        """Test notes output pattern formatting."""
        result = FilePatterns.NOTES_OUTPUT.format(
            base="test",
            lang="zh-CN",
            ext=".pptx"
        )
        assert result == "test_zh-CN_with_notes.pptx"
    
    def test_visuals_dir_pattern(self):
        """Test visuals directory pattern."""
        result = FilePatterns.VISUALS_DIR.format(
            base="test",
            lang="en"
        )
        assert result == "test_en_visuals"
    
    def test_reimagined_slide_pattern(self):
        """Test reimagined slide pattern."""
        result = FilePatterns.REIMAGINED_SLIDE.format(idx=5)
        assert result == "slide_5_reimagined.png"


class TestLanguageConfig:
    """Tests for LanguageConfig."""
    
    def test_default_language(self):
        """Test default language is English."""
        assert LanguageConfig.DEFAULT_LANGUAGE == "en"
    
    def test_get_language_name_english(self):
        """Test getting English language name."""
        name = LanguageConfig.get_language_name("en")
        assert name == "English"
    
    def test_get_language_name_chinese(self):
        """Test getting Chinese language name."""
        name = LanguageConfig.get_language_name("zh-CN")
        assert "Chinese" in name
        assert "简体" in name
    
    def test_get_language_name_unknown(self):
        """Test getting unknown language returns code."""
        name = LanguageConfig.get_language_name("unknown")
        assert name == "unknown"
    
    def test_locale_names_not_empty(self):
        """Test that locale names dict is not empty."""
        assert len(LanguageConfig.LOCALE_NAMES) > 0
    
    def test_all_locales_have_names(self):
        """Test that all locales have non-empty names."""
        for locale, name in LanguageConfig.LOCALE_NAMES.items():
            assert isinstance(locale, str)
            assert isinstance(name, str)
            assert len(locale) > 0
            assert len(name) > 0


class TestSlideConfig:
    """Tests for SlideConfig."""
    
    def test_slide_dimensions(self):
        """Test slide dimensions are positive."""
        assert SlideConfig.SLIDE_WIDTH_INCHES > 0
        assert SlideConfig.SLIDE_HEIGHT_INCHES > 0
    
    def test_aspect_ratio(self):
        """Test aspect ratio is 16:9."""
        assert SlideConfig.ASPECT_RATIO == "16:9"
        
        # Verify actual ratio
        ratio = SlideConfig.SLIDE_WIDTH_INCHES / SlideConfig.SLIDE_HEIGHT_INCHES
        expected_ratio = 16 / 9
        assert abs(ratio - expected_ratio) < 0.01


class TestEnvironmentVars:
    """Tests for EnvironmentVars."""
    
    def test_env_var_names_are_strings(self):
        """Test that all env var names are strings."""
        assert isinstance(EnvironmentVars.PROGRESS_FILE, str)
        assert isinstance(EnvironmentVars.RETRY_ERRORS, str)
        assert isinstance(EnvironmentVars.GOOGLE_CLOUD_LOCATION, str)
    
    def test_env_var_names_not_empty(self):
        """Test that env var names are not empty."""
        assert len(EnvironmentVars.PROGRESS_FILE) > 0
        assert len(EnvironmentVars.RETRY_ERRORS) > 0
        assert len(EnvironmentVars.GOOGLE_CLOUD_LOCATION) > 0
