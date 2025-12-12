# Changelog

## [Unreleased] - 2025-12-12

### Fixed
- **Language Enforcement Strengthening**: Fixed issue where styles with foreign language examples override target language
  - HK Comic style was generating Chinese notes even when English was requested
  - Strengthened language enforcement in fallback prompt rewriter with absolute priority rules
  - Added explicit instructions to translate style concepts rather than copy foreign examples
  - Ensures target language always takes precedence over style language examples
  - See `LANGUAGE_ENFORCEMENT_STRENGTHENING_FIX.md` for technical details

- **Prompt Rewriter Content Object Bug**: Fixed critical coding bug where styles weren't being applied
  - InMemoryRunner was receiving raw strings instead of proper Content objects, causing silent failures
  - Fixed all 4 rewrite methods to create proper `types.Content` objects with `types.Part.from_text()`
  - Added validation to detect empty responses and fall back to concatenation method
  - Ensures all style configurations (HK Comic, Cyberpunk, Gundam, etc.) are properly applied
  - Fixes issue where `--style-config hkcomic` was producing professional style instead of martial arts master style
  - See `PROMPT_REWRITER_EMPTY_RESPONSE_FIX.md` for technical details

- **Translation with Style Application**: Enhanced translator agent to apply speaker styles
  - Created styled translator agent using prompt rewriter system
  - Translator agent now applies configured speaker styles during translation (Cyberpunk, Gundam, etc.)
  - Maintains informational accuracy while adapting tone, vocabulary, and phrasing patterns
  - Ensures consistent style application across all languages
  - Integrates with existing agent factory and prompt rewriter architecture
  - See `TRANSLATION_STYLE_FIX.md` for technical details

## [Unreleased] - 2025-11-27

### Added
- **Video Prompt Generation**: New `--generate-videos` flag to generate video prompts for each slide
  - Extracts concise video prompts from speaker notes
  - Creates professional video prompt descriptions
  - Organizes prompts in `{filename}_{locale}_videos/` directory
  - Ready for integration with Veo 3.1 API or custom video generation
  - Works seamlessly with speaker notes and visuals generation
  - Multi-language support for video prompts

## [Unreleased] - 2025-11-25

### Added
- **Folder Processing Mode**: New `--folder` parameter to process all PPTX files in a directory
  - Automatically finds matching PDF files for each PPTX
  - Processes files sequentially with error handling
  - Skips files without matching PDFs
  - Continues processing remaining files if one fails
  
- **Multi-Language Support**: New `--language` parameter for speaker notes using locale codes
  - Default: en (English)
  - Supports locale codes: en, zh-CN (Simplified Chinese), yue-HK (Cantonese), zh-TW (Traditional Chinese), es (Spanish), fr (French), ja (Japanese), ko (Korean), etc.
  - Automatic language name mapping for clear AI instructions
  - Language instruction integrated into writer agent prompt
  
- **File-Specific Progress Tracking**: Each PPTX now has its own isolated progress file
  - Progress files named: `{filename}_progress.json` (English) or `{filename}_{locale}_progress.json`
  - Prevents conflicts when processing multiple files or languages
  - Enables parallel or sequential batch processing
  - Language-specific progress tracking allows same file in multiple languages
  
- **File-Specific Visual Organization**: Each PPTX now has its own visuals directory
  - Visuals directories named: `{filename}_visuals/` (English) or `{filename}_{locale}_visuals/`
  - Prevents image filename conflicts
  - Organized structure for managing multiple presentations and languages
  - Language-specific directories enable multi-language processing of same content

### Changed
- Updated `main.py`:
  - Added `process_folder()` function for batch processing
  - Added `--folder` and `--language` CLI arguments
  - Made `--pptx` optional when using `--folder`
  - Language parameter passed through entire processing pipeline
  
- Updated `config.py`:
  - Added `language` parameter to Config class
  - Changed `visuals_dir` property to return file-specific directory names
  
- Updated `progress_utils.py`:
  - Modified `get_progress_file_path()` to generate file-specific names
  
- Updated `tools/agent_tools.py`:
  - Modified `create_writer_tool()` to accept and use language parameter
  - Added language instruction to writer prompt when non-English
  
- Updated `services/presentation_processor.py`:
  - Pass language parameter to writer tool configuration
- Updated `run.ps1` and `run.sh`:
  - Added support for `--folder` parameter
  - Updated usage messages with folder and language examples
  - Validation for mutually exclusive `--pptx` and `--folder` options
  
- Updated `README.md`:
  - Added documentation for folder processing mode
  - Added documentation for multi-language support
  - Added examples for batch processing
  - Added file organization structure examples
  - Updated arguments section with new parameters

### Benefits
- **Scalability**: Process entire folders of presentations with one command
- **Organization**: Each presentation maintains its own progress and visuals
- **Internationalization**: Generate speaker notes in any language with proper file organization
- **Multi-Language Support**: Process the same presentation in multiple languages without conflicts
- **Isolation**: No shared state between different PPTX files or languages
- **Robustness**: Batch processing continues even if individual files fail
- **Clean Structure**: Language-specific suffixes keep outputs organized and identifiable
