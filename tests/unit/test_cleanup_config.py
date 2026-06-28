"""Tests for cleanup configuration helpers."""

from config.cleanup_config import CleanupConfig


class TestCleanupConfig:
    """Tests for cleanup policy configuration."""

    def test_get_config_returns_expected_keys(self):
        """The exported config dictionary should expose the documented knobs."""
        config = CleanupConfig.get_config()

        assert config["min_free_space_gb"] == CleanupConfig.MIN_FREE_SPACE_GB
        assert config["warn_high_disk_usage"] == CleanupConfig.WARN_HIGH_DISK_USAGE
        assert config["chunk_size"] == CleanupConfig.CHUNK_SIZE

    def test_cleanup_flags_reflect_class_settings(self):
        """Boolean cleanup helpers should mirror the class-level policy."""
        assert CleanupConfig.should_cleanup_immediately() is True
        assert CleanupConfig.should_force_cleanup_on_error() is True

    def test_chunked_processing_threshold_is_enforced(self):
        """Chunked processing should start only above the configured threshold."""
        assert CleanupConfig.should_use_chunked_processing(CleanupConfig.CHUNKED_PROCESSING_THRESHOLD) is False
        assert CleanupConfig.should_use_chunked_processing(CleanupConfig.CHUNKED_PROCESSING_THRESHOLD + 1) is True
        assert CleanupConfig.get_chunk_size() == CleanupConfig.CHUNK_SIZE
