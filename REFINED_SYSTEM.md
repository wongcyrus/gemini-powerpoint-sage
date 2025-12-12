# Refined Gemini PowerPoint Sage System

## Overview

The system has been refactored to provide a cleaner, more unified approach to processing presentations with support for organized directory structures and reduced complexity in running methods.

## Key Improvements

### 1. Unified Processing Architecture

- **Single Processor**: Replaced multiple command classes (`ProcessCommand`, `BatchCommand`) with `UnifiedProcessor`
- **Consolidated Logic**: All processing modes now use the same underlying logic
- **Reduced Complexity**: Fewer running methods and cleaner code paths

### 2. YAML-Driven Configuration

- **Primary Configuration**: `input_folder`, `output_dir`, `language`, and `style` are now defined in YAML files
- **CLI Overrides**: Command-line options work as overrides for flexibility
- **Complex Styles**: Detailed visual and speaker style definitions possible in YAML
- **Team Collaboration**: Version-controlled, shareable configurations

### 3. 2-Level Input Scanning

The new `InputScanner` provides intelligent discovery of presentation files across different organizational structures:

#### Supported Directory Structures

```
project/
├── styles/                     # Style-organized presentations
│   ├── config.cyberpunk.yaml   # Style configurations
│   ├── config.gundam.yaml
│   └── cyberpunk/
│       ├── input/              # Input files
│       │   ├── presentation.pptx
│       │   └── presentation.pdf
│       └── generate/           # Output directory
├── notes/                      # Course/topic-organized presentations
│   ├── professional/           # Category subdirectory
│   │   ├── module1.pptx
│   │   ├── module1.pdf
│   │   ├── module2.pptx
│   │   └── module2.pdf
│   ├── course.pptx            # Direct files
│   └── course.pdf
└── presentation.pptx          # Root level files
└── presentation.pdf
```

### 3. Simplified CLI Interface

#### New Command Structure

```bash
# YAML-driven processing (recommended)
python main.py --styles                    # Uses styles/config.*.yaml files
python main.py --notes                     # Process notes directory
python main.py --all-sources               # Process everything
python main.py                             # Auto-detect mode

# Single file processing
python main.py --pptx presentation.pptx --pdf presentation.pdf

# CLI overrides (for testing/flexibility)
python main.py --styles --language "en"    # Override YAML language setting
python main.py --styles --output-dir "test/output"  # Override YAML output
```

#### Removed Complexity

- Eliminated `--folder` and `--input-folder` distinction
- Simplified to single `--directory` option
- Removed complex batch processing logic
- Unified language and style handling

### 4. Smart Configuration Loading

#### Style-Specific Configurations

When processing the styles directory, the system automatically:

1. Detects style subdirectories
2. Loads corresponding `config.{style}.yaml` files
3. Applies style-specific settings
4. Processes files with appropriate configurations

#### Output Directory Management

- **Styles**: Automatically uses `styles/{style}/generate/` for output
- **Notes**: Uses same directory as input files
- **Root**: Uses same directory as input files
- **Override**: `--output-dir` parameter overrides all defaults

## Usage Examples

### Basic Usage

```python
from application.unified_processor import UnifiedProcessor

# Create processor
processor = UnifiedProcessor(
    languages="en,zh-CN",
    style="Cyberpunk",
    generate_videos=True
)

# Process all sources
results = await processor.process_all_sources()
```

### Input Scanning

```python
from application.input_scanner import InputScanner

# Scan for available files
scanner = InputScanner(".")
all_sources = scanner.scan_all()

# Results organized by source type
for source_type, file_sets in all_sources.items():
    print(f"{source_type}: {len(file_sets)} files")
```

### Style-Specific Processing

```python
# Process styles directory with automatic config loading
results = await processor.process_styles_directory()

# Results organized by style
for style_name, style_results in results.items():
    print(f"Style {style_name}: {len(style_results)} files processed")
```

## Configuration Files

### Style Configuration Example

```yaml
# styles/config.cyberpunk.yaml
style: "Cyberpunk"
language: "en,zh-CN"
generate_videos: true
skip_visuals: false
output_dir: "cyberpunk/generate"

# Style-specific settings
visual_style: "Neon-lit cyberpunk aesthetic with dark themes"
speaker_style: "Tech-savvy, futuristic tone with cyberpunk terminology"
```

### Main Configuration Example

```yaml
# config.yaml
# Auto-detect all sources
all_sources: true

# Or specify specific mode
# styles: true
# notes: true
# directory: "path/to/presentations"

# Global settings
language: "en,zh-CN"
style: "Professional"
generate_videos: false
skip_visuals: false
region: "global"
```

## Migration Guide

### From Old System

1. **Replace command usage**:
   ```bash
   # Old
   python main.py --folder presentations/ --language en,zh-CN
   
   # New
   python main.py --directory presentations/ --language en,zh-CN
   ```

2. **Update configuration files**:
   - Move style configs to `styles/config.{style}.yaml`
   - Use new parameter names (`directory` instead of `folder`)

3. **Organize files**:
   - Move style-specific files to `styles/{style}/input/`
   - Move course materials to `notes/{category}/`

### Benefits

- **Cleaner Code**: Reduced from 3 command classes to 1 unified processor
- **Better Organization**: Clear separation of styles, notes, and general files
- **Automatic Discovery**: No need to specify every file path
- **Style Integration**: Automatic loading of style-specific configurations
- **Flexible Output**: Smart output directory management
- **Simplified CLI**: Fewer options, clearer intent

## File Structure

```
application/
├── cli.py                 # Simplified CLI interface
├── unified_processor.py   # Single processor for all modes
├── input_scanner.py       # 2-level input discovery
└── commands/
    ├── base.py           # Base command class
    └── refine.py         # Refinement command (unchanged)

examples/
└── usage_examples.py     # Usage examples and demos
```

This refined system provides a much cleaner and more maintainable codebase while offering enhanced functionality for organized presentation processing.