# Gemini PowerPoint Sage

🤖 **AI-powered presentation enhancement system using 10 specialized Gemini agents** to generate speaker notes, enhance visuals, and apply custom styles. Supports 16+ languages with batch processing and themed styling (Cyberpunk, Gundam, Star Wars, etc.).

Transforms static PowerPoint presentations into engaging experiences with AI-generated speaker scripts, enhanced visuals, and professional styling. Uses a sophisticated **Supervisor-led Multi-Agent Architecture** with Google Gemini models for intelligent content generation and style integration.

## 📚 Documentation

- **[Quick Start](docs/QUICK_START.md)** - Get running in 3 steps
- **[User Guide](QUICK_REFERENCE.md)** - Commands, styles, and workflows  
- **[All Documentation](docs/README.md)** - Complete documentation index

## 🏗️ Architecture

The system uses a sophisticated **10-Agent Multi-Agent Architecture** with three processing phases:

### 🤖 The Agent Ecosystem

1. **Overviewer Agent** (`gemini-3-pro-preview`): Analyzes entire presentation for global context and narrative consistency
2. **Supervisor Agent** (`gemini-2.5-flash`): Orchestrates 5-step workflow for each slide, coordinating other agents
3. **Auditor Agent** (`gemini-2.5-flash`): Quality control - evaluates existing content and determines if regeneration is needed
4. **Analyst Agent** (`gemini-3-pro-preview`): Visual content analysis - extracts insights from slide images
5. **Writer Agent** (`gemini-2.5-flash`): Generates natural, engaging speaker scripts with style integration
6. **Designer Agent** (`gemini-3-pro-image-preview`): Creates enhanced slide visuals with consistent styling
7. **Translator Agent** (`gemini-2.5-flash`): Style-aware translation maintaining persona and technical accuracy
8. **Image Translator Agent** (`gemini-3-pro-image-preview`): Analyzes and translates visual content for different languages
9. **Video Generator Agent** (`gemini-2.5-flash`): Creates video prompts ready for Veo 3.1 integration
10. **Prompt Rewriter Agent** (`gemini-2.5-flash`): Meta-agent that integrates styles into other agents' prompts at creation time

### 📋 Three-Phase Processing

**Phase 1: Speaker Notes Generation**
- Global context analysis by Overviewer
- Per-slide supervisor workflow (Audit → Analyze → Write)
- Translation mode for non-English languages

**Phase 2: Visual Enhancement** 
- AI-generated slide designs with style consistency
- Visual translation for multilingual presentations
- Layout optimization and professional styling

**Phase 3: Video Content** (Optional)
- Video prompt generation for promotional content
- MCP integration with Veo 3.1
- Slide-appropriate timing and concepts



## ✨ Key Features

- 🤖 **10 Specialized AI Agents** working in harmony for comprehensive presentation enhancement
- 🌍 **16+ Languages** with cultural adaptation (en, zh-CN, zh-TW, yue-HK, es, fr, ja, ko, de, it, pt, ru, ar, hi, th, vi)
- 🎨 **Custom Themed Styles** (Cyberpunk, Gundam, Star Wars, Professional, HK Comic) affecting both visuals and speaker persona
- 📁 **Batch Processing** for entire presentation libraries with YAML-driven configuration
- ⚡ **Translation Mode** 2-3x faster than full generation by translating from English baseline
- 🎬 **Video Integration** ready for Veo 3.1 with professional video concepts
- 📊 **Progress Tracking** with resume capability and error retry
- 🛠️ **Production Ready** with robust error handling and fallback mechanisms
- 🎯 **Style Integration** via Prompt Rewriter agent that deeply integrates themes into all agents
- 💾 **Self-Contained Output** with organized language-specific folders

## 🚀 Quick Start

Choose from three processing modes based on your needs:

```bash
# 🌟 All Styles Processing (Production - Process all files with all style configurations)
python main.py --styles
python main.py  # defaults to --styles

# 🎨 Single Style Processing (Focused - Process all files with one specific style)
python main.py --style-config cyberpunk
python main.py --style-config professional
python main.py --style-config gundam

# 📄 Single File Processing (Testing - Process one file with CLI parameters)
python main.py --pptx lecture.pptx --language en --style professional
python main.py --pptx presentation.pptx --language "en,zh-CN,yue-HK" --style cyberpunk
```

```powershell
# Windows PowerShell
python main.py --styles
python main.py --style-config starwars
python main.py --pptx "lecture.pptx" --language "en,zh-CN" --style gundam
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

### Three Processing Modes

#### 🌟 All Styles Processing (Production)
Process all files with all available style configurations:

```bash
# Process all styles with their YAML configurations
python main.py --styles
python main.py  # defaults to --styles

# All configuration comes from styles/config.*.yaml files:
# - input_folder: where to find PPTX/PDF pairs
# - output_dir: where to save results
# - language: languages to process
# - style: visual and speaker style definitions
```

#### 🎨 Single Style Processing (Focused)
Process all files with one specific style configuration:

```bash
# Process with cyberpunk style only
python main.py --style-config cyberpunk

# Process with professional style only
python main.py --style-config professional

# Use full path to config file
python main.py --style-config /path/to/custom-config.yaml
```

#### 📄 Single File Processing (Quick Testing)
Process one specific file with CLI parameters:

```bash
# Basic usage - PDF auto-detected
python main.py --pptx presentation.pptx --language en --style Professional

# With explicit PDF
python main.py --pptx presentation.pptx --pdf presentation.pdf --language en --style Gundam

# Multiple languages
python main.py --pptx file.pptx --language "en,zh-CN,yue-HK" --style Cyberpunk

# Custom output directory
python main.py --pptx file.pptx --language en --style Professional --output-dir output/custom
```

### Additional Options (All Modes)

```bash
# Skip visual generation (faster, notes only)
python main.py --styles --skip-visuals

# Generate video prompts
python main.py --style-config cyberpunk --generate-videos

# Retry failed slides
python main.py --styles --retry-errors

# Custom course context
python main.py --style-config professional --course-id course123
```

### YAML Configuration Structure

All organized processing uses YAML configuration files in the `styles/` directory:

```yaml
# styles/config.cyberpunk.yaml
input_folder: "notes"                    # Where to find PPTX/PDF pairs
output_dir: "notes/cyberpunk/generate"   # Where to save results
language: "en,zh-CN,yue-HK"             # Languages to process
style:
  visual_style: "Cyberpunk aesthetic with neon colors..."
  speaker_style: "Night City edgerunner persona..."
skip_visuals: false
generate_videos: false
```

**Available Style Configurations:**
- `styles/config.cyberpunk.yaml` - 🌃 Neon-soaked Night City edgerunner aesthetic with anti-corpo attitude
- `styles/config.professional.yaml` - 📋 Clean, corporate design with authoritative tone
- `styles/config.gundam.yaml` - 🤖 Mecha anime aesthetic with philosophical antagonist voice
- `styles/config.starwars.yaml` - 🌌 Epic space opera with Jedi Master narration
- `styles/config.hkcomic.yaml` - 🎨 Vibrant Hong Kong comic book style with dynamic energy

## Command-Line Arguments

### Processing Modes (choose one)

**YAML-Driven Processing:**
- `--styles` - Process all files with all available YAML configurations (default)
- `--style-config <name>` - Process all files with one specific YAML configuration
  - Examples: `cyberpunk`, `professional`, `gundam`
  - Can also use full path to config file

**Single File Processing:**
- `--pptx <path>` - Path to input PowerPoint file (requires CLI parameters)

### Single File Parameters (only with --pptx)
- `--pdf <path>` - Path to PDF export (auto-detected if not specified)
- `--language <locale(s)>` - Language codes, comma-separated (default: `en`)
  - Examples: `en`, `zh-CN`, `"en,zh-CN,yue-HK"`
  - English always processed first as translation baseline
  - **Supported Languages**: en, zh-CN, zh-TW, yue-HK, es, fr, ja, ko, de, it, pt, ru, ar, hi, th, vi
- `--style <name>` - Style/theme for content generation
  - **Available**: `professional`, `cyberpunk`, `gundam`, `starwars`, `hkcomic`
- `--output-dir <path>` - Output directory for processed files

### Global Options (all modes)
- `--course-id <id>` - Firestore Course ID for thematic context
- `--progress-file <path>` - Custom progress file location
- `--retry-errors` - Retry previously failed slides
- `--skip-visuals` - Skip AI visual generation (notes only, faster)
- `--generate-videos` - Generate video prompts for all slides
- `--region <region>` - GCP region (default: global)
- `--refine <path>` - Refine existing progress JSON for TTS (removes markdown)

## 🎭 Custom Themed Styles

Transform your presentations with AI-powered themed styles that affect both visuals and speaker persona:

```bash
# Process all styles at once (recommended for production)
python main.py --styles

# Process one specific style configuration
python main.py --style-config starwars
python main.py --style-config gundam
python main.py --style-config cyberpunk
python main.py --style-config hkcomic
python main.py --style-config professional

# Single file with specific style
python main.py --pptx file.pptx --language en --style starwars
python main.py --pptx presentation.pptx --language "en,zh-CN" --style cyberpunk
```

### 🎨 Available Themed Styles

- 🌌 **Star Wars** - Epic space opera with Jedi Master narration and galactic visuals
- 🤖 **Gundam** - Mecha anime aesthetic with philosophical antagonist voice and dramatic speeches  
- 🌃 **Cyberpunk** - Night City edgerunner persona with neon-soaked dystopian visuals and anti-corpo attitude
- 🎨 **HK Comic** - Vibrant Hong Kong comic book style with dynamic energy and bold colors
- 📋 **Professional** - Clean, corporate design with authoritative tone and business-focused approach

### 🔧 Style Integration System

Each style deeply integrates into the AI agents through the **Prompt Rewriter Agent**:

- **Visual Style**: Affects Designer agent for consistent slide aesthetics, color palettes, typography, and layout
- **Speaker Style**: Affects Writer and Translator agents for persona, vocabulary, tone, and cultural references
- **Deep Integration**: Styles are woven throughout prompts, not just appended, for natural and cohesive results

**Style Configuration Structure:**
```yaml
# styles/config.{style}.yaml
input_folder: "notes"                    # Source PPTX/PDF location
output_dir: "notes/{style}/generate"     # Organized output by style
language: "en,zh-CN,yue-HK"             # Languages to process
style:
  visual_style: |                       # Detailed visual aesthetic guide
    Color palettes, typography, layout principles...
  speaker_style: |                      # Detailed speaker persona guide
    Tone, vocabulary, cultural references, roleplay instructions...
```

See the `styles/` directory for complete configuration examples and create your own custom styles.

## Multi-Language Translation Workflow

### How It Works

1. **English Baseline** - Always processed first from slide analysis with configured speaker style
2. **Style-Aware Translation** - Other languages translate AND restyle from English notes, applying the target language's speaker style configuration
3. **Visual Translation** - Image Translator analyzes English visuals, Designer regenerates with translated text
4. **Organized Output** - All files include language suffix: `filename_{locale}_*`

### Example

```bash
# Single file processing
python main.py --pptx lecture.pptx --language "en,zh-CN,yue-HK" --style Professional

# Or use YAML configuration for organized processing
python main.py --style-config professional  # Uses styles/config.professional.yaml
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
- 🎭 **Style-Aware**: Each language applies its configured speaker style during translation
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

**Example structure (YAML-driven processing):**
```
# Single style processing: python main.py --style-config cyberpunk
notes/cyberpunk/generate/
├── lecture_en_notes.pptm
├── lecture_en_visuals.pptm
├── lecture_en_progress.json
└── lecture_en_visuals/

# All styles processing: python main.py --styles
notes/
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
└── professional/generate/
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

The system automatically processes multiple PPTX files using YAML configurations:

```bash
# Process all files with all styles
python main.py --styles

# Process all files with one specific style
python main.py --style-config cyberpunk
```

**How it works:**
- YAML configs specify `input_folder` (e.g., "notes") containing PPTX/PDF pairs
- Auto-discovers all `.pptx` files in the specified folder
- Auto-detects matching PDF files (same basename)
- Skips files without PDFs with warning
- Independent progress tracking per file and language
- Continues on individual file failures
- Processes all languages for each file before moving to next

**Directory Structure:**
```
notes/                          # input_folder from YAML
├── module1.pptx
├── module1.pdf
├── module2.pptx
├── module2.pdf
└── module3.pptx
└── module3.pdf

notes/cyberpunk/generate/       # output_dir from YAML
├── module1_en_notes.pptm
├── module1_zh-CN_notes.pptm
├── module2_en_notes.pptm
└── module2_zh-CN_notes.pptm
```

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

## 🔧 Technical Implementation

### Multi-Agent Workflow

**Supervisor 5-Step Process** (per slide):
1. **Audit** - Quality check of existing notes
2. **Decision** - Determine if regeneration needed  
3. **Analyze** - Visual content extraction from slide
4. **Generate** - Create speaker notes with style integration
5. **Return** - Final polished speaker script

**Translation Mode Optimization**:
- English processed first as baseline
- Non-English languages use style-aware translation (2-3x faster)
- Maintains consistency across all language versions

### Robust Error Handling

- **Supervisor Fallback**: "Last Tool Output" pattern captures writer output if supervisor terminates unexpectedly
- **Retry Strategy**: Exponential backoff with 3 attempts for all agent calls
- **Progress Tracking**: Resume interrupted processing automatically
- **Image Caching**: Skip existing visuals unless `--retry-errors` specified

### Style Integration Architecture

**Prompt Rewriter Agent** operates at agent creation time:
1. Takes base agent prompts + style guidelines
2. Uses LLM to deeply integrate style throughout prompts
3. Creates style-aware agents before content processing begins
4. Fallback to simple concatenation if LLM rewriting fails

### Context Management

- **Global Context**: Overviewer analyzes entire presentation for narrative consistency
- **Rolling Context**: Previous slide summary informs next slide generation
- **Language Isolation**: Independent progress tracking per language
- **Session Management**: Reused supervisor sessions for efficiency



## 🛠️ Technology Stack

- **AI Models**: Google Gemini (2.5-flash, 3-pro-preview, 3-pro-image-preview)
- **Language**: Python 3.10+
- **Frameworks**: Google ADK (Agent Development Kit), FastMCP
- **Document Processing**: python-pptx, PyMuPDF, Pillow
- **Configuration**: YAML-driven with environment variable support

## 🌐 Environment Variables (Optional)

```bash
# Linux/macOS - Use alternate GCP project
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='us-central1'
python main.py --pptx file.pptx
```

```powershell
# Windows - Use alternate GCP project
$env:GOOGLE_CLOUD_PROJECT = 'your-project-id'
$env:GOOGLE_CLOUD_LOCATION = 'us-central1'
python main.py --pptx "file.pptx"
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 3 steps
- **[User Guide](QUICK_REFERENCE.md)** - Commands, styles, and workflows  
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and agent relationships
- **[Agent Flow Details](docs/AGENT_FLOW_DETAILED.md)** - Complete workflow trace
- **[All Documentation](docs/README.md)** - Complete documentation index

## 🤝 Contributing

We welcome contributions! The multi-agent architecture makes it easy to:
- Add new AI agents for specialized tasks
- Create custom presentation styles  
- Extend language support
- Improve processing capabilities

## 📄 License

See [LICENSE](LICENSE) file for details.

## 📈 Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and feature updates.

---

**Transform your presentations from static slides to engaging experiences with AI-powered enhancement.**
