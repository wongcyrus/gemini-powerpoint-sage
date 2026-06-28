# Performance & Caching Guide

## Overview

The Gemini PowerPoint Sage includes advanced performance optimizations through intelligent caching and TTS integration that dramatically improve processing speed and reliability.

## 🚀 Prompt Rewriter Caching

### Performance Impact
- **Before**: 110+ seconds per style combination (4 sequential LLM calls)
- **After**: <1 second for cached results
- **Cache Hit Rate**: Typically 80%+ after initial runs
- **Storage**: Efficient file-based persistence with automatic cleanup

### How It Works

The system caches the results of prompt rewriting operations using:

1. **SHA-256 Hash Keys**: Generated from base prompt + style + prompt type
2. **JSON File Storage**: Persistent across application restarts
3. **TTL Management**: Configurable expiration (default: 30 days)
4. **Size Limits**: Automatic cleanup when cache exceeds limits (default: 100MB)
5. **Metadata Tracking**: Hit rates, performance metrics, and statistics

### Cache Configuration

```bash
# Environment Variables
export PROMPT_CACHE_ENABLED=true              # Enable/disable (default: true)
export PROMPT_CACHE_DIR=cache/prompt_rewriter  # Directory (default: cache/prompt_rewriter)
export PROMPT_CACHE_MAX_SIZE_MB=100           # Size limit (default: 100MB)
export PROMPT_CACHE_TTL_DAYS=30               # Expiration (default: 30 days)
```

### Cache Statistics

The system provides detailed performance metrics:

```
CACHE PERFORMANCE SUMMARY
Status: ENABLED
Total Requests: 45
Cache Hits: 38
Cache Misses: 7
Hit Rate: 84.4%
Efficiency Rating: EXCELLENT
Storage: 2.34MB / 100MB
Entries: 23
Estimated Time Saved: 570s (9.5 min)
```

## 🎙️ TTS Integration

### Gemini TTS Engine

Advanced text-to-speech integration with:

- **Unified Configuration**: Single `MODEL_TTS` environment variable
- **Intelligent Timeouts**: Configurable via `TTS_TIMEOUT_SECONDS` (default: 90s)
- **Tone Validation**: Ensures valid tone values for synthesis
- **Multi-language Support**: 25+ languages with voice mapping
- **Error Resilience**: Exponential backoff retry with fallbacks

### TTS Configuration

```bash
# TTS Settings
export MODEL_TTS=gemini-2.5-flash-tts         # Model (default: gemini-2.5-flash-tts)
export TTS_TIMEOUT_SECONDS=90                 # Timeout (default: 90s)
export TTS_ENABLED=true                       # Enable/disable (default: true)
export TTS_CACHE_ENABLED=true                 # Cache audio (default: true)
```

### Supported Languages

The TTS system supports 25+ languages with intelligent voice selection:

- **English**: en-US (Aoede, Callirrhoe, Kore, Zephyr)
- **Chinese**: cmn-CN, cmn-TW (Mandarin variants)
- **Japanese**: ja-JP (Despina, Erinome, Laomedeia)
- **Korean**: ko-KR (Gacrux, Sulafat)
- **European**: fr-FR, de-DE, es-ES, it-IT, pt-BR, ru-RU
- **And more**: ar-EG, hi-IN, th-TH, vi-VN, etc.

## 📊 Performance Monitoring

### Cache Performance Metrics

Monitor cache effectiveness with built-in statistics:

```python
# Cache statistics are logged automatically
cache_stats = cache.get_cache_stats()
print(f"Hit Rate: {cache_stats['hit_rate']:.1%}")
print(f"Storage: {cache_stats['total_size_mb']:.2f}MB")
```

### TTS Performance

TTS operations include comprehensive error handling:

- **Timeout Protection**: Prevents hanging on slow network/API responses
- **Retry Logic**: Exponential backoff for transient failures
- **Tone Validation**: Automatic mapping to valid tone values
- **Quality Validation**: MP3 format verification and metadata extraction

## 🛠️ Troubleshooting

### Cache Issues

**Cache not working?**
1. Check `PROMPT_CACHE_ENABLED=true`
2. Verify cache directory permissions
3. Check disk space for cache storage

**Cache too large?**
1. Reduce `PROMPT_CACHE_MAX_SIZE_MB`
2. Lower `PROMPT_CACHE_TTL_DAYS`
3. Manual cleanup: delete `cache/prompt_rewriter/*`

### TTS Issues

**TTS timeouts?**
1. Increase `TTS_TIMEOUT_SECONDS` (try 120 or 180)
2. Check network connectivity
3. Verify Google Cloud credentials

**Invalid tone errors?**
1. System automatically maps invalid tones to valid ones
2. Valid tones: professional, casual, enthusiastic, technical, narrative
3. Check logs for tone mapping messages

## 🔧 Advanced Configuration

### Custom Cache Directory

```bash
# Use custom cache location
export PROMPT_CACHE_DIR=/path/to/custom/cache
python main.py --styles
```

### Performance Tuning

```bash
# High-performance setup
export PROMPT_CACHE_MAX_SIZE_MB=500    # Larger cache
export PROMPT_CACHE_TTL_DAYS=90        # Longer retention
export TTS_TIMEOUT_SECONDS=120         # More generous timeout
```

### Development Mode

```bash
# Disable caching for development
export PROMPT_CACHE_ENABLED=false
export TTS_CACHE_ENABLED=false
python main.py --config configs/test.yaml
```

## 📈 Best Practices

1. **Keep caching enabled** for production use
2. **Monitor cache hit rates** - should be >50% for good performance
3. **Use appropriate timeouts** - balance speed vs reliability
4. **Regular cache cleanup** - system handles this automatically
5. **Test with cache disabled** during development to ensure correctness

The caching and TTS systems work together to provide a fast, reliable, and scalable presentation enhancement experience.