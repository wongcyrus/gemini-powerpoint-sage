# Configuration File Guide

Using configuration files makes it easier to manage multiple parameters and share settings with your team.

## Quick Start

### 1. Create Your Config File

Copy the example file:

```bash
cp config.example.yaml config.yaml
```

### 2. Edit Your Config File

Open `config.yaml` and customize:

```yaml
# Input files
pptx: "path/to/your/presentation.pptx"
pdf: "path/to/your/presentation.pdf"

# Settings
region: "us-central1"
language: "en"
style: "Gundam"
skip_visuals: false
```

### 3. Run with Config File

```bash
python main.py --config config.yaml
```

That's it! Much simpler than:
```bash
python main.py --pptx path/to/your/presentation.pptx --pdf path/to/your/presentation.pdf --region us-central1 --language en --style Gundam
```

## Configuration File Format

Configuration files use **YAML format** for readability and comments support.

**Example:**
```yaml
# My presentation config
pptx: "slides.pptx"
pdf: "slides.pdf"
style: "Cyberpunk"  # Use cyberpunk theme
language: "en,zh-CN"  # English and Chinese
```

**Why YAML?**
- Supports comments for documentation
- More readable than JSON
- Easier to edit manually
- Industry standard for configuration

## Configuration Options

### Required (choose one)

```yaml
# Single file
pptx: "presentation.pptx"
pdf: "presentation.pdf"  # Optional if same name

# OR folder processing
folder: "path/to/folder"
```

### Google Cloud Settings

```yaml
region: "global"  # or us-central1, europe-west1, etc.
```

### Language Settings

```yaml
# Single language
language: "en"

# Multiple languages
language: "en,zh-CN,yue-HK"
```

### Style/Theme

```yaml
style: "Professional"  # Default
# style: "Gundam"
# style: "Cyberpunk"
# style: "Minimalist"
# style: "Custom description here"
```

### Generation Options

```yaml
skip_visuals: false      # Only generate speaker notes
generate_videos: false   # Generate videos with Veo
retry_errors: false      # Retry failed slides
```

### Advanced Options

```yaml
course_id: "course-123"           # Optional context
progress_file: "custom.json"      # Custom progress file
```

## Command-Line Override

Command-line arguments always override config file settings:

```bash
# Config file has style: "Professional"
# This will use "Gundam" instead
python main.py --config config.yaml --style "Gundam"
```

## Multiple Configurations

Create different config files for different scenarios:

```bash
# Development config
config.dev.yaml

# Production config
config.prod.yaml

# Gundam-themed presentations
config.gundam.yaml

# Minimalist presentations
config.minimalist.yaml
```

Use them like:
```bash
python main.py --config config.gundam.yaml
python main.py --config config.minimalist.yaml
```

## Example Configurations

### Example 1: Simple Single File

**config.simple.yaml:**
```yaml
pptx: "presentation.pptx"
region: "global"
language: "en"
style: "Professional"
```

**Usage:**
```bash
python main.py --config config.simple.yaml
```

### Example 2: Multi-Language with Custom Style

**config.multilang.yaml:**
```yaml
pptx: "slides.pptx"
pdf: "slides.pdf"
region: "us-central1"
language: "en,zh-CN,yue-HK"
style: "Gundam - futuristic mecha-inspired design"
skip_visuals: false
```

**Usage:**
```bash
python main.py --config config.multilang.yaml
```

### Example 3: Folder Processing

**config.batch.yaml:**
```yaml
folder: "presentations/"
region: "global"
language: "en"
style: "Corporate"
retry_errors: true
```

**Usage:**
```bash
python main.py --config config.batch.yaml
```

### Example 4: Notes Only (No Visuals)

**config.notes-only.yaml:**
```yaml
pptx: "presentation.pptx"
region: "global"
language: "en"
skip_visuals: true  # Skip visual generation
```

**Usage:**
```bash
python main.py --config config.notes-only.yaml
```

## Tips

1. **Version Control**: Add `config.yaml` to `.gitignore` and commit `config.example.yaml` instead
2. **Team Sharing**: Share example configs with your team for consistency
3. **Documentation**: Add comments in YAML files to explain your choices
4. **Testing**: Create separate configs for testing vs production
5. **Validation**: The tool validates your config file and shows helpful error messages

## Troubleshooting

### "Configuration file not found"
- Check the path to your config file
- Use absolute path or path relative to current directory

### "Invalid YAML"
- Check for syntax errors (indentation, missing quotes, etc.)
- Use a YAML validator online
- Make sure colons have spaces after them: `key: value`

### "PyYAML is required"
- Install PyYAML: `pip install pyyaml`
- It's included in requirements.txt

### "Configuration must specify either 'pptx' or 'folder'"
- Make sure you have either `pptx` or `folder` in your config
- Don't specify both at the same time

## Generate Example Config

To create a new example config file:

```python
from config.config_loader import create_example_config

# Create YAML example
create_example_config("my-config.yaml")
```

Or simply copy the existing example:
```bash
cp config.example.yaml my-config.yaml
```

## See Also

- [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md) - Style/theme examples
- [README.md](README.md) - Main documentation
- [.env.example](.env.example) - Environment variables
