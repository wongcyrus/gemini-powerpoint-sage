# File Naming Conventions

## Overview

The Gemini PowerPoint Sage uses a systematic file naming convention to organize outputs across multiple languages, styles, and processing stages. This document explains the logic behind all file naming patterns used throughout the system.

## Core Naming Principles

### 1. Language-Specific Suffixes
All output files include language codes to prevent conflicts and enable parallel processing:

```
{base_name}_{language_code}_{file_type}.{extension}
```

**Examples:**
- `presentation_en_with_notes.pptx` (English)
- `presentation_zh-CN_with_notes.pptx` (Simplified Chinese)
- `presentation_yue-HK_progress.json` (Cantonese)

### 2. Content Hash Integration
Files that depend on content include hash suffixes for cache invalidation:

```
{base_name}_{slide_number}_{content_hash}.{extension}
```

**Examples:**
- `slide_5_abc123.mp3` (TTS audio with content hash)
- `slide_1_a1b2c3d4` (Progress JSON key with content hash)

### 3. Natural Number Sorting
All numbered files use zero-padded or natural sorting to ensure correct order:

```
slide_1.png, slide_2.png, ..., slide_10.png, slide_11.png
```

**Not:** `slide_1.png, slide_10.png, slide_11.png, slide_2.png` (lexicographic)

## File Type Categories

### 1. Presentation Files

#### Input Files
```
presentation.pptx          # Original PowerPoint file
presentation.pdf           # PDF export for content analysis
```

#### Output Files
```
{name}_{lang}_with_notes.pptx     # Slides with speaker notes
{name}_{lang}_with_visuals.pptx   # Slides with AI-generated visuals
```

**Examples:**
- `lecture_en_with_notes.pptx`
- `lecture_zh-CN_with_visuals.pptx`

### 2. Progress Tracking Files

#### Progress JSON
```
{name}_{lang}_progress.json       # Processing progress and metadata
```

**Structure:**
```json
{
  "slides": {
    "slide_1_abc123": {
      "slide_index": 1,
      "existing_notes_hash": "abc123",
      "note": "Generated speaker notes...",
      "status": "success"
    }
  },
  "global_context": "Presentation overview..."
}
```

#### Refined Progress (TTS-optimized)
```
{name}_{lang}_progress_refined.json   # TTS-optimized version
```

### 3. Visual Assets

#### Generated Images Directory
```
{name}_{lang}_visuals/            # Directory containing slide images
├── slide_1_reimagined.png        # AI-generated slide 1
├── slide_2_reimagined.png        # AI-generated slide 2
└── slide_N_reimagined.png        # AI-generated slide N
```

#### Image Naming Pattern
```
slide_{number}_reimagined.{ext}
```

**Supported Extensions:** `.png`, `.jpg`, `.jpeg`

### 4. Audio Files

#### TTS Audio Directory
```
{name}_{lang}_speech/             # Directory containing audio files
├── slide_1_abc123.mp3           # TTS audio for slide 1
├── slide_2_def456.mp3           # TTS audio for slide 2
└── slide_N_xyz789.mp3           # TTS audio for slide N
```

#### Audio Naming Pattern
```
slide_{number}_{content_hash}.mp3
```

**Content Hash:** SHA-256 hash of speaker notes content (first 8 characters)

### 5. Video Files

#### Video Segments Cache
```
{name}_{lang}_segments/           # Cached video segments
├── slide_1_abc123.mp4           # Cached segment for slide 1
├── slide_2_def456.mp4           # Cached segment for slide 2
└── slide_N_xyz789.mp4           # Cached segment for slide N
```

#### Final Video Output
```
{name}_{lang}.mp4                # Complete presentation video
```

**Examples:**
- `Introduction_to_Programming_en.mp4`
- `Introduction_to_Programming_zh-CN.mp4`

## Language Code Mapping

### Standard Language Codes
| User Code | Full Code | Language | Example Filename |
|-----------|-----------|----------|------------------|
| `en` | `en-US` | English | `lecture_en_progress.json` |
| `zh-CN` | `cmn-CN` | Simplified Chinese | `lecture_zh-CN_with_notes.pptx` |
| `zh-TW` | `cmn-TW` | Traditional Chinese | `lecture_zh-TW_progress.json` |
| `yue-HK` | `yue-HK` | Cantonese | `lecture_yue-HK_with_visuals.pptx` |
| `ja` | `ja-JP` | Japanese | `lecture_ja_speech/` |
| `ko` | `ko-KR` | Korean | `lecture_ko_visuals/` |

### TTS Engine Mapping
Different TTS engines use different language codes:

**Gemini TTS:**
- `zh-CN` → `cmn-CN`
- `zh-TW` → `cmn-TW`

**Traditional TTS:**
- `zh-CN` → `cmn-CN`
- `yue-HK` → `yue-HK` (no mapping)

## Directory Structure Examples

### Single File Processing
```
input/
├── presentation.pptx
├── presentation.pdf
├── presentation_en_with_notes.pptx
├── presentation_en_with_visuals.pptx
├── presentation_en_progress.json
├── presentation_en_visuals/
│   ├── slide_1_reimagined.png
│   └── slide_2_reimagined.png
├── presentation_en_speech/
│   ├── slide_1_abc123.mp3
│   └── slide_2_def456.mp3
├── presentation_en_segments/
│   ├── slide_1_abc123.mp4
│   └── slide_2_def456.mp4
└── presentation_en.mp4
```

### Style-Based Processing
```
notes/cyberpunk/generate/
├── lecture_en_notes.pptm
├── lecture_en_visuals.pptm
├── lecture_en_progress.json
├── lecture_en_visuals/
├── lecture_en_speech/
├── lecture_en_segments/
├── lecture_zh-CN_notes.pptm
├── lecture_zh-CN_visuals.pptm
├── lecture_zh-CN_progress.json
├── lecture_zh-CN_visuals/
├── lecture_zh-CN_speech/
└── lecture_zh-CN_segments/
```

## File Pairing Logic

### 1:1:1 Correspondence
The system maintains strict 1:1:1 correspondence between:
- Slide images (`slide_N_reimagined.png`)
- Audio files (`slide_N_hash.mp3`)
- Video segments (`slide_N_hash.mp4`)

### Natural Sorting
Files are sorted using natural number ordering:

```python
# Correct order
slide_1.png, slide_2.png, ..., slide_10.png, slide_11.png

# Incorrect lexicographic order
slide_1.png, slide_10.png, slide_11.png, slide_2.png
```

### Slide Number Extraction
The system extracts slide numbers using regex patterns:

```python
# Pattern: slide_(\d+)
"slide_5_reimagined.png" → 5
"slide_10_abc123.mp3" → 10
```

## Content Hash System

### Purpose
Content hashes ensure cache invalidation when speaker notes change:

```python
# Same content = same hash = reuse cached audio
"Welcome to the presentation" → "abc123"

# Different content = different hash = regenerate audio
"Welcome to our presentation" → "def456"
```

### Hash Generation
- **Algorithm:** SHA-256
- **Length:** First 8 characters
- **Input:** Speaker notes text content

### Cache Benefits
- **Speed:** Avoid regenerating unchanged audio
- **Cost:** Reduce TTS API calls
- **Consistency:** Same content produces same output

## Error Handling Patterns

### Missing Files
When files are missing, the naming convention helps identify gaps:

```
✅ slide_1_reimagined.png + slide_1_abc123.mp3
✅ slide_2_reimagined.png + slide_2_def456.mp3
❌ slide_3_reimagined.png MISSING
✅ slide_4_reimagined.png + slide_3_ghi789.mp3  # MISALIGNED!
```

### Status Tracking
Progress files track status per slide:

```json
{
  "slides": {
    "slide_3_xyz789": {
      "slide_index": 3,
      "status": "error",
      "error_message": "TTS generation failed"
    }
  }
}
```

## Configuration Patterns

### TTS Configuration
```python
# Directory pattern
"{base_name}_{language_code}_speech"

# Filename pattern  
"slide_{slide_number}_{content_hash}.mp3"
```

### Video Cache Configuration
```python
# Cache directory (derived from speech directory)
speech_dir = "presentation_en_speech"
cache_dir = "presentation_en_segments"  # Replace _speech with _segments
```

## Best Practices

### 1. Consistent Naming
Always use the established patterns:
- Include language codes in all outputs
- Use natural number sorting for sequences
- Include content hashes for cache-dependent files

### 2. Directory Organization
Group related files by language and type:
```
presentation_en_visuals/     # All English visuals
presentation_en_speech/      # All English audio
presentation_zh-CN_visuals/  # All Chinese visuals
presentation_zh-CN_speech/   # All Chinese audio
```

### 3. File Verification
Always verify 1:1:1 correspondence before video synthesis:
```bash
python tools/verify_1to1_correspondence.py --presentation "lecture" --language "en"
```

### 4. Cleanup Patterns
Use wildcards for language-specific cleanup:
```bash
# Remove all Chinese files
rm -rf *_zh-CN_*

# Remove all cached segments
rm -rf *_segments/
```

## Tools and Utilities

### File Sorting
- `utils/file_sorting.py` - Natural sorting utilities
- `natural_sort_files()` - Sort file lists correctly
- `extract_slide_number()` - Extract slide numbers from filenames

### Verification
- `tools/verify_1to1_correspondence.py` - Check file pairing
- `tools/check_existing_videos.py` - Verify video outputs

### Cache Management
- Video cache stats: `python main.py --video-cache-stats`
- Clear cache: `python main.py --video-clear-cache 7`

## Migration Notes

### From Legacy Naming
If migrating from older naming conventions:

1. **Add language suffixes** to all files
2. **Update progress JSON keys** to include content hashes
3. **Reorganize directories** by language
4. **Update configuration files** to use new patterns

### Backward Compatibility
The system maintains backward compatibility by:
- Detecting old naming patterns
- Auto-migrating when possible
- Providing clear error messages for unsupported formats

---

This naming convention ensures consistent, predictable file organization that supports multi-language processing, caching, and parallel execution while maintaining clear relationships between related files.