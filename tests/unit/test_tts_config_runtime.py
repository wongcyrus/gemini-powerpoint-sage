"""Tests for TTS configuration behavior."""

import os
from unittest.mock import patch

import pytest

from config.tts_config import (
    GeminiTTSConfig,
    TTSCacheConfig,
    TTSConfig,
    TTSStorageConfig,
    TraditionalTTSConfig,
    create_tts_config_from_dict,
    get_tts_config,
)
from core.domain.tts import TTSEngineType


class TestGeminiTTSConfig:
    """Tests for Gemini TTS engine settings."""

    def test_language_support_and_voice_lookup(self):
        """Gemini config should report support and return fallback voices."""
        config = GeminiTTSConfig()

        assert config.is_language_supported("en-US") is True
        assert config.is_language_supported("yue-HK") is True
        assert config.is_language_supported("xx-YY") is False
        assert config.get_api_language_code("yue-HK") == "cmn-CN"
        assert config.get_api_language_code("zh-HK") == "cmn-CN"
        assert config.get_voices_for_language("xx-YY") == config.voice_mapping["en-US"]
        assert config.get_voices_for_language("yue-HK") == config.voice_mapping["cmn-CN"]


class TestTraditionalTTSConfig:
    """Tests for traditional TTS mappings."""

    def test_language_mapping_and_voice_lookup(self):
        """Traditional config should map zh locales to the underlying TTS locale."""
        config = TraditionalTTSConfig()

        assert config.is_language_supported("zh-CN") is True
        assert config.can_handle_language("en-US") is True
        assert config.map_language_code("zh-CN") == "cmn-CN"
        assert config.map_language_code("zh-HK") == "yue-HK"
        assert config.get_voices_for_language("zh-CN")[0].startswith("cmn-CN")
        assert config.get_voices_for_language("yue-HK")[0] == "yue-HK-Standard-A"


class TestTTSConfig:
    """Tests for top-level TTS configuration."""

    def test_env_overrides_apply_to_runtime_config(self, monkeypatch):
        """Environment variables should override TTS runtime settings."""
        monkeypatch.setenv("TTS_ENABLED", "false")
        monkeypatch.setenv("TTS_CACHE_ENABLED", "false")
        monkeypatch.setenv("TTS_CACHE_TTL_HOURS", "12")
        monkeypatch.setenv("TTS_STORAGE_BUCKET", "speech-bucket")
        monkeypatch.setenv("TTS_PARALLEL_PROCESSING", "false")
        monkeypatch.setenv("TTS_MAX_CONCURRENT_SLIDES", "4")
        monkeypatch.setenv("TTS_GEMINI_MAX_CONCURRENT", "2")
        monkeypatch.setenv("TTS_TRADITIONAL_MAX_CONCURRENT", "5")
        monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "30")

        config = TTSConfig()

        assert config.enabled is False
        assert config.cache.enabled is False
        assert config.cache.ttl_hours == 12
        assert config.storage.bucket_name == "speech-bucket"
        assert config.parallel_processing is False
        assert config.max_concurrent_slides == 4
        assert config.gemini_max_concurrent == 2
        assert config.traditional_max_concurrent == 5
        assert config.gemini.timeout_seconds == 30
        assert config.traditional.timeout_seconds == 30

    def test_normalize_language_code_and_engine_selection(self):
        """Language normalization should drive engine selection."""
        config = TTSConfig()

        assert config.normalize_language_code("en") == "en-US"
        assert config.normalize_language_code("zh-CN") == "cmn-CN"
        assert config.normalize_language_code("zh-HK") == "yue-HK"
        assert config.select_engine_for_language("en") == TTSEngineType.GEMINI
        assert config.select_engine_for_language("yue-HK") == TTSEngineType.GEMINI
        assert config.select_engine_for_language("zh-HK") == TTSEngineType.GEMINI
        assert config.select_engine_for_language("unknown-lang") == TTSEngineType.TRADITIONAL

    def test_get_max_concurrent_for_engine_respects_parallel_toggle(self):
        """Concurrency should collapse to one when parallel processing is disabled."""
        config = TTSConfig(parallel_processing=False)
        assert config.get_max_concurrent_for_engine(TTSEngineType.GEMINI) == 1

        config = TTSConfig(parallel_processing=True, gemini_max_concurrent=2, traditional_max_concurrent=4)
        assert config.get_max_concurrent_for_engine(TTSEngineType.GEMINI) == 2
        assert config.get_max_concurrent_for_engine(TTSEngineType.TRADITIONAL) == 4

    def test_get_voice_config_for_language_selects_expected_voice(self):
        """Voice selection should normalize languages and honor gender preference."""
        config = TTSConfig()

        female = config.get_voice_config_for_language("en", TTSEngineType.GEMINI, gender="female")
        male = config.get_voice_config_for_language("zh-CN", TTSEngineType.TRADITIONAL, gender="male")
        cantonese = config.get_voice_config_for_language("yue-HK", TTSEngineType.GEMINI, gender="female")
        cantonese_hk = config.get_voice_config_for_language("zh-HK", TTSEngineType.GEMINI, gender="female")

        assert female.language_code == "en-US"
        assert female.voice_name is not None
        assert male.language_code == "cmn-CN"
        assert male.voice_name is not None
        assert cantonese.language_code == "cmn-CN"
        assert cantonese.voice_name in {"Aoede", "Callirrhoe", "Kore", "Zephyr"}
        assert cantonese_hk.language_code == "cmn-CN"

    def test_validate_requires_bucket_and_positive_concurrency(self, tmp_path):
        """Validation should enforce storage bucket and positive concurrency limits."""
        config = TTSConfig()
        config.storage.bucket_name = ""
        with pytest.raises(ValueError, match="bucket name"):
            config.validate()

        config.storage.bucket_name = "bucket"
        config.cache.cache_directory = str(tmp_path / "tts-cache")
        config.max_concurrent_slides = 0
        with pytest.raises(ValueError, match="Max concurrent slides"):
            config.validate()

    def test_validate_accepts_configured_runtime(self, tmp_path):
        """A fully configured runtime should validate successfully."""
        config = TTSConfig()
        config.storage.bucket_name = "bucket"
        config.cache.cache_directory = str(tmp_path / "tts-cache")

        assert config.validate() is True
        assert os.path.isdir(config.get_cache_directory())
        assert config.get_storage_directory_pattern() == "{base_name}_{language_code}_speech"
        assert config.get_filename_pattern() == "slide_{slide_number}_{content_hash}.mp3"

    def test_validate_skips_when_disabled(self):
        """Disabled TTS should bypass validation requirements."""
        config = TTSConfig(enabled=False)
        config.storage.bucket_name = ""

        assert config.validate() is True

    def test_validate_raises_when_cache_directory_cannot_be_created(self, monkeypatch):
        """Cache directory creation failures should surface as validation errors."""
        config = TTSConfig()
        config.storage.bucket_name = "bucket"
        monkeypatch.setattr("config.tts_config.os.makedirs", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")))

        with pytest.raises(ValueError, match="Cannot create cache directory"):
            config.validate()

    def test_select_voice_by_gender_prefers_expected_voice_group(self):
        """Gender-based selection should prefer matching voices when available."""
        config = TTSConfig()

        assert config._select_voice_by_gender(["Aoede", "Kore"], "female") == "Aoede"
        assert config._select_voice_by_gender(["Zeus", "Apollo"], "male") == "Zeus"
        assert config._select_voice_by_gender(["Aoede", "Zeus"], "neutral") == "Aoede"


class TestTTSConfigFactories:
    """Tests for TTS config factory helpers."""

    def test_get_tts_config_returns_fresh_config(self):
        """The getter should build a new config instance on each call."""
        first = get_tts_config()
        second = get_tts_config()

        assert isinstance(first, TTSConfig)
        assert isinstance(second, TTSConfig)
        assert first is not second

    def test_create_tts_config_from_dict_builds_nested_configs(self):
        """Dict-based construction should hydrate nested config objects."""
        config = create_tts_config_from_dict(
            {
                "enabled": False,
                "gemini": {"timeout_seconds": 12},
                "traditional": {"timeout_seconds": 18},
                "cache": {"ttl_hours": 6},
                "storage": {"bucket_name": "bucket"},
            }
        )

        assert config.enabled is False
        assert config.gemini.timeout_seconds == 12
        assert config.traditional.timeout_seconds == 18
        assert config.cache.ttl_hours == 6
        assert config.storage.bucket_name == "bucket"

    def test_component_configs_validate_their_own_invariants(self):
        """Low-level config classes should reject invalid numeric settings."""
        with pytest.raises(ValueError, match="TTL hours"):
            TTSCacheConfig(ttl_hours=-1)

        with pytest.raises(ValueError, match="Max cache size"):
            TTSCacheConfig(max_cache_size_mb=0)

        with pytest.raises(ValueError, match="Upload timeout"):
            TTSStorageConfig(upload_timeout_seconds=0)
