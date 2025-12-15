"""Text processing utilities for TTS preparation."""

import re
import logging
from typing import Tuple

try:
    import markdown
    from bs4 import BeautifulSoup
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("markdown and/or beautifulsoup4 not available, falling back to regex-based stripping")

logger = logging.getLogger(__name__)


class MarkdownStripper:
    """Utility class for stripping markdown syntax from text."""
    
    def __init__(self):
        """Initialize markdown stripper with library or regex fallback."""
        self.use_library = MARKDOWN_AVAILABLE
        
        if self.use_library:
            # Configure markdown processor
            self.md = markdown.Markdown(extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br'
            ])
            logger.debug("Using markdown library for text processing")
        else:
            logger.debug("Using regex-based markdown stripping")
        
        # Compile regex patterns for fallback or additional cleaning
        self.patterns = {
            # Headers (# ## ### etc.)
            'headers': re.compile(r'^#{1,6}\s+', re.MULTILINE),
            
            # Bold and italic (**text**, *text*, __text__, _text_)
            'bold_italic': re.compile(r'\*{1,2}([^*]+)\*{1,2}|_{1,2}([^_]+)_{1,2}'),
            
            # Code blocks (```code``` and `code`)
            'code_blocks': re.compile(r'```[\s\S]*?```'),
            'inline_code': re.compile(r'`([^`]+)`'),
            
            # Links [text](url) and ![alt](url)
            'links': re.compile(r'!?\[([^\]]*)\]\([^)]+\)'),
            
            # Strikethrough ~~text~~
            'strikethrough': re.compile(r'~~([^~]+)~~'),
            
            # Blockquotes (> text)
            'blockquotes': re.compile(r'^>\s*', re.MULTILINE),
            
            # Horizontal rules (--- or ***)
            'horizontal_rules': re.compile(r'^[-*]{3,}\s*$', re.MULTILINE),
            
            # Lists (- item, * item, 1. item)
            'lists': re.compile(r'^[\s]*[-*+]\s+|^\s*\d+\.\s+', re.MULTILINE),
            
            # Tables (| col | col |)
            'tables': re.compile(r'\|[^|\n]*\|', re.MULTILINE),
            
            # HTML tags
            'html_tags': re.compile(r'<[^>]+>'),
            
            # Escape sequences
            'escapes': re.compile(r'\\([\\`*_{}[\]()#+\-.!])'),
        }
    
    def strip_markdown(self, text: str) -> str:
        """
        Strip markdown syntax from text, preserving readable content.
        
        Args:
            text: Text with markdown syntax
            
        Returns:
            Clean text without markdown syntax
        """
        if not text:
            return text
        
        if self.use_library:
            return self._strip_markdown_with_library(text)
        else:
            return self._strip_markdown_with_regex(text)
    
    def _strip_markdown_with_library(self, text: str) -> str:
        """Strip markdown using the markdown library and BeautifulSoup."""
        try:
            # Convert markdown to HTML
            html = self.md.convert(text)
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Handle images and links specially to preserve alt text and link text
            for img in soup.find_all('img'):
                if img.get('alt'):
                    img.replace_with(img['alt'])
                else:
                    img.decompose()
            
            # Get text content, preserving some structure
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up extra whitespace
            clean_text = re.sub(r'\s+', ' ', clean_text)  # Multiple spaces to single
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)  # Clean up newlines
            clean_text = clean_text.strip()
            
            # Reset markdown processor for next use
            self.md.reset()
            
            return clean_text
            
        except Exception as e:
            logger.warning(f"Library-based markdown stripping failed: {e}, falling back to regex")
            return self._strip_markdown_with_regex(text)
    
    def _strip_markdown_with_regex(self, text: str) -> str:
        """Strip markdown using regex patterns (fallback method)."""
        # Start with original text
        clean_text = text
        
        # Remove code blocks first (preserve content inside, remove language identifier)
        def replace_code_block(match):
            content = match.group(0)[3:-3].strip()  # Remove ``` from both ends
            # Remove language identifier from first line if present
            lines = content.split('\n')
            if lines and not lines[0].strip().startswith((' ', '\t')):
                # First line might be language identifier, remove it
                if len(lines) > 1:
                    return '\n'.join(lines[1:])
                else:
                    return lines[0]  # Single line, keep it
            return content
        
        clean_text = self.patterns['code_blocks'].sub(replace_code_block, clean_text)
        
        # Remove inline code (preserve content)
        clean_text = self.patterns['inline_code'].sub(r'\1', clean_text)
        
        # Remove headers (keep text)
        clean_text = self.patterns['headers'].sub('', clean_text)
        
        # Remove bold/italic (keep text)
        clean_text = self.patterns['bold_italic'].sub(r'\1\2', clean_text)
        
        # Remove links (keep link text)
        clean_text = self.patterns['links'].sub(r'\1', clean_text)
        
        # Remove strikethrough (keep text)
        clean_text = self.patterns['strikethrough'].sub(r'\1', clean_text)
        
        # Remove blockquotes
        clean_text = self.patterns['blockquotes'].sub('', clean_text)
        
        # Remove horizontal rules
        clean_text = self.patterns['horizontal_rules'].sub('', clean_text)
        
        # Remove list markers
        clean_text = self.patterns['lists'].sub('', clean_text)
        
        # Remove table syntax (keep content between pipes)
        clean_text = self.patterns['tables'].sub(lambda m: m.group(0).replace('|', ' '), clean_text)
        
        # Remove HTML tags
        clean_text = self.patterns['html_tags'].sub('', clean_text)
        
        # Handle escape sequences
        clean_text = self.patterns['escapes'].sub(r'\1', clean_text)
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)  # Multiple newlines to double
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Multiple spaces to single
        clean_text = clean_text.strip()
        
        return clean_text
    
    def strip_and_truncate(self, text: str, max_bytes: int = 3500) -> Tuple[str, bool]:
        """
        Strip markdown and truncate text to fit within byte limit.
        
        Args:
            text: Text with markdown syntax
            max_bytes: Maximum bytes allowed (default 3500 for Gemini TTS)
            
        Returns:
            Tuple of (processed_text, was_truncated)
        """
        # First strip markdown
        clean_text = self.strip_markdown(text)
        
        # Check if we need to truncate
        text_bytes = len(clean_text.encode('utf-8'))
        
        if text_bytes <= max_bytes:
            return clean_text, False
        
        # Need to truncate - do it intelligently
        logger.warning(f"Text too long ({text_bytes} bytes), truncating to {max_bytes} bytes")
        
        # Try to truncate at sentence boundaries
        sentences = re.split(r'[.!?]+\s+', clean_text)
        truncated_text = ""
        
        for sentence in sentences:
            test_text = truncated_text + sentence + ". "
            if len(test_text.encode('utf-8')) > max_bytes:
                break
            truncated_text = test_text
        
        # If no complete sentences fit, truncate by words
        if not truncated_text:
            words = clean_text.split()
            truncated_text = ""
            
            for word in words:
                test_text = truncated_text + word + " "
                if len(test_text.encode('utf-8')) > max_bytes:
                    break
                truncated_text = test_text
        
        # Final fallback - truncate by bytes (might break UTF-8)
        if not truncated_text:
            truncated_text = clean_text.encode('utf-8')[:max_bytes].decode('utf-8', errors='ignore')
        
        return truncated_text.strip(), True


class TTSTextProcessor:
    """Text processor specifically for TTS preparation."""
    
    def __init__(self):
        """Initialize TTS text processor."""
        self.markdown_stripper = MarkdownStripper()
    
    def prepare_text_for_tts(
        self, 
        text: str, 
        style_prompt: str = "", 
        max_total_bytes: int = 3800
    ) -> Tuple[str, str, bool]:
        """
        Prepare text and style prompt for TTS, ensuring size limits.
        
        Args:
            text: Original text content
            style_prompt: Style prompt for TTS
            max_total_bytes: Maximum total bytes for text + prompt
            
        Returns:
            Tuple of (processed_text, processed_prompt, was_truncated)
        """
        # Strip markdown from text first
        clean_text = self.markdown_stripper.strip_markdown(text)
        
        # Calculate total size after markdown stripping
        text_bytes = len(clean_text.encode('utf-8'))
        prompt_bytes = len(style_prompt.encode('utf-8'))
        total_bytes = text_bytes + prompt_bytes
        
        # Check if we need to truncate
        if total_bytes <= max_total_bytes:
            # No truncation needed
            return clean_text, style_prompt, False
        
        # Text is too long - we'll need to truncate
        logger.warning(f"Text too long ({total_bytes} bytes), truncating to {max_total_bytes} bytes")
        
        # Reserve space for style prompt (minimum 200 bytes, maximum half of limit)
        prompt_reserve = min(max(prompt_bytes, 200), max_total_bytes // 2)
        text_limit = max_total_bytes - prompt_reserve - 100  # Leave 100 byte buffer
        
        # Truncate text intelligently
        clean_text, text_truncated = self.markdown_stripper.strip_and_truncate(
            text, max_bytes=text_limit
        )
        
        # Truncate style prompt if still needed
        remaining_bytes = max_total_bytes - len(clean_text.encode('utf-8')) - 100
        prompt_truncated = False
        
        if len(style_prompt.encode('utf-8')) > remaining_bytes:
            logger.warning(f"Style prompt too long, truncating to {remaining_bytes} bytes")
            style_prompt = style_prompt.encode('utf-8')[:remaining_bytes].decode('utf-8', errors='ignore')
            prompt_truncated = True
        
        was_truncated = text_truncated or prompt_truncated
        final_total = len(clean_text.encode('utf-8')) + len(style_prompt.encode('utf-8'))
        
        logger.info(f"Text processed for TTS: {final_total} bytes (truncated: {was_truncated})")
        
        return clean_text, style_prompt, was_truncated
    
    def check_size_for_gemini_tts(
        self,
        text: str,
        style_prompt: str = "",
        max_bytes: int = 3800
    ) -> bool:
        """
        Check if text and style prompt would fit within Gemini TTS size limits.
        
        Args:
            text: Text content
            style_prompt: Style prompt
            max_bytes: Maximum allowed bytes
            
        Returns:
            True if content fits within limits, False otherwise
        """
        # Strip markdown first
        clean_text = self.markdown_stripper.strip_markdown(text)
        
        # Calculate total size
        total_bytes = len(clean_text.encode('utf-8')) + len(style_prompt.encode('utf-8'))
        
        return total_bytes <= max_bytes


# Global instances for easy import
markdown_stripper = MarkdownStripper()
tts_text_processor = TTSTextProcessor()


def strip_markdown(text: str) -> str:
    """Convenience function to strip markdown from text."""
    return markdown_stripper.strip_markdown(text)


def prepare_text_for_tts(text: str, style_prompt: str = "") -> Tuple[str, str, bool]:
    """Convenience function to prepare text for TTS."""
    return tts_text_processor.prepare_text_for_tts(text, style_prompt)


def check_gemini_tts_size_limit(text: str, style_prompt: str = "") -> bool:
    """Convenience function to check if content fits Gemini TTS size limits."""
    return tts_text_processor.check_size_for_gemini_tts(text, style_prompt)