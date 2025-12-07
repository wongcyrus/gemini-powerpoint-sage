# Quick Start Guide

Get started with Gemini Powerpoint Sage in 3 easy steps!

## Method 1: Using Config File (Recommended) ⭐

### Step 1: Setup
```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml with your files
nano config.yaml  # or use your favorite editor
```

### Step 2: Configure
Edit `config.yaml`:
```yaml
pptx: "path/to/your/presentation.pptx"
pdf: "path/to/your/presentation.pdf"
style: "Professional"  # or Gundam, Cyberpunk, Minimalist
language: "en"
```

### Step 3: Run
```bash
python main.py --config config.yaml
```

**That's it!** ✨

---

## Method 2: Command Line

### Basic Usage
```bash
python main.py --pptx presentation.pptx --pdf presentation.pdf
```

### With Custom Style
```bash
python main.py --pptx presentation.pptx --style "Gundam"
```

### Multiple Languages
```bash
python main.py --pptx presentation.pptx --language "en,zh-CN"
```

---

## Test with Sample Data

Try it out with the included sample:

```bash
# Using config file
python main.py --config config.sample.yaml

# Or command line
python main.py --pptx tests/sample_data/cloudtech.pptm --pdf tests/sample_data/cloudtech.pdf
```

---

## Output Files

Your generated files will be in the `generate/` folder:

```
your-presentation-folder/
├── presentation.pptx
├── presentation.pdf
└── generate/
    ├── presentation_en_with_notes.pptm      # Speaker notes only
    ├── presentation_en_with_visuals.pptm    # With redesigned slides
    └── presentation_en_visuals/             # Individual slide images
```

---

## Common Options

### Skip Visual Generation (Notes Only)
```bash
python main.py --config config.yaml --skip-visuals
```

### Process Entire Folder
```yaml
# In config.yaml
folder: "path/to/presentations/"
```

### Custom Style/Theme
```bash
python main.py --config config.yaml --style "Cyberpunk"
```

Available styles:
- **Professional** (default) - Clean, business-appropriate
- **Gundam** - Mecha-inspired, futuristic, tactical
- **Cyberpunk** - Neon colors, edgy, tech-savvy
- **Minimalist** - Simple, clean, lots of whitespace
- **Corporate** - Traditional business style
- **Custom** - Describe your own: "Anime - vibrant colors"

---

## Need Help?

- **Config Files**: See [CONFIG_FILE_GUIDE.md](CONFIG_FILE_GUIDE.md)
- **Styles**: See [STYLE_EXAMPLES.md](STYLE_EXAMPLES.md)
- **Full Docs**: See [README.md](README.md)

---

## Tips

1. **Use Config Files** - Much easier than long command lines
2. **Start Simple** - Try with default settings first
3. **Experiment with Styles** - Different styles for different audiences
4. **Version Control** - Keep `config.example.yaml`, ignore `config.yaml`
5. **Share Configs** - Share example configs with your team

---

## Troubleshooting

### "Configuration file not found"
Check your file path. Use `ls` to verify the file exists.

### "PPTX file not found"
Make sure the path in your config is correct. Use absolute paths if needed.

### "Missing Google Cloud credentials"
1. Set up `.env` file with your project ID
2. Or run: `gcloud auth application-default login`

### Need more help?
Check the full documentation in [README.md](README.md)
