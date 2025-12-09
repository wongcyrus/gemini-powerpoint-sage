# Style Configuration Files

This directory contains YAML configuration files that define visual and speaker styles for presentations.

## Available Styles

### config.sample.yaml
Basic example configuration showing the structure.

### config.cyberpunk.yaml
Cyberpunk-themed style with neon colors and futuristic aesthetics.

### config.gundam.yaml
Gundam/mecha-themed style with military and technical terminology.

### config.starwars.yaml
Star Wars-themed style with galactic and sci-fi elements.

## Usage

Use these configuration files with the `--config` flag:

```bash
python main.py --config styles/config.gundam.yaml --pptx presentation.pptx --pdf presentation.pdf
```

Or specify the style directly:

```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf --style Gundam
```

## Creating Custom Styles

Copy `config.sample.yaml` and modify the `visual_style` and `speaker_style` sections to create your own custom style.

### Structure

```yaml
# Input files
pptx: "path/to/presentation.pptx"
pdf: "path/to/presentation.pdf"

# Output directory (recommended pattern: {style}/generate/)
output_dir: "cyberpunk/generate"

# Style configuration
style: "YourStyleName"

# Visual style (for slide design)
visual_style: |
  Your visual style description here...
  - Color schemes
  - Typography
  - Visual elements

# Speaker style (for speaker notes)
speaker_style: |
  Your speaker style description here...
  - Tone and voice
  - Vocabulary
  - Phrasing patterns

# Optional parameters
language: "en"
skip_visuals: false
generate_videos: false
```

### Output Directory Pattern

**Recommended:** Use `{style}/generate/` pattern for clean organization:

```yaml
# Cyberpunk style
output_dir: "cyberpunk/generate"

# Gundam style
output_dir: "gundam/generate"

# Star Wars style
output_dir: "star_wars/generate"
```

This creates a structure like:
```
project/
├── presentation.pptx
├── presentation.pdf
├── cyberpunk/
│   └── generate/
│       ├── presentation_en_notes.pptx
│       └── presentation_en_visuals.pptx
├── gundam/
│   └── generate/
│       ├── presentation_en_notes.pptx
│       └── presentation_en_visuals.pptx
└── star_wars/
    └── generate/
        ├── presentation_en_notes.pptx
        └── presentation_en_visuals.pptx
```

**Benefits:**
- Each style has its own top-level folder
- Easy to compare different styles
- Clean separation of outputs
- `generate/` subfolder keeps outputs organized

## Style Guidelines

### Visual Style
Define how slides should look:
- Color palette
- Typography choices
- Layout preferences
- Visual metaphors
- Design elements

### Speaker Style
Define how speaker notes should sound:
- Tone (formal, casual, energetic, etc.)
- Vocabulary (technical, simple, domain-specific)
- Sentence structure
- Personality traits
- Example phrases

## Examples

### Minimalist Style
```yaml
visual_style: |
  Clean, minimal design with lots of white space.
  Use simple sans-serif fonts.
  Limited color palette (black, white, one accent color).
  Focus on clarity and simplicity.

speaker_style: |
  Clear, concise, and direct.
  Short sentences.
  No jargon.
  Professional but approachable.
```

### Academic Style
```yaml
visual_style: |
  Traditional academic presentation style.
  Serif fonts for titles.
  Charts and data visualizations.
  Formal color scheme (navy, gray, white).

speaker_style: |
  Formal academic tone.
  Precise terminology.
  Evidence-based statements.
  References to research and data.
```

## Notes

- Style configurations are optional
- Default style is "Professional" if not specified
- Styles affect both visual generation and speaker notes
- You can mix and match visual and speaker styles
