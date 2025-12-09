# Output File Organization

## Overview

The system organizes outputs by **folder structure** based on style, not by filename. This keeps filenames clean and makes it easy to compare different styles side-by-side.

## Folder-Based Organization

### Default Structure

```
project/
├── presentation.pptx
├── presentation.pdf
└── generate/
    ├── presentation_en_notes.pptx          # Professional style (default)
    ├── presentation_en_visuals.pptx
    ├── presentation_en_progress.json       # Progress tracking
    ├── cyberpunk/
    │   ├── presentation_en_notes.pptx      # Cyberpunk style
    │   ├── presentation_en_visuals.pptx
    │   ├── presentation_en_progress.json
    │   └── presentation_en_visuals/
    │       └── slide_1_reimagined.png
    ├── gundam/
    │   ├── presentation_en_notes.pptx      # Gundam style
    │   ├── presentation_en_visuals.pptx
    │   ├── presentation_en_progress.json
    │   └── presentation_en_visuals/
    └── star_wars/
        ├── presentation_en_notes.pptx      # Star Wars style
        ├── presentation_en_visuals.pptx
        └── presentation_en_progress.json
```

### Key Points

1. **Professional style** (default) goes directly in `generate/`
2. **Other styles** get their own subfolder: `generate/{style}/`
3. **Filenames stay clean** - no style suffix needed
4. **Language code is always included**: `presentation_en_notes.pptx`, `presentation_zh-CN_notes.pptx`

## Filename Convention

Filenames **always include language code** (not style):

```
{original_name}_{language}_{suffix}.{extension}
```

### Components:
- **original_name**: Original presentation filename (without extension)
- **language**: Language code (always required) - e.g., `en`, `zh-CN`, `ja`, `yue-HK`
- **suffix**: Type of output (`notes` or `visuals`)
- **extension**: Original file extension (`.pptx`, `.pptm`)

**Note:** Language code is mandatory for all outputs, including English (`en`).

## Examples

### Basic Processing (English, Professional)
```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf --language en
```
**Output:**
```
generate/
├── presentation_en_notes.pptx
└── presentation_en_visuals.pptx
```

### With Cyberpunk Style
```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf --style Cyberpunk --language en
```
**Output:**
```
generate/
└── cyberpunk/
    ├── presentation_en_notes.pptx
    └── presentation_en_visuals.pptx
```

### With Chinese Language
```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf --language zh-CN
```
**Output:**
```
generate/
├── presentation_zh-CN_notes.pptx
└── presentation_zh-CN_visuals.pptx
```

### With Gundam Style + Chinese
```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf --style Gundam --language zh-CN
```
**Output:**
```
generate/
└── gundam/
    ├── presentation_zh-CN_notes.pptx
    └── presentation_zh-CN_visuals.pptx
```

### Multiple Styles - No Overwrites!
```bash
python main.py --pptx deck.pptx --pdf deck.pdf --style Cyberpunk --language en
python main.py --pptx deck.pptx --pdf deck.pdf --style Gundam --language en
python main.py --pptx deck.pptx --pdf deck.pdf --style "Star Wars" --language en
```
**Output:**
```
generate/
├── cyberpunk/
│   └── deck_en_notes.pptx
├── gundam/
│   └── deck_en_notes.pptx
└── star_wars/
    └── deck_en_notes.pptx
```

## Custom Output Directory

Use `--output-dir` to specify a custom location. This **overrides** the style-based folder structure:

```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf \
  --style Cyberpunk --output-dir ./output/cyberpunk
```

**Output:**
```
output/
└── cyberpunk/
    ├── presentation_notes.pptx
    └── presentation_visuals.pptx
```

### Organizing Multiple Styles

```bash
# Process each style to its own directory
python main.py --pptx deck.pptx --pdf deck.pdf \
  --style Cyberpunk --output-dir ./output/cyberpunk --language en

python main.py --pptx deck.pptx --pdf deck.pdf \
  --style Gundam --output-dir ./output/gundam --language en

python main.py --pptx deck.pptx --pdf deck.pdf \
  --style "Star Wars" --output-dir ./output/starwars --language en
```

**Output:**
```
output/
├── cyberpunk/
│   └── deck_en_notes.pptx
├── gundam/
│   └── deck_en_notes.pptx
└── starwars/
    └── deck_en_notes.pptx
```

## Using Configuration Files

Specify output directory in YAML config:

```yaml
# styles/config.cyberpunk.yaml
pptx: "presentation.pptx"
pdf: "presentation.pdf"
style: "Cyberpunk"
output_dir: "./output/cyberpunk"
```

Then run:
```bash
python main.py --config styles/config.cyberpunk.yaml
```

## Batch Processing

When processing a folder, each style gets its own subfolder:

```bash
python main.py --folder ./presentations --style Gundam
```

**Output:**
```
presentations/
├── deck1.pptx
├── deck2.pptx
└── generate/
    └── gundam/
        ├── deck1_notes.pptx
        ├── deck2_notes.pptx
        └── ...
```

With custom output directory:
```bash
python main.py --folder ./presentations --style Gundam --output-dir ./output
```

**Output:**
```
output/
├── deck1_notes.pptx
├── deck2_notes.pptx
└── ...
```

## Best Practices

### 1. Default Workflow (Recommended)
Let the system organize by style automatically:
```bash
python main.py --pptx deck.pptx --pdf deck.pdf --style Cyberpunk
python main.py --pptx deck.pptx --pdf deck.pdf --style Gundam
```
Result: Clean folder structure in `generate/cyberpunk/` and `generate/gundam/`

### 2. Custom Organization
Use `--output-dir` when you need specific folder structure:
```bash
python main.py --pptx deck.pptx --pdf deck.pdf \
  --style Cyberpunk --output-dir ./client-a/cyberpunk
```

### 3. Multiple Languages
Process English first, then other languages:
```bash
# English first (enables translation mode)
python main.py --pptx deck.pptx --pdf deck.pdf --style Gundam --language en

# Then other languages
python main.py --pptx deck.pptx --pdf deck.pdf --style Gundam --language zh-CN
python main.py --pptx deck.pptx --pdf deck.pdf --style Gundam --language ja
```

Result:
```
generate/
└── gundam/
    ├── deck_en_notes.pptx           # English
    ├── deck_zh-CN_notes.pptx        # Chinese
    └── deck_ja_notes.pptx           # Japanese
```

### 4. Comparing Styles
All styles in one place for easy comparison:
```
generate/
├── deck_en_notes.pptx              # Professional
├── cyberpunk/
│   └── deck_en_notes.pptx          # Cyberpunk
├── gundam/
│   └── deck_en_notes.pptx          # Gundam
└── star_wars/
    └── deck_en_notes.pptx          # Star Wars
```

## Complete Output Structure

Each output folder is **self-contained** with all generated files including progress tracking:

```
generate/
└── cyberpunk/
    ├── presentation_en_notes.pptx
    ├── presentation_en_visuals.pptx
    ├── presentation_en_progress.json        # Progress tracking
    ├── presentation_en_visuals/
    │   ├── slide_1_reimagined.png
    │   └── slide_2_reimagined.png
    └── presentation_en_videos/
        ├── slide_1_video_prompt.txt
        └── slide_2_video_prompt.txt
```

With language:
```
generate/
└── gundam/
    ├── presentation_zh-CN_notes.pptx
    ├── presentation_zh-CN_visuals.pptx
    ├── presentation_zh-CN_progress.json     # Progress tracking
    └── presentation_zh-CN_visuals/
        └── slide_1_reimagined.png
```

## Progress Files

Progress JSON files are **always included** in the output folder, making each folder self-contained:

```
generate/
├── cyberpunk/
│   ├── presentation_en_progress.json
│   ├── presentation_en_notes.pptx
│   └── presentation_en_visuals.pptx
└── gundam/
    ├── presentation_zh-CN_progress.json
    ├── presentation_zh-CN_notes.pptx
    └── presentation_zh-CN_visuals.pptx
```

**Benefits:**
- **Self-contained**: Each folder has everything needed
- **Resume processing**: Can resume from any folder independently
- **Track progress**: See which slides succeeded/failed
- **Portable**: Move folders without losing progress data
- **Retry errors**: Retry specific style/language combinations

## Tips

1. **Let the system organize** - Default folder structure works great
2. **Use `--output-dir`** only when you need custom organization
3. **Process English first** for translation mode
4. **Keep styles separate** - Each style in its own folder
5. **Clean filenames** - No style clutter in filenames

## Troubleshooting

### Where are my files?
- **Professional style**: `generate/presentation_en_notes.pptx`
- **Other styles**: `generate/{style}/presentation_en_notes.pptx`
- **Custom output**: Whatever you specified in `--output-dir`
- **Note**: Language code (`en`, `zh-CN`, etc.) is always in the filename

### Files overwriting?
- Different styles go to different folders automatically
- Different languages get different filenames
- Use `--output-dir` for complete separation

### Can't find output directory?
The system creates directories automatically. Check:
1. `generate/` folder next to your input file
2. `generate/{style}/` for non-Professional styles
3. Your custom `--output-dir` if specified

## Summary

**Folder-based organization** keeps things clean:
- ✅ Styles organized by folder
- ✅ Clean filenames (no style suffix)
- ✅ Easy to compare styles
- ✅ No overwrites
- ✅ Language in filename when needed
