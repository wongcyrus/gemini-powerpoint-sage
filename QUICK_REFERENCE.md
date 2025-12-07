# Quick Reference - Refactored Code

## Import Cheat Sheet

```python
# Configuration
from config.constants import (
    ModelConfig,           # AI model names
    ProcessingConfig,      # Retry, concurrency settings
    FilePatterns,          # File naming patterns
    LanguageConfig,        # Locale mappings
    SlideConfig,           # Slide dimensions
    EnvironmentVars,       # Environment variable names
)

# Error Handling
from utils.error_handling import (
    RetryStrategy,         # Retry with exponential backoff
    with_retry,            # Decorator for retry
    ProcessingError,       # Base exception
    SlideProcessingError,  # Slide-specific error
    TranslationError,      # Translation error
    VisualGenerationError, # Visual generation error
    VideoGenerationError,  # Video generation error
)

# Services
from services.agent_manager import AgentManager
from services.notes_generator import NotesGenerator
from services.translation_service import TranslationService
from services.video_service import VideoService
from services.visual_generator import VisualGenerator
```

## Common Patterns

### 1. Get a Configuration Value

```python
from config.constants import ModelConfig, ProcessingConfig

# Model names
supervisor_model = ModelConfig.SUPERVISOR
analyst_model = ModelConfig.ANALYST

# Processing settings
max_retries = ProcessingConfig.MAX_RETRIES
retry_delay = ProcessingConfig.RETRY_DELAY
```

### 2. Get a Language Name

```python
from config.constants import LanguageConfig

# Get display name
name = LanguageConfig.get_language_name("zh-CN")
# Returns: "Simplified Chinese (简体中文)"

# Check if supported
if locale in LanguageConfig.LOCALE_NAMES:
    print("Supported")
```

### 3. Generate a Filename

```python
from config.constants import FilePatterns

# Progress file
filename = FilePatterns.PROGRESS_FILE.format(
    base="lecture",
    lang="zh-CN"
)
# Returns: "lecture_zh-CN_progress.json"

# Visual file
visual = FilePatterns.REIMAGINED_SLIDE.format(idx=5)
# Returns: "slide_5_reimagined.png"
```

### 4. Add Retry Logic

```python
from utils.error_handling import with_retry, RetryStrategy

# Option 1: Decorator
@with_retry(max_retries=3, base_delay=2.0)
async def my_function():
    # Your code
    pass

# Option 2: Strategy
strategy = RetryStrategy(max_retries=3)
result = await strategy.execute(my_function, arg1, arg2)
```

### 5. Initialize Agents

```python
from services.agent_manager import AgentManager

manager = AgentManager()
manager.initialize_agents()

# Get specific agents
supervisor = manager.get_supervisor()
analyst = manager.get_analyst()
translator = manager.get_translator()
```

### 6. Generate Speaker Notes

```python
from services.notes_generator import NotesGenerator

generator = NotesGenerator(
    tool_factory=factory,
    supervisor_runner=runner,
    language="zh-CN",
    english_notes=en_notes
)

notes, status = await generator.generate_notes(
    slide_idx=1,
    slide_image=image,
    existing_notes="",
    previous_slide_summary="",
    presentation_theme="Security",
    global_context="..."
)
```

### 7. Translate Content

```python
from services.translation_service import TranslationService

service = TranslationService(
    translator_agent=translator,
    image_translator_agent=img_translator
)

# Translate text
translated = await service.translate_notes(
    english_notes="Hello world",
    target_language="zh-CN",
    slide_idx=1
)

# Translate visual
img_bytes = await service.translate_visual(
    english_visual=image,
    target_language="zh-CN",
    speaker_notes=notes,
    slide_idx=1
)
```

### 8. Generate Video

```python
from services.video_service import VideoService

service = VideoService(
    video_generator_agent=agent,
    videos_dir="/path/to/videos"
)

# Generate prompt
prompt = await service.generate_video_prompt(
    slide_idx=1,
    speaker_notes=notes,
    slide_image=image
)

# Generate video
artifact_id = await service.generate_video(
    slide_idx=1,
    speaker_notes=notes,
    slide_image=image
)

# Save prompt
path = await service.save_video_prompt(
    slide_idx=1,
    video_prompt=prompt,
    speaker_notes=notes,
    video_artifact=artifact_id
)
```

### 9. Handle Errors

```python
from utils.error_handling import ProcessingError, SlideProcessingError

try:
    result = await process_slide(slide_idx)
except SlideProcessingError as e:
    logger.error(f"Slide {e.slide_idx} failed: {e}")
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
```

### 10. Check Service Availability

```python
# Translation service
if translation_service.is_translation_available():
    translated = await translation_service.translate_notes(...)

# Video service
if video_service.is_available():
    video = await video_service.generate_video(...)
```

## File Locations

```
config/
├── constants.py          # All configuration constants
└── __init__.py

services/
├── agent_manager.py      # Agent initialization
├── notes_generator.py    # Notes generation
├── translation_service.py # Translation
├── video_service.py      # Video generation
└── visual_generator.py   # Visual generation

utils/
├── error_handling.py     # Retry & exceptions
├── agent_utils.py        # Agent execution
├── progress_utils.py     # Progress tracking
└── image_utils.py        # Image handling

docs/
├── REFACTORED_ARCHITECTURE.md  # Architecture diagrams
└── FOLDER_STRUCTURE.md         # File organization

REFACTORING.md            # Comprehensive guide
REFACTORING_SUMMARY.md    # Executive summary
DEVELOPER_GUIDE.md        # Developer handbook
REFACTORING_CHECKLIST.md  # Progress checklist
QUICK_REFERENCE.md        # This file
```

## Constants Reference

### ModelConfig
```python
SUPERVISOR = "gemini-2.5-flash"
ANALYST = "gemini-3-pro-preview"
WRITER = "gemini-2.5-flash"
AUDITOR = "gemini-2.5-flash"
OVERVIEWER = "gemini-3-pro-preview"
DESIGNER = "gemini-3-pro-image-preview"
TRANSLATOR = "gemini-2.5-flash"
IMAGE_TRANSLATOR = "gemini-3-pro-image-preview"
VIDEO_GENERATOR = "gemini-2.5-flash"
REFINER = "gemini-2.5-flash"
FALLBACK_IMAGEN = "imagen-4.0-generate-001"
```

### ProcessingConfig
```python
MAX_RETRIES = 3
RETRY_DELAY = 2.0
RETRY_BACKOFF_MULTIPLIER = 2.0
MAX_CONCURRENT_SLIDES = 3
PROGRESS_SAVE_INTERVAL = 1
PDF_DPI_STANDARD = 150
PDF_DPI_LOW = 75
```

### FilePatterns
```python
PROGRESS_FILE = "{base}_{lang}_progress.json"
NOTES_OUTPUT = "{base}_{lang}_with_notes{ext}"
VISUALS_OUTPUT = "{base}_{lang}_with_visuals{ext}"
VISUALS_DIR = "{base}_{lang}_visuals"
VIDEOS_DIR = "{base}_{lang}_videos"
VIDEO_PROMPT_FILE = "slide_{idx}_video_prompt.txt"
REIMAGINED_SLIDE = "slide_{idx}_reimagined.png"
```

### EnvironmentVars
```python
PROGRESS_FILE = "SPEAKER_NOTE_PROGRESS_FILE"
RETRY_ERRORS = "SPEAKER_NOTE_RETRY_ERRORS"
GOOGLE_CLOUD_LOCATION = "GOOGLE_CLOUD_LOCATION"
GOOGLE_CLOUD_PROJECT = "GOOGLE_CLOUD_PROJECT"
FORCE_FALLBACK_IMAGE_GEN = "FORCE_FALLBACK_IMAGE_GEN"
FALLBACK_IMAGEN_MODEL = "FALLBACK_IMAGEN_MODEL"
```

## Supported Languages

```python
"en"     → "English"
"zh-CN"  → "Simplified Chinese (简体中文)"
"zh-TW"  → "Traditional Chinese (繁體中文)"
"yue-HK" → "Cantonese (廣東話)"
"es"     → "Spanish (Español)"
"fr"     → "French (Français)"
"ja"     → "Japanese (日本語)"
"ko"     → "Korean (한국어)"
"de"     → "German (Deutsch)"
"it"     → "Italian (Italiano)"
"pt"     → "Portuguese (Português)"
"ru"     → "Russian (Русский)"
"ar"     → "Arabic (العربية)"
"hi"     → "Hindi (हिन्दी)"
"th"     → "Thai (ไทย)"
"vi"     → "Vietnamese (Tiếng Việt)"
```

## CLI Commands

```bash
# Single file, English
./run.sh --pptx lecture.pptx

# Multiple languages
./run.sh --pptx lecture.pptx --language "en,zh-CN,yue-HK"

# Batch processing
./run.sh --folder presentations --language "en,zh-CN"

# Skip visuals
./run.sh --pptx lecture.pptx --skip-visuals

# Generate videos
./run.sh --pptx lecture.pptx --generate-videos

# Retry errors
./run.sh --pptx lecture.pptx --retry-errors

# Refine for TTS
./run.sh --refine progress.json
```

## Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check agent initialization
manager = AgentManager()
manager.initialize_agents()
print(f"Initialized: {manager.is_initialized}")

# Test retry logic
from utils.error_handling import RetryStrategy

strategy = RetryStrategy(max_retries=2, base_delay=0.1)
result = await strategy.execute(test_function)

# Verify constants
from config.constants import ModelConfig
print(f"Supervisor: {ModelConfig.SUPERVISOR}")
```

## Common Issues

### Import Error
```python
# Problem: ModuleNotFoundError: No module named 'config'
# Solution: Run from project root
cd /path/to/gemini-powerpoint-sage
python3 main.py --pptx file.pptx
```

### Agent Not Found
```python
# Problem: Agent not found: my_agent
# Solution: Check AgentManager.initialize_agents()
manager = AgentManager()
manager.initialize_agents()
agent = manager.get_agent("supervisor")  # Use correct name
```

### Retry Not Working
```python
# Problem: Function not retrying
# Solution: Use await and catch right exceptions
@with_retry(exceptions=(ValueError, RuntimeError))
async def my_function():
    # Will only retry on ValueError or RuntimeError
    pass
```

## Performance Tips

1. **Use constants** - Faster than string lookups
2. **Reuse services** - Don't create new instances per slide
3. **Batch operations** - Process multiple slides when possible
4. **Cache results** - Store expensive computations
5. **Profile first** - Measure before optimizing

## Best Practices

1. ✅ Always use constants from `config/constants.py`
2. ✅ Use `@with_retry` for unreliable operations
3. ✅ Inject dependencies, don't create them
4. ✅ Log at appropriate levels (debug/info/warning/error)
5. ✅ Handle errors with custom exceptions
6. ✅ Write focused services (150-300 lines)
7. ✅ Add type hints to all functions
8. ✅ Document public APIs with docstrings
9. ✅ Test in isolation with mocks
10. ✅ Keep backward compatibility

## Resources

- **Architecture:** `docs/REFACTORED_ARCHITECTURE.md`
- **Developer Guide:** `DEVELOPER_GUIDE.md`
- **Refactoring Details:** `REFACTORING.md`
- **Progress:** `REFACTORING_CHECKLIST.md`
- **Main README:** `README.md`
