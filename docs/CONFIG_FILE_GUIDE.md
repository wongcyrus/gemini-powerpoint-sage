# Configuration File Guide

The system uses YAML configuration files in the `styles/` directory to manage processing settings and style definitions.

## Quick Start

### 1. Choose an Existing Style Config

```bash
ls styles/config.*.yaml
# styles/config.cyberpunk.yaml
# styles/config.gundam.yaml  
# styles/config.professional.yaml
# styles/config.starwars.yaml
```

### 2. Run with Style Config

```bash
python main.py --style-config cyberpunk
```

### 3. Or Create Your Own

Copy an existing config:

```bash
cp styles/config.professional.yaml styles/config.mystyle.yaml
```

Edit `styles/config.mystyle.yaml`:

```yaml
input_folder: "notes"
output_dir: "notes/mystyle/generate"
language: "en"
style:
  visual_style: "Your visual description here..."
  speaker_style: "Your speaker persona here..."
```

Run it:

```bash
python main.py --style-config mystyle
```

## Configuration File Format

Configuration files use **YAML format** for readability and comments support.

**Example:**
```yaml
# My presentation config
pptx: "slides.pptx"
pdf: "slides.pdf"
style: "cyberpunk"  # Use cyberpunk theme
language: "en,zh-CN"  # English and Chinese
```

**Why YAML?**
- Supports comments for documentation
- More readable than JSON
- Easier to edit manually
- Industry standard for configuration

## Configuration Options

### Required Settings

```yaml
input_folder: "notes"                    # Where to find PPTX/PDF pairs
output_dir: "notes/mystyle/generate"     # Where to save results
language: "en"                           # Language(s) to process
```

### Style Definition (Required)

```yaml
style:
  visual_style: |
    Detailed visual aesthetic description:
    - Color palette with hex codes
    - Typography and layout preferences
    - Visual elements and mood
    
  speaker_style: |
    Detailed speaker persona description:
    - Tone and voice characteristics
    - Key vocabulary and phrases
    - Example speaking patterns
```

### Optional Settings

```yaml
skip_visuals: false      # Skip visual generation (notes only)
generate_videos: false   # Generate video prompts
retry_errors: false      # Retry failed slides
```

## Global Options

You can add global options to any style config:

```bash
# Skip visuals for any style
python main.py --style-config cyberpunk --skip-visuals

# Generate videos for any style  
python main.py --style-config gundam --generate-videos
```

## Multiple Style Configurations

The `styles/` directory contains different style configurations:

```bash
styles/
├── config.cyberpunk.yaml      # Neon dystopian aesthetic
├── config.gundam.yaml         # Mecha anime style
├── config.professional.yaml   # Clean business style
└── config.starwars.yaml       # Epic space opera style
```

Use them like:
```bash
python main.py --style-config cyberpunk
python main.py --style-config gundam
python main.py --styles  # Process all styles
```

## Example Configurations

### Example 1: Professional Style

**styles/config.professional.yaml:**
```yaml
input_folder: "notes"
output_dir: "notes/professional/generate"
language: "en"
style:
  visual_style: |
    Clean, modern business aesthetic
    - Conservative color palette: Navy (#003366), Gray (#666666), White
    - Sans-serif typography (Arial, Helvetica)
    - Minimal decorative elements
    
  speaker_style: |
    Professional business presenter
    - Formal, authoritative tone
    - Clear, structured communication
    - Uses business terminology appropriately
```

**Usage:**
```bash
python main.py --style-config professional
```

### Example 2: Multi-Language Cyberpunk

**styles/config.cyberpunk.yaml:**
```yaml
input_folder: "notes"
output_dir: "notes/cyberpunk/generate"
language: "en,zh-CN,ja"
style:
  visual_style: |
    Cyberpunk aesthetic with neon colors
    - Electric Blue (#00FFFF), Hot Pink (#FF1493), Purple (#9D00FF)
    - Dark backgrounds (#0A0E27) with glowing elements
    - Futuristic typography with sharp angles
    
  speaker_style: |
    Tech-savvy street philosopher
    - Edgy, direct communication style
    - Uses tech slang and cutting-edge terminology
    - Challenges conventional thinking
```

**Usage:**
```bash
python main.py --style-config cyberpunk
```

### Example 3: Notes Only (No Visuals)

**styles/config.notes-only.yaml:**
```yaml
input_folder: "notes"
output_dir: "notes/notes-only/generate"
language: "en"
skip_visuals: true  # Skip visual generation
style:
  speaker_style: |
    Clear, concise presenter
    - Direct communication
    - Focuses on key points
```

**Usage:**
```bash
python main.py --style-config notes-only
```

## Tips

1. **Version Control**: Commit style configs in `styles/` directory for team sharing
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

## Create New Style Config

To create a new style configuration:

```bash
# Copy existing config as template
cp styles/config.professional.yaml styles/config.mystyle.yaml

# Edit the new config
# - Change output_dir to "notes/mystyle/generate"
# - Customize visual_style and speaker_style sections
# - Adjust language and other settings as needed
```

## See Also

- [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md) - Style/theme examples
- [README.md](README.md) - Main documentation
- [.env.example](.env.example) - Environment variables
