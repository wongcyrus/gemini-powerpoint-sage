# TTS Markdown Stripping and Size Limit Solution

## Problem Summary

Your TTS system was encountering two main issues:

1. **Request size exceeding Gemini TTS limits** - 3975 byte requests were too large for the 4000 byte limit
2. **Markdown syntax in text** - Raw markdown was being sent to TTS engines, causing poor speech quality

## Solution Implemented

### 1. Text Processing Utility (`utils/text_processing.py`)

Created a comprehensive text processing system with two main classes:

#### `MarkdownStripper`
- Strips all markdown syntax while preserving readable content
- Handles: headers, bold/italic, code blocks, links, lists, blockquotes, tables, HTML tags
- Uses compiled regex patterns for performance
- Intelligent code block handling (removes language identifiers)

#### `TTSTextProcessor`
- Combines markdown stripping with size limit handling
- Ensures total request size stays under 3800 bytes (with buffer)
- Intelligent truncation at sentence/word boundaries
- Preserves text quality while meeting API limits

### 2. Engine Updates

#### Gemini TTS Engine (`services/tts/engines/gemini_tts_engine.py`)
- Added `prepare_text_for_tts()` call before synthesis
- Processes both text content and style prompts
- Logs truncation warnings when size limits are exceeded
- Includes metadata about truncation in results

#### Traditional TTS Engine (`services/tts/engines/traditional_tts_engine.py`)
- Added `strip_markdown()` call for text content
- Ensures clean text for SSML processing
- Maintains compatibility with existing SSML enhancement

### 3. Key Features

- **Automatic markdown removal**: Headers, bold, italic, code, links, lists, etc.
- **Size limit enforcement**: Keeps requests under Gemini TTS 4KB limit
- **Intelligent truncation**: Preserves sentence structure when possible
- **Logging and monitoring**: Tracks when truncation occurs
- **Backward compatibility**: Works with existing TTS pipeline

## Usage Examples

```python
from utils.text_processing import strip_markdown, prepare_text_for_tts

# Simple markdown stripping
clean_text = strip_markdown("# Title\n\nThis is **bold** text with `code`.")
# Result: "Title\n\nThis is bold text with code."

# TTS preparation with size limits
text = "# Long presentation content..."
style_prompt = "Speak professionally..."
processed_text, processed_prompt, was_truncated = prepare_text_for_tts(text, style_prompt)
```

## ✅ Enhanced with Libraries

Updated `requirements.txt` to include:
- `markdown>=3.5.0` - Robust markdown parsing
- `beautifulsoup4>=4.12.0` - HTML text extraction

The text processor now automatically uses these libraries when available, with regex fallback for compatibility.

## Testing

The solution has been tested with various markdown patterns:
- ✅ Headers (# ## ###)
- ✅ Bold and italic (**text**, *text*)
- ✅ Code blocks (```code```) and inline code (`code`)
- ✅ Links [text](url) and images ![alt](url)
- ✅ Lists (- item, 1. item)
- ✅ Blockquotes (> text)
- ✅ Size limit handling and intelligent truncation

## Impact

This solution should resolve both issues:
1. **No more "Request contains an invalid argument" errors** from oversized requests
2. **Better TTS quality** with clean text instead of raw markdown syntax
3. **Automatic fallback** to Traditional TTS when Gemini fails
4. **Preserved functionality** - all existing features continue to work

The TTS system will now automatically clean and size-limit all text before sending to either engine.