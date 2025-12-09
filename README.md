# Gemini PowerPoint Sage

Automatically generates or enhances speaker notes for PowerPoint presentations using a **Supervisor-led Multi-Agent System** powered by Google Gemini. Supports multi-language translation workflows with English as baseline.

Takes a PowerPoint (`.pptx`) and its corresponding PDF export (`.pdf`) as input. The PDF provides visual context for AI analysis, while the PPTX is updated with generated speaker notes in one or multiple languages.

## Architecture

The system employs a sophisticated multi-agent approach, orchestrated in a two-pass system:

### Agents

1. **Overviewer Agent** (`gemini-exp-1206`, Pass 1): Analyzes all PDF slide images to generate a comprehensive Global Context Guide capturing overall narrative, key themes, vocabulary, and desired speaker persona
2. **Supervisor Agent** (`gemini-2.0-flash-exp`, Pass 2 Orchestrator): Directs the workflow for each slide, consulting the Auditor, triggering the Analyst, and requesting the Writer to generate notes
3. **Auditor Agent** (`gemini-2.0-flash-exp`): Evaluates quality and usefulness of existing speaker notes
4. **Analyst Agent** (`gemini-exp-1206`): Analyzes visual and textual content of slide images to extract key topics, information, and intent
5. **Writer Agent** (`gemini-2.0-flash-exp`): Crafts coherent, first-person speaker notes using Analyst insights, Global Context, and Previous Slide Summary
6. **Designer Agent** (`gemini-2.0-flash-exp`): Generates high-fidelity slide images with consistent styling, converting notes to concise on-slide text
7. **Translator Agent** (`gemini-2.0-flash-exp`): Translates speaker notes while maintaining technical accuracy and cultural appropriateness
8. **Image Translator Agent** (`gemini-exp-1206`): Analyzes English visuals and provides translations with culturally adapted descriptions

### Additional Documentation

See the extended design rationale, sequence flows, and agent interface contracts in: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Key Features

- 🌍 **Multi-Language Support**: Process presentations in multiple languages (en, zh-CN, yue-HK, es, fr, ja, ko, etc.)
- 📁 **Batch Processing**: Process entire folders of PPTX files
- 🎨 **AI Visual Generation**: Create professional slide designs with consistent styling
- 🎬 **Video Prompt Generation**: Generate video prompts ready for Veo 3.1
- 💾 **Organized Output**: Language-specific file naming with self-contained folders
- ⚡ **Translation Mode**: Faster processing by translating from English baseline
- 📊 **Progress Tracking**: Resume interrupted processing automatically
- 🎭 **Custom Styles**: Apply themed styles (Gundam, Cyberpunk, Star Wars, etc.)

## Quick Start

```bash
# Linux/macOS - Using config file (recommended)
./run.sh --config styles/config.gundam.yaml

# Single file, English only
./run.sh --pptx lecture.pptx

# Multiple languages
./run.sh --pptx lecture.pptx --language "en,zh-CN,yue-HK"

# Batch process folder
./run.sh --folder presentations --language "en,zh-CN"
```

```powershell
# Windows
.\run.ps1 --config "styles\config.gundam.yaml"
.\run.ps1 --pptx "lecture.pptx"
```

## Setup

### Quick Setup (Recommended)

```bash
# Linux/macOS
./setup.sh

# Windows
.\setup.ps1
```

The setup script will:
- Create a Python virtual environment at `.venv`
- Install all required dependencies
- Configure the environment

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure Google Cloud credentials
gcloud auth application-default login
```

## Usage

### With Config File (Recommended)

```bash
# Use pre-configured styles
./run.sh --config styles/config.gundam.yaml
./run.sh --config styles/config.cyberpunk.yaml
./run.sh --config styles/config.starwars.yaml

# Or create your own
cp styles/config.professional.yaml my-config.yaml
# Edit my-config.yaml
./run.sh --config my-config.yaml
```

### Command Line

```bash
# Basic usage - PDF auto-detected
./run.sh --pptx presentation.pptx

# With explicit PDF
./run.sh --pptx presentation.pptx --pdf presentation.pdf

# With custom style
./run.sh --pptx presentation.pptx --style "Gundam"

# Multiple languages
./run.sh --pptx file.pptx --language "en,zh-CN,yue-HK"

# Folder mode
./run.sh --folder presentations --language "en,zh-CN"

# Skip visual generation (faster, notes only)
./run.sh --pptx file.pptx --skip-visuals

# Generate video prompts
./run.sh --pptx file.pptx --generate-videos

# Retry failed slides
./run.sh --pptx file.pptx --retry-errors

# Custom output directory
./run.sh --pptx file.pptx --output-dir output/custom
```

### Process All Styles at Once

Generate multiple style variants automatically:

```bash
python run_all_styles.py

# With specific language
python run_all_styles.py zh-CN

# With multiple languages
python run_all_styles.py "en,yue-HK,zh-CN"
```

Output structure:
```
output/
├── cyberpunk/generate/presentation_en_notes.pptm
├── gundam/generate/presentation_en_notes.pptm
├── starwars/generate/presentation_en_notes.pptm
└── professional/generate/presentation_en_notes.pptm
```

See [docs/RUN_ALL_STYLES.md](docs/RUN_ALL_STYLES.md) for details.

## Command-Line Arguments

**Required (one of):**
- `--pptx <path>` - Path to input PowerPoint file
- `--folder <path>` - Path to folder with multiple PPTX files

**Optional:**
- `--config <path>` - Path to YAML configuration file (recommended)
- `--pdf <path>` - Path to PDF export (auto-detected if not specified)
- `--language <locale(s)>` - Language codes, comma-separated (default: `en`)
  - Examples: `en`, `zh-CN`, `"en,zh-CN,yue-HK"`
  - English always processed first as translation baseline
  - Supported: en, zh-CN, zh-TW, yue-HK, es, fr, ja, ko, de, it, pt, ru, ar, hi, th, vi
- `--style <name>` - Style/theme for content generation (e.g., "Gundam", "Cyberpunk")
- `--output-dir <path>` - Output directory for processed files
- `--course-id <id>` - Firestore Course ID for thematic context
- `--progress-file <path>` - Custom progress file location
- `--retry-errors` - Retry previously failed slides
- `--skip-visuals` - Skip AI visual generation (notes only, faster)
- `--generate-videos` - Generate video prompts for all slides
- `--region <region>` - GCP region (default: global)
- `--refine <path>` - Refine existing progress JSON for TTS (removes markdown)

## 🎭 Custom Styles

Apply themed styles using pre-configured YAML files in `styles/`:

```bash
# Star Wars - Epic space opera with Jedi Master narration
./run.sh --config styles/config.starwars.yaml

# Gundam - Mecha anime with dramatic Char Aznable-style speeches
./run.sh --config styles/config.gundam.yaml

# Cyberpunk - Neon-soaked dystopian aesthetic
./run.sh --config styles/config.cyberpunk.yaml

# Hong Kong Comic - Vibrant comic book style
./run.sh --config styles/config.hkcomic.yaml

# Professional - Clean and corporate
./run.sh --config styles/config.professional.yaml
```

**Available Styles:**
- 🌌 **Star Wars** - Jedi briefings with epic space opera visuals
- 🤖 **Gundam** - Mecha anime aesthetic with philosophical antagonist voice
- 🌃 **Cyberpunk** - Neon colors with edgy tech-savvy narration
- 🎨 **HK Comic** - Vibrant Hong Kong comic book style
- 📋 **Professional** - Clean and corporate default style

See [docs/STYLE_CONFIGS.md](docs/STYLE_CONFIGS.md) for details and how to create your own.

## Multi-Language Translation Workflow

### How It Works

1. **English Baseline** - Always processed first from slide analysis
2. **Speaker Note Translation** - Other languages translate from English notes using Translator agent (faster)
3. **Visual Translation** - Image Translator analyzes English visuals, Designer regenerates with translated text
4. **Organized Output** - All files include language suffix: `filename_{locale}_*`

### Example

```bash
./run.sh --pptx lecture.pptx --language "en,zh-CN,yue-HK"
```

**Output:**
```
lecture_en_with_notes.pptx       # English (generated)
lecture_en_with_visuals.pptx
lecture_en_progress.json
lecture_en_visuals/              # Generated visuals

lecture_zh-CN_with_notes.pptx    # Simplified Chinese (translated)
lecture_zh-CN_with_visuals.pptx
lecture_zh-CN_progress.json
lecture_zh-CN_visuals/           # Translated visuals

lecture_yue-HK_with_notes.pptx   # Cantonese (translated)
lecture_yue-HK_with_visuals.pptx
lecture_yue-HK_progress.json
lecture_yue-HK_visuals/
```

### Benefits

- ⚡ **Faster**: Translation 2-3x faster than full generation
- 💰 **Cost-effective**: Fewer API calls (2 vs 4-5 calls per slide)
- 🌍 **Localized**: Text in visuals translated to target language
- 📐 **Design Consistency**: Layout and style maintained across languages
- 🎯 **Consistent**: All versions based on same English baseline
- ✅ **Quality**: English serves as reviewed baseline

## Output Files

The tool generates self-contained output folders with all files per language/style:

**Generated files per language:**
1. `{filename}_{locale}_with_notes.pptx` - Original slides with speaker notes
2. `{filename}_{locale}_with_visuals.pptx` - Slides with notes and AI-generated visuals
3. `{filename}_{locale}_progress.json` - Progress tracking for incremental processing
4. `{filename}_{locale}_visuals/` - Directory containing AI-generated slide images (PNG)

**Example structure (single file):**
```
presentations/
├── lecture.pptx (original)
├── lecture.pdf (original)
├── lecture_en_with_notes.pptx
├── lecture_en_with_visuals.pptx
├── lecture_en_progress.json
├── lecture_en_visuals/
│   ├── slide_1_reimagined.png
│   └── slide_2_reimagined.png
├── lecture_zh-CN_with_notes.pptx
├── lecture_zh-CN_with_visuals.pptx
├── lecture_zh-CN_progress.json
└── lecture_zh-CN_visuals/
    ├── slide_1_reimagined.png
    └── slide_2_reimagined.png
```

**Example structure (with styles):**
```
output/
├── cyberpunk/generate/
│   ├── lecture_en_notes.pptm
│   ├── lecture_en_visuals.pptm
│   ├── lecture_en_progress.json
│   └── lecture_en_visuals/
├── gundam/generate/
│   ├── lecture_en_notes.pptm
│   ├── lecture_en_visuals.pptm
│   ├── lecture_en_progress.json
│   └── lecture_en_visuals/
└── starwars/generate/
    ├── lecture_en_notes.pptm
    ├── lecture_en_visuals.pptm
    ├── lecture_en_progress.json
    └── lecture_en_visuals/
```

**Note:** Each output folder is self-contained - you can move, share, or archive any folder independently.

## Progress Tracking & Resume

The tool automatically tracks processing progress for each language:

- **Incremental processing**: Resume interrupted work without reprocessing completed slides
- **Error retry**: Failed slides automatically retried on subsequent runs
- **Force retry**: Use `--retry-errors` to regenerate all slides including successful ones
- **Language isolation**: Each language has independent progress tracking

Progress files track:
- Slide index and original notes hash
- Generated speaker notes
- Processing status (success/error)
- Global context for consistency

## Batch Processing

Process multiple PPTX files at once:

```bash
./run.sh --folder presentations --language "en,zh-CN"
```

**Features:**
- Auto-discovers all `.pptx` files in folder
- Auto-detects matching PDF files (same basename)
- Skips files without PDFs
- Independent progress tracking per file and language
- Continues on individual file failures
- Processes all languages for each file before moving to next

See [docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md) for more details.

## Refining Speaker Notes (TTS Optimization)

Refine existing generated speaker notes for Text-to-Speech systems:

```bash
# Single file
./run.sh --refine path/to/progress.json

# Batch process folder
./run.sh --refine path/to/folder/
```

This process:
- Removes markdown formatting (bold, italics, headers)
- Simplifies complex sentence structures
- Converts bullet points into natural conversational flow
- Removes visual references (e.g., "As you can see in this chart")

Output: Creates `_refined.json` suffix files (e.g., `progress_refined.json`)

## Technical Implementation Details

### Supervisor "Silent Finish" Fallback

Implements a **Last Tool Output Fallback** pattern to handle cases where the Supervisor agent calls a tool but terminates without returning the output:

1. The `speech_writer` tool captures generated text into `last_writer_output`
2. If Supervisor produces empty final text, system checks `last_writer_output`
3. If data exists, uses captured text as final speaker note

This ensures robustness against model unpredictability.

### Image Generation Skip Logic

- **Stable Caching**: Generated images named `slide_{index}_reimagined.png`
- **Skip Check**: Checks if image exists before calling Image Generation API
- **Forced Retry**: `--retry-errors` flag bypasses cache to force regeneration
- **Language-Specific**: Each language has its own visuals directory

### Translation Mode

- **English First**: Always generates English from scratch as baseline
- **Translation**: Non-English languages translate from English notes
- **Consistency**: Ensures all language versions convey same content
- **Performance**: Translation 2-3x faster than full generation

## Context Handling

- **Rolling Context**: Supervisor Agent maintains awareness of previous slide's generated note for smooth transitions
- **Presentation Theme**: Overall theme derived from generic default or `--course-id` (if provided)
- **Global Context**: Overviewer Agent analyzes all slides first to create comprehensive context guide ensuring consistency

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

### Quick Start
- [Quick Start Guide](docs/QUICK_START.md) - Get started in 3 easy steps
- [Configuration File Guide](docs/CONFIG_FILE_GUIDE.md) - Use YAML config files
- [Style Examples](docs/STYLE_EXAMPLES.md) - Apply custom themes

### Reference
- [Folder Structure](docs/FOLDER_STRUCTURE.md) - Understand output organization
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command-line reference
- [Run All Styles](docs/RUN_ALL_STYLES.md) - Batch style processing

### Architecture
- [Architecture](docs/ARCHITECTURE.md) - System architecture overview
- [Refactored Architecture](docs/REFACTORED_ARCHITECTURE.md) - Improved design

**Full documentation index:** [docs/README.md](docs/README.md)

## Environment Variables (Optional)

```bash
# Linux/macOS - Use alternate GCP project
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='us-central1'
./run.sh --pptx file.pptx
```

```powershell
# Windows - Use alternate GCP project
$env:GOOGLE_CLOUD_PROJECT = 'your-project-id'
$env:GOOGLE_CLOUD_LOCATION = 'us-central1'
.\run.ps1 --pptx "file.pptx"
```

## License

See [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and feature updates.
