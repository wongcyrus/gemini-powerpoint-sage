"""Tests for markdown stripping and TTS text preparation."""

from utils.text_processing import (
    MarkdownStripper,
    TTSTextProcessor,
    check_gemini_tts_size_limit,
    prepare_text_for_tts,
    strip_markdown,
)


class TestMarkdownStripper:
    """Tests for markdown cleanup."""

    def test_strip_markdown_with_regex_handles_common_syntax(self):
        """Regex fallback should preserve readable content while removing markdown syntax."""
        stripper = MarkdownStripper()
        stripper.use_library = False
        text = (
            "# Title\n"
            "- **Bold** item with [link](https://example.com)\n"
            "> quote\n"
            "`inline`\n"
            "~~gone~~\n"
            "| a | b |\n"
            "<b>html</b>"
        )

        cleaned = stripper.strip_markdown(text)

        assert "Title" in cleaned
        assert "Bold" in cleaned
        assert "link" in cleaned
        assert "quote" in cleaned
        assert "inline" in cleaned
        assert "gone" in cleaned
        assert "html" in cleaned
        assert "**" not in cleaned
        assert "[" not in cleaned

    def test_strip_markdown_with_regex_handles_code_blocks(self):
        """Code block stripping should drop fences while keeping meaningful content."""
        stripper = MarkdownStripper()
        stripper.use_library = False

        cleaned = stripper.strip_markdown("```python\nprint('hi')\n```")

        assert "print('hi')" in cleaned
        assert "```" not in cleaned

    def test_strip_and_truncate_prefers_sentence_boundaries(self):
        """Truncation should keep full sentences when they fit within the limit."""
        stripper = MarkdownStripper()
        stripper.use_library = False
        text = "First sentence is short. Second sentence is also short. Third sentence is much longer than the rest."

        truncated, was_truncated = stripper.strip_and_truncate(text, max_bytes=45)

        assert was_truncated is True
        assert truncated.endswith(".")
        assert "First sentence is short." in truncated

    def test_strip_and_truncate_falls_back_to_word_boundaries(self):
        """Long unpunctuated content should truncate by words."""
        stripper = MarkdownStripper()
        stripper.use_library = False
        text = "word " * 200

        truncated, was_truncated = stripper.strip_and_truncate(text, max_bytes=40)

        assert was_truncated is True
        assert len(truncated.encode("utf-8")) <= 40


class TestTTSTextProcessor:
    """Tests for TTS text processing."""

    def test_prepare_text_for_tts_returns_clean_text_when_under_limit(self):
        """Small inputs should be cleaned without truncation."""
        text, prompt, truncated = prepare_text_for_tts("# Hello **world**", "style")

        assert text == "Hello world"
        assert prompt == "style"
        assert truncated is False

    def test_prepare_text_for_tts_truncates_text_and_prompt_when_needed(self):
        """Large inputs should be trimmed to fit the combined byte budget."""
        processor = TTSTextProcessor()
        processor.markdown_stripper.use_library = False
        text = "Sentence one. " * 200
        prompt = "Prompt " * 200

        clean_text, clean_prompt, truncated = processor.prepare_text_for_tts(
            text,
            prompt,
            max_total_bytes=300,
        )

        assert truncated is True
        assert len(clean_text.encode("utf-8")) + len(clean_prompt.encode("utf-8")) <= 300

    def test_check_size_for_gemini_tts_uses_cleaned_text_length(self):
        """Size checks should be based on markdown-stripped content."""
        processor = TTSTextProcessor()
        processor.markdown_stripper.use_library = False

        assert processor.check_size_for_gemini_tts("# Hello **world**", "", max_bytes=20) is True
        assert processor.check_size_for_gemini_tts("A" * 100, "", max_bytes=20) is False

    def test_convenience_strip_markdown_uses_global_processor(self):
        """Convenience helpers should expose the same stripping behavior."""
        cleaned = strip_markdown("## Header\nSome **bold** text")

        assert "Header" in cleaned
        assert "**" not in cleaned

    def test_convenience_size_check_uses_global_tts_processor(self):
        """Global size checks should return a boolean result."""
        assert check_gemini_tts_size_limit("small text", "") is True

    def test_strip_markdown_with_library_uses_html_parser(self, monkeypatch):
        """Library mode should preserve text from HTML conversion output."""
        stripper = MarkdownStripper()
        stripper.use_library = True
        stripper.md.convert = lambda text: "<h1>Title</h1><p>Body <a href='x'>link</a><img alt='alt text' /></p>"

        cleaned = stripper.strip_markdown("ignored")

        assert "Title" in cleaned
        assert "Body" in cleaned
        assert "link" in cleaned
        assert "alt text" in cleaned
