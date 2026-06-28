"""Tests for prompt cache behavior."""

import json
from datetime import datetime, timedelta

from services.prompt_cache import CacheEntry, PromptCache


class TestPromptCache:
    """Tests for file-based prompt caching."""

    def test_cache_initialization_creates_metadata(self, tmp_path, monkeypatch):
        """Creating a cache should initialize its metadata file."""
        monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")

        cache = PromptCache(cache_dir=str(tmp_path))

        assert cache.cache_enabled is True
        assert (tmp_path / "cache_metadata.json").exists()

    def test_generate_cache_key_is_stable_and_namespaced(self, tmp_path):
        """The same inputs should always produce the same prompt-type-prefixed key."""
        cache = PromptCache(cache_dir=str(tmp_path))

        first = cache.generate_cache_key("base", "style", "writer")
        second = cache.generate_cache_key("base", "style", "writer")

        assert first == second
        assert first.startswith("writer_")

    def test_store_and_retrieve_cached_prompt_round_trip(self, tmp_path):
        """Stored prompts should be retrievable and reflected in cache stats."""
        cache = PromptCache(cache_dir=str(tmp_path))
        cache_key = cache.generate_cache_key("base", "style", "writer")

        assert cache.store_prompt(cache_key, "rewritten", "writer", "base", "style") is True
        assert cache.get_cached_prompt(cache_key) == "rewritten"

        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 1
        assert stats["cache_hits"] >= 1
        assert stats["cache_misses"] >= 1

    def test_get_cached_prompt_removes_corrupted_files(self, tmp_path):
        """Corrupted cache files should be ignored and deleted."""
        cache = PromptCache(cache_dir=str(tmp_path))
        cache_file = tmp_path / "broken.cache"
        cache_file.write_text("{not json}", encoding="utf-8")

        assert cache.get_cached_prompt("broken") is None
        assert cache_file.exists() is False

    def test_is_cache_valid_respects_expiry(self, tmp_path):
        """Expired entries should no longer be considered valid."""
        cache = PromptCache(cache_dir=str(tmp_path))
        cache.ttl_days = 1
        old_entry = CacheEntry(
            cache_key="expired",
            prompt_type="writer",
            base_prompt_hash="a",
            style_hash="b",
            rewritten_prompt="old",
            created_at=(datetime.now() - timedelta(days=2)).isoformat(),
            accessed_at=datetime.now().isoformat(),
        )
        cache._save_cache_entry(old_entry)

        assert cache.is_cache_valid("expired") is False
        assert cache.get_cached_prompt("expired") is None

    def test_clear_cache_removes_entries_and_resets_metadata(self, tmp_path):
        """Clearing the cache should remove entries and reset counters."""
        cache = PromptCache(cache_dir=str(tmp_path))
        cache_key = cache.generate_cache_key("base", "style", "writer")
        cache.store_prompt(cache_key, "rewritten", "writer", "base", "style")

        cache.clear_cache()

        assert list(tmp_path.glob("*.cache")) == []
        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 0

    def test_get_cache_stats_handles_metadata_read_errors(self, tmp_path):
        """Stats should still return an error payload if metadata loading fails unexpectedly."""
        cache = PromptCache(cache_dir=str(tmp_path))
        metadata_path = tmp_path / "cache_metadata.json"
        metadata_path.write_text("{broken", encoding="utf-8")

        stats = cache.get_cache_stats()

        assert stats["enabled"] is True
