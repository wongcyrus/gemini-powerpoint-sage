# Requirements Document

## Introduction

The prompt rewriter service is experiencing significant performance issues, taking over 110 seconds per language to rewrite agent prompts. This creates a poor user experience and blocks the presentation processing pipeline. We need to optimize the prompt rewriting process to reduce latency while maintaining quality.

## Glossary

- **Prompt Rewriter**: Service that integrates style guidelines into base agent prompts using LLM processing
- **Agent Factory**: Component that creates styled agents for presentation processing
- **Style Guidelines**: Visual and speaker style descriptions used to customize agent behavior
- **LLM Rewriting**: Process of using a language model to intelligently combine base prompts with styles
- **Session Management**: Creation and management of LLM runner sessions for API calls

## Requirements

### Requirement 1

**User Story:** As a user, I want prompt rewriting to complete quickly, so that presentation processing doesn't have long delays.

#### Acceptance Criteria

1. WHEN the system processes agent prompts THEN the system SHALL cache rewritten prompts to avoid redundant LLM processing
2. WHEN the same style configuration is used multiple times THEN the system SHALL reuse cached results immediately
3. WHEN cached results exist THEN the rewriting SHALL complete in under 1 second
4. WHEN no cache exists THEN the system SHALL perform LLM rewriting and cache the result
5. WHEN LLM calls fail THEN the system SHALL fall back to simple concatenation without blocking the pipeline

### Requirement 2

**User Story:** As a developer, I want efficient caching mechanisms, so that repeated style applications don't require expensive LLM calls.

#### Acceptance Criteria

1. WHEN a prompt is rewritten with specific style guidelines THEN the system SHALL cache the result with a hash key
2. WHEN the same base prompt and style combination is requested THEN the system SHALL return the cached result immediately
3. WHEN style guidelines change THEN the system SHALL invalidate related cache entries
4. WHEN cache storage exceeds limits THEN the system SHALL implement LRU eviction policy
5. WHEN the system starts up THEN the cache SHALL persist across application restarts

### Requirement 3

**User Story:** As a system administrator, I want simple cache configuration, so that caching works reliably without complex setup.

#### Acceptance Criteria

1. WHEN the system starts THEN the cache SHALL initialize automatically with default settings
2. WHEN cache directory doesn't exist THEN the system SHALL create it automatically
3. WHEN cache files become corrupted THEN the system SHALL handle errors gracefully and rebuild cache
4. WHEN disk space is limited THEN the system SHALL implement basic cache size limits
5. WHEN cache settings need changes THEN the system SHALL use simple environment variables

### Requirement 4

**User Story:** As a user, I want reliable fallback mechanisms, so that prompt rewriting never completely fails and blocks processing.

#### Acceptance Criteria

1. WHEN LLM rewriting fails after retries THEN the system SHALL use intelligent concatenation as fallback
2. WHEN API rate limits are hit THEN the system SHALL queue requests and retry with exponential backoff
3. WHEN network connectivity issues occur THEN the system SHALL use cached results or fallback methods
4. WHEN the fallback method is used THEN the system SHALL log the reason and maintain functionality
5. WHEN critical errors occur THEN the system SHALL continue processing with degraded prompt quality rather than failing

### Requirement 5

**User Story:** As a developer, I want basic performance logging, so that I can see cache effectiveness.

#### Acceptance Criteria

1. WHEN cache hits occur THEN the system SHALL log cache hit with timing information
2. WHEN cache misses occur THEN the system SHALL log cache miss and LLM processing time
3. WHEN rewritten prompts are cached THEN the system SHALL log successful cache storage
4. WHEN cache operations fail THEN the system SHALL log errors with fallback behavior
5. WHEN the system starts THEN the system SHALL log cache initialization status