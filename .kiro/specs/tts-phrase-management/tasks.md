# Implementation Plan

- [x] 1. Set up TTS system foundation and core interfaces
  - Create directory structure for TTS services and engines
  - Define core data models and interfaces for TTS system
  - Set up configuration management for dual TTS engines
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.1 Create TTS data models and enums
  - Write Python interfaces for TTSResult, StyleContext, VoiceConfig
  - Implement TTSEngineType and PresentationType enums
  - Create SlideData dataclass for slide processing
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Write property test for data model validation
  - **Property 12: MP3 Format Compliance**
  - **Validates: Requirements 5.1**

- [x] 1.3 Set up TTS configuration system
  - Create TTS configuration classes with engine selection logic
  - Implement language-to-engine mapping for Gemini vs Traditional TTS
  - Add configuration validation and fallback settings
  - _Requirements: 3.1, 3.2_

- [x] 1.4 Create EngineSelector class
  - Implement engine selection logic based on language
  - Add voice configuration management for different engines
  - Create language support validation methods
  - _Requirements: 3.1, 3.2_

- [x] 1.5 Create CacheManager class
  - Implement content hash generation including style parameters
  - Add cache validation and file existence checking
  - Create metadata storage linking hashes to file locations
  - _Requirements: 2.1, 2.4, 2.5_

- [x] 1.6 Create StorageManager class
  - Implement directory structure creation following visual asset patterns
  - Add local file storage with organized paths
  - Create file organization with predictable naming patterns
  - _Requirements: 1.1, 1.3, 5.2_

- [ ]* 1.7 Write property test for engine selection
  - **Property 7: Engine Selection for Cantonese**
  - **Validates: Requirements 3.1**

- [x] 2. Implement TTS Style Adapter using existing PromptRewriter
  - Extend PromptRewriter system for TTS style prompt generation
  - Create speaker notes analysis and style extraction logic
  - Implement TTS-specific prompt generation methods
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 2.1 Implement TTSStyleAdapter class
  - Implement speaker notes analysis using pattern matching
  - Create style guidelines conversion for PromptRewriter integration
  - Add fallback mechanisms for missing or ambiguous speaker notes
  - _Requirements: 6.1, 6.4, 6.5_

- [ ]* 2.2 Write property test for style analysis consistency
  - **Property 9: Style Analysis Consistency**
  - **Validates: Requirements 6.1**

- [x] 2.3 Add rewrite_tts_prompt method to PromptRewriter
  - Add new rewrite_tts_prompt method to existing PromptRewriter class
  - Implement TTS-specific rewrite request formatting
  - Add retry logic and fallback for TTS prompt generation
  - _Requirements: 6.2, 6.3_

- [ ]* 2.4 Write property test for default style fallback
  - **Property 10: Default Style Fallback**
  - **Validates: Requirements 6.4**

- [x] 3. Implement Gemini TTS Engine
  - Create Gemini TTS engine with natural language style prompts
  - Implement voice selection and model selection logic
  - Add audio synthesis with style control capabilities
  - _Requirements: 3.2, 3.4, 5.1_

- [x] 3.1 Create GeminiTTSEngine class
  - Implement Gemini TTS API integration with style prompts
  - Add voice mapping and selection for different languages
  - Create model selection logic (Flash vs Pro based on complexity)
  - _Requirements: 3.2, 3.4_

- [ ]* 3.2 Write property test for Gemini TTS usage
  - **Property 8: Gemini TTS Usage for Supported Languages**
  - **Validates: Requirements 3.2**

- [x] 3.3 Implement audio synthesis and processing
  - Add MP3 format generation and validation
  - Implement duration estimation and audio metadata extraction
  - Create error handling for TTS API failures
  - _Requirements: 5.1, 3.5_

- [ ]* 3.4 Write property test for MP3 format compliance
  - **Property 12: MP3 Format Compliance**
  - **Validates: Requirements 5.1**

- [x] 4. Implement Traditional TTS Engine for Cantonese
  - Create Traditional TTS engine for yue-HK and fallback scenarios
  - Implement SSML enhancement for traditional TTS
  - Add voice configuration for Cantonese languages
  - _Requirements: 3.1, 3.5_

- [x] 4.1 Create TraditionalTTSEngine class
  - Implement Google Cloud TTS integration for Cantonese
  - Add SSML enhancement based on style hints
  - Create voice configuration management for traditional TTS
  - _Requirements: 3.1_

- [ ]* 4.2 Write property test for engine fallback
  - **Property 7: Engine Selection for Cantonese**
  - **Validates: Requirements 3.1**

- [x] 4.3 Implement SSML enhancement system
  - Create SSML tag generation based on style context
  - Add pace and emphasis control through SSML
  - Implement error handling and graceful degradation
  - _Requirements: 3.5_

- [ ]* 5.1 Write property test for cache hit behavior
  - **Property 5: Cache Hit Behavior**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 5.2 Write property test for directory structure consistency
  - **Property 1: Directory Structure Consistency**
  - **Validates: Requirements 1.1**

- [ ]* 5.3 Write property test for cache invalidation
  - **Property 6: Cache Invalidation on Change**
  - **Validates: Requirements 2.3**

- [x] 5. Implement TTS Orchestrator for workflow coordination
  - Create main TTS orchestrator for slide processing coordination
  - Implement parallel processing for multiple languages and slides
  - Add integration with existing presentation processing pipeline
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5.1 Implement TTSOrchestrator class
  - Implement slide-level TTS processing with style adaptation
  - Add batch processing for multiple slides and languages
  - Create integration points with existing workflow components
  - _Requirements: 4.1, 4.2_

- [ ]* 5.2 Write property test for parallel processing independence
  - **Property 14: Parallel Processing Independence**
  - **Validates: Requirements 4.2**

- [x] 5.3 Implement error isolation and graceful degradation
  - Add error handling that doesn't block other slide processing
  - Implement graceful fallback when TTS engines fail
  - Create comprehensive logging and error reporting
  - _Requirements: 4.3, 7.1, 7.2_

- [ ]* 5.4 Write property test for error isolation
  - **Property 11: Error Isolation**
  - **Validates: Requirements 4.3**

- [x] 5.5 Add workflow integration and compatibility
  - Integrate with existing progress file formats
  - Ensure compatibility with current presentation processing
  - Add non-blocking integration with visual generation pipeline
  - _Requirements: 4.4, 4.5_

- [ ]* 5.6 Write property test for cache metadata consistency
  - **Property 15: Cache Metadata Consistency**
  - **Validates: Requirements 2.4, 2.5**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Integrate TTS system with existing presentation workflow
  - Modify existing presentation processor to include TTS generation
  - Add TTS configuration to existing config management
  - Update progress file format to include local file paths and metadata
  - _Requirements: 4.1, 4.4, 4.5_

- [x] 7.1 Update presentation processor integration
  - Add TTS orchestrator calls to existing slide processing workflow
  - Implement parallel execution with visual generation
  - Create configuration integration with existing settings
  - _Requirements: 4.1, 4.4_

- [x] 7.2 Update progress file format
  - Add optional audio_file_path and tts_metadata fields to progress JSON
  - Ensure backward compatibility with existing progress files
  - Update file reading/writing logic to handle new fields
  - _Requirements: 4.4, 4.5_

- [ ]* 7.3 Write property test for file naming convention
  - **Property 2: File Naming Convention Adherence**
  - **Validates: Requirements 1.2**

- [x] 7.4 Add comprehensive logging and monitoring
  - Implement detailed logging for TTS engine selection and processing
  - Add performance metrics and statistics reporting
  - Create thread-safe logging for concurrent operations
  - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [ ]* 7.5 Write property test for language directory separation
  - **Property 3: Language Directory Separation**
  - **Validates: Requirements 1.3**

- [x] 8. Create command-line interface and utilities
  - Add CLI commands for TTS generation and testing
  - Create utilities for cache management and cleanup
  - Implement batch processing tools for existing presentations
  - _Requirements: 5.5_

- [x] 8.1 Create TTS CLI commands
  - Add command for generating TTS for existing presentations
  - Implement cache cleanup and management commands
  - Create testing utilities for TTS engine validation
  - _Requirements: 5.5_

- [x] 8.2 Add batch processing utilities
  - Create tools for processing multiple presentations
  - Implement progress tracking and resume capabilities
  - Add validation tools for generated audio files
  - _Requirements: 5.5_

- [ ]* 8.3 Write property test for content hash normalization
  - **Property 4: Content Hash Normalization Consistency**
  - **Validates: Requirements 1.4**

- [x] 9. Final Checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Validate end-to-end TTS workflow with real presentation data
  - Verify integration with existing systems works correctly