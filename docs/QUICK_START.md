# Quick Start Guide

Get started with Gemini Powerpoint Sage using the new three-mode system!

## 🌟 Method 1: All Styles Processing (Recommended)

Process all your presentations with all available styles at once.

### Step 1: Setup Your Files
```bash
# Put your PPTX and PDF files in the notes/ directory
mkdir -p notes
cp your-presentation.pptx notes/
cp your-presentation.pdf notes/
```

### Step 2: Run All Styles
```bash
python main.py --styles
# or simply:
python main.py
```

**That's it!** ✨ All styles will be processed automatically using their YAML configurations.

---

## 🎨 Method 2: Single Style Processing

Process with one specific style configuration.

### Choose a Style
```bash
# Cyberpunk style
python main.py --style-config cyberpunk

# Professional style  
python main.py --style-config professional

# Gundam style
python main.py --style-config gundam
```

---

## 📄 Method 3: Single File Processing

Quick processing of one specific file.

### Basic Usage
```bash
python main.py --pptx presentation.pptx --language en --style professional
```

### With Multiple Languages
```bash
python main.py --pptx presentation.pptx --language "en,zh-CN" --style Cyberpunk
```

---

## Test with Sample Data

Try it out with the included sample files:

```bash
# Test all styles (recommended)
python main.py --styles

# Test specific style
python main.py --style-config professional

# Test single file
python main.py --pptx notes/sample.pptx --language en --style professional
```

---

## Output Files

### YAML-Driven Processing (Modes 1 & 2)
Files are organized by style in their configured output directories:

```
notes/                              # Input files
├── presentation.pptx
├── presentation.pdf
└── cyberpunk/generate/             # Output from YAML config
    ├── presentation_en_notes.pptm      # Speaker notes only
    ├── presentation_en_visuals.pptm    # With redesigned slides
    └── presentation_en_visuals/        # Individual slide images
```

### Single File Processing (Mode 3)
Files are saved in the same directory as input:

```
input/
├── presentation.pptx
├── presentation.pdf
├── presentation_en_notes.pptm      # Generated files
├── presentation_en_visuals.pptm
└── presentation_en_visuals/
```

---

## Common Options

### Skip Visual Generation (Notes Only)
```bash
python main.py --styles --skip-visuals
python main.py --style-config cyberpunk --skip-visuals
```

### Generate Video Prompts
```bash
python main.py --styles --generate-videos
python main.py --style-config professional --generate-videos
```

### Available Styles
Each style has its own YAML configuration file:

- **🌃 Cyberpunk** - Neon colors, edgy, tech-savvy
- **📋 Professional** - Clean, business-appropriate  
- **🤖 Gundam** - Mecha-inspired, futuristic, tactical
- **🌌 starwars** - Epic space opera aesthetic
- **🎨 HK Comic** - Vibrant Hong Kong comic book style

Style configurations are in `styles/config.{style}.yaml` files.

---

## Need Help?

- **Three Modes**: See [FINAL_SYSTEM_SUMMARY.md](../FINAL_SYSTEM_SUMMARY.md)
- **Migration**: See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)
- **Styles**: See [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md)
- **Full Docs**: See [README.md](../README.md)

---

## Tips

1. **Start with All Styles** - `python main.py --styles` processes everything
2. **Test Single Styles** - Use `--style-config` for focused testing
3. **YAML Configurations** - All settings are in `styles/config.*.yaml` files
4. **Organized Output** - Each style outputs to its own directory
5. **Team Consistency** - Share YAML configs for consistent results

---

## Troubleshooting

### "No configuration file found for style"
Make sure the style name exists: `ls styles/config.*.yaml`

### "No PPTX/PDF pairs found"
Check that your input folder (from YAML config) contains matching PPTX and PDF files.

### "Missing Google Cloud credentials"
1. Set up `.env` file with your project ID
2. Or run: `gcloud auth application-default login`

### Need more help?
- Check [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) if migrating from old system
- See full documentation in [README.md](../README.md)
