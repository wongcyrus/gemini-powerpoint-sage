# Caching Architecture - Source of Truth Documentation

## Overview

This document clarifies the source of truth for each caching system in the codebase to ensure consistent behavior and avoid confusion.

## Caching Systems Summary

| System | Source of Truth | Validation Method | Metadata File | Purpose |
|--------|----------------|-------------------|---------------|---------|
| **Prompt Cache** | File + JSON Content | File exists + JSON parse | ✅ `cache_metadata.json` | LLM prompt rewriting |
| **Video Segment Cache** | File Only | File exists | ❌ None | Video segment reuse |
| **TTS Audio Cache** | File Only | File exists | ❌ None | Audio file reuse |

## 1. Prompt Cache (services/prompt_cache.py)

**Source of Truth:** Both file existence AND JSON content validation

```python
# Validates both file existence and JSON structure
if not cache_file.exists():
    return None
try:
    with open(cache_file, 'r') as f:
        entry_data = json.load(f)  # Validates JSON
        entry = CacheEntry(**entry_data)  # Validates structure
except (json.JSONDecodeError, TypeError, ValueError):
    cache_file.unlink()  # Delete corrupted file
    return None
```

**Why JSON validation?**
- Prompt cache entries contain structured metadata (timestamps, hashes, etc.)
- Corrupted JSON files are automatically detected and removed
- Metadata file tracks statistics and cleanup history

**Files:**
- Cache entries: `cache/prompt_rewriter/*.cache`
- Metadata: `cache/prompt_rewriter/cache_metadata.json`

## 2. Video Segment Cache (services/video_synthesis/file_manager.py)

**Source of Truth:** File existence only

```python
# Simple file existence check - no JSON validation
if cached_file.exists() and cached_file.is_file():
    return cached_file
```

**Why file-only?**
- Video segments are binary MP4 files, not JSON
- Cache key includes content hash, ensuring integrity
- No metadata needed - file presence indicates validity

**Files:**
- Cache entries: `<output_dir>/<presentation>_segments/slide_*.mp4`
- No metadata file

## 3. TTS Audio Cache (services/tts/tts_orchestrator.py)

**Source of Truth:** File existence only

```python
# SOURCE OF TRUTH: file existence only
if Path(output_file_path).exists():
    with open(output_file_path, 'rb') as f:
        audio_data = f.read()
```

**Why file-only?**
- Audio files are binary MP3 files, not JSON
- Filename includes content hash for integrity
- Direct file checking is faster than metadata lookups

**Files:**
- Cache entries: `output/[style]/generate/<presentation>_<lang>_speech/slide_*.mp3`
- No metadata file (config defines one but it's unused)

## Key Principles

### 1. File Existence is Always Checked First
All systems check if the file exists before attempting to read it.

### 2. JSON Validation Only When Necessary
Only the prompt cache validates JSON content because it stores structured metadata.

### 3. Binary Files Use File-Only Validation
Video and audio files rely on file existence + content hashes in filenames.

### 4. Metadata Files Are Optional
Only prompt cache uses metadata for statistics and cleanup tracking.

## Fixed Issues

### ❌ Before: TTS Cache Metadata Inconsistency
- Config defined `metadata_file: "cache_metadata.json"`
- But cache lookups ignored metadata completely
- Tool `fix_tts_cache_paths.py` updated unused metadata

### ✅ After: Consistent File-Only Approach
- Removed unused `metadata_file` from TTS config
- Clarified that TTS uses file existence only
- Deprecated `fix_tts_cache_paths.py` tool

### ❌ Before: Unclear Source of Truth
- Mixed patterns across different caching systems
- No documentation of validation approaches

### ✅ After: Clear Documentation
- Each system clearly documents its source of truth
- Consistent comments in code
- This architecture document

## Best Practices

### For New Caching Systems

1. **Binary Files (video, audio, images):**
   - Use file existence only
   - Include content hash in filename
   - No JSON metadata needed

2. **Structured Data (JSON, configuration):**
   - Validate both file existence AND content
   - Use metadata file for statistics
   - Handle corrupted files gracefully

3. **Cache Key Generation:**
   - Include all relevant inputs in hash
   - Use consistent hash algorithm (SHA256)
   - Keep keys short but unique

### Code Comments

Always include source of truth comments:

```python
# SOURCE OF TRUTH: file existence only
if file.exists():
    return file

# SOURCE OF TRUTH: file existence + JSON validation  
if file.exists():
    try:
        data = json.load(file)
    except json.JSONDecodeError:
        file.unlink()  # Remove corrupted file
        return None
```

## Migration Notes

If you need to change a caching system's validation approach:

1. **File-only → JSON validation:** Add metadata file and validation logic
2. **JSON validation → File-only:** Remove metadata dependencies and JSON parsing
3. **Always:** Update documentation and add clear comments

## Testing

Each caching system should test:

1. **Cache hits:** Valid files return expected content
2. **Cache misses:** Missing files return None
3. **Corruption handling:** Invalid files are handled gracefully
4. **Cleanup:** Expired/invalid entries are removed properly

For JSON-based caches, also test:
- Corrupted JSON files are deleted
- Metadata consistency after operations
- Statistics tracking accuracy