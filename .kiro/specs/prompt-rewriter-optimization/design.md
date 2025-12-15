# Design Document

## Overview

The prompt rewriter optimization focuses on implementing a simple file-based caching system to eliminate redundant LLM API calls. The current system makes 4 LLM calls per language (designer, writer, title generator, translator) taking ~110 seconds total. With caching, subsequent runs with the same style configuration will complete in under 1 second.

## Architecture

The caching system will be integrated into the existing `PromptRewriter` class with minimal changes to the public interface. The cache will use a hash-based key system to identify unique combinations of base prompts and style guidelines.

### Cache Key Strategy
- Hash input: `base_prompt + style_guidelines + prompt_type`
- Use SHA-256 for reliable, collision-resistant keys
- Store as JSON files with `.cache` extension

### Cache Storage Structure
```
cache/
└── prompt_rewriter/
    ├── cache_metadata.json
    ├── designer_abc123def.cache
    ├── writer_def456ghi.cache
    ├── title_jkl789mno.cache
    └── translator_pqr012stu.cache
```

## Components and Interfaces

### PromptCache Class
New component to handle all caching operations:

```python
class PromptCache:
    def __init__(self, cache_dir: str = "cache/prompt_rewriter")
    def get_cached_prompt(self, cache_key: str) -> Optional[str]
    def store_prompt(self, cache_key: str, rewritten_prompt: str) -> bool
    def generate_cache_key(self, base_prompt: str, style: str, prompt_type: str) -> str
    def is_cache_valid(self, cache_key: str) -> bool
    def clear_cache(self) -> None
```

### Modified PromptRewriter Methods
Each rewriting method will follow this pattern:
1. Generate cache key from inputs
2. Check cache for existing result
3. Return cached result if found
4. Perform LLM rewriting if cache miss
5. Store result in cache
6. Return rewritten prompt

## Data Models

### Cache Entry Format
```json
{
  "cache_key": "designer_abc123def456",
  "prompt_type": "designer",
  "base_prompt_hash": "abc123",
  "style_hash": "def456",
  "rewritten_prompt": "...",
  "created_at": "2025-12-15T15:10:40Z",
  "accessed_at": "2025-12-15T15:10:40Z"
}
```

### Cache Metadata Format
```json
{
  "version": "1.0",
  "created_at": "2025-12-15T15:10:40Z",
  "total_entries": 12,
  "cache_hits": 45,
  "cache_misses": 12,
  "last_cleanup": "2025-12-15T15:10:40Z"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Cache hit performance
*For any* cached prompt request, the response time should be under 1 second when cache exists
**Validates: Requirements 1.3**

Property 2: Cache storage consistency  
*For any* successful LLM rewrite operation, the result should be stored in cache with the correct hash key
**Validates: Requirements 2.1**

Property 3: Cache key uniqueness
*For any* two different combinations of base prompt and style guidelines, the generated cache keys should be different
**Validates: Requirements 2.3**

Property 4: Cache persistence
*For any* cached entry, it should remain available after system restart until explicitly invalidated
**Validates: Requirements 2.5**

Property 5: Fallback reliability
*For any* LLM failure scenario, the system should continue processing using concatenation fallback without throwing exceptions
**Validates: Requirements 4.1, 4.5**

Property 6: Cache directory initialization
*For any* system startup, if cache directory doesn't exist, it should be created automatically
**Validates: Requirements 3.1, 3.2**

## Error Handling

The caching system implements multiple layers of error handling:

1. **Cache File Corruption**: Invalid JSON files are deleted and regenerated
2. **Disk Space Issues**: Cache size limits prevent unbounded growth
3. **Permission Errors**: Graceful degradation to non-cached operation
4. **LLM API Failures**: Automatic fallback to concatenation method

## Testing Strategy

**Dual testing approach**:

**Unit Testing**:
- Cache key generation with various inputs
- File I/O operations and error conditions
- Cache hit/miss scenarios
- Fallback behavior under failure conditions

**Property-Based Testing**:
- Use Hypothesis library for Python property-based testing
- Configure each property test to run minimum 100 iterations
- Each property test tagged with format: '**Feature: prompt-rewriter-optimization, Property {number}: {property_text}**'
- Test cache consistency across random prompt/style combinations
- Verify performance characteristics under various load conditions
- Test error recovery with randomly corrupted cache states

## Implementation Details

### Cache Key Generation
```python
def generate_cache_key(self, base_prompt: str, style: str, prompt_type: str) -> str:
    content = f"{base_prompt}|{style}|{prompt_type}"
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return f"{prompt_type}_{hash_obj.hexdigest()[:16]}"
```

### Cache File Management
- JSON format for human readability and debugging
- Atomic writes using temporary files to prevent corruption
- Metadata tracking for cache statistics and cleanup
- Configurable cache size limits via environment variables

### Integration Points
- Minimal changes to existing `PromptRewriter` class
- Cache operations wrapped in try-catch for graceful degradation
- Logging integration for cache hit/miss tracking
- Environment variable configuration for cache settings

### Performance Expectations
- **Cache Hit**: < 1 second (file read + JSON parse)
- **Cache Miss**: Current LLM time + cache write overhead (~1-2 seconds)
- **Cache Storage**: ~1-5KB per cached prompt
- **Memory Usage**: Minimal (no in-memory cache, file-based only)

### Configuration Options
```bash
# Environment variables
PROMPT_CACHE_ENABLED=true
PROMPT_CACHE_DIR=cache/prompt_rewriter
PROMPT_CACHE_MAX_SIZE_MB=100
PROMPT_CACHE_TTL_DAYS=30
```

## Migration Strategy

1. **Phase 1**: Add caching to existing methods without changing interfaces
2. **Phase 2**: Deploy with caching enabled, monitor performance improvements
3. **Phase 3**: Add cache management utilities (clear, stats, cleanup)

The implementation maintains full backward compatibility - if caching fails, the system falls back to current LLM rewriting behavior.