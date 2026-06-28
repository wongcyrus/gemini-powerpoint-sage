"""Tests for TTS engine selection wrapper."""

from unittest.mock import Mock

from core.domain.tts import TTSEngineType, VoiceConfig
from services.tts.engine_selector import EngineSelector


class TestEngineSelector:
    """Tests for EngineSelector delegation."""

    def test_select_engine_delegates_to_config(self):
        """Engine selection should call through to the config object."""
        config = Mock()
        config.select_engine_for_language.return_value = TTSEngineType.GEMINI

        selector = EngineSelector(config)

        assert selector.select_engine("en-US") == TTSEngineType.GEMINI
        config.select_engine_for_language.assert_called_once_with("en-US")

    def test_get_voice_config_delegates_to_config(self):
        """Voice config lookup should forward all parameters."""
        config = Mock()
        voice_config = VoiceConfig(language_code="en-US")
        config.get_voice_config_for_language.return_value = voice_config

        selector = EngineSelector(config)

        assert selector.get_voice_config("en-US", TTSEngineType.TRADITIONAL, gender="female") is voice_config
        config.get_voice_config_for_language.assert_called_once_with(
            "en-US",
            TTSEngineType.TRADITIONAL,
            "female",
        )

    def test_language_support_helpers_delegate_to_nested_configs(self):
        """Support checks should rely on the nested config objects."""
        config = Mock()
        config.gemini.is_language_supported.return_value = True
        config.traditional.is_language_supported.return_value = False

        selector = EngineSelector(config)

        assert selector.is_gemini_supported("ja-JP") is True
        assert selector.is_traditional_required("ja-JP") is False
        config.gemini.is_language_supported.assert_called_once_with("ja-JP")
        config.traditional.is_language_supported.assert_called_once_with("ja-JP")
