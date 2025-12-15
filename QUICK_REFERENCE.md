# Quick Reference Card

## 🚀 Three Processing Modes

### 🌟 All Styles Processing (Production)
```bash
python main.py --styles              # Process all available styles
python main.py                       # Same as above (default)
```

### 🎨 Single Style Processing (Focused)
```bash
python main.py --style-config starwars      # starwars style only
python main.py --style-config gundam        # gundam style only
python main.py --style-config cyberpunk     # cyberpunk style only
python main.py --style-config professional  # professional style only
python main.py --style-config hkcomic       # Hong Kong Comic style only
```

### 📄 Single File Processing (Quick Testing)
```bash
python main.py --pptx file.pptx --language en --style starwars
python main.py --pptx file.pptx --language "en,zh-CN" --style gundam
python main.py --pptx file.pptx --language en --style professional --output-dir output/test
```

## ⚙️ Additional Options (All Modes)
```bash
python main.py --styles --skip-visuals              # Skip visual generation
python main.py --style-config cyberpunk --generate-videos  # Generate video prompts
python main.py --styles --retry-errors              # Retry failed slides
python main.py --style-config gundam --course-id course123  # Add course context
```

## 📁 Output Locations

### YAML-Driven Processing (Modes 1 & 2)
```
notes/                                # input_folder from YAML
├── presentation.pptx
├── presentation.pdf
└── ...

notes/cyberpunk/generate/             # output_dir from YAML
├── presentation_en_notes.pptm        # Notes only
├── presentation_en_visuals.pptm      # With redesigned slides
├── presentation_en_progress.json     # Progress tracking
└── presentation_en_visuals/          # Generated slide images
    ├── slide_1_reimagined.png
    ├── slide_2_reimagined.png
    └── ...
```

### Single File Processing (Mode 3)
```
input/
├── presentation.pptx                 # Input file
├── presentation.pdf                  # Input PDF
├── presentation_en_notes.pptm        # Generated notes
├── presentation_en_visuals.pptm      # Generated visuals
├── presentation_en_progress.json     # Progress tracking
└── presentation_en_visuals/          # Generated images
```

## 🎨 Available Styles

| Style | Visual | Voice | Best For |
|-------|--------|-------|----------|
| **starwars** | Space opera, cinematic | Jedi Master | Strategic briefings |
| **gundam** | Mecha anime | Char Aznable | Dramatic tech reveals |
| **cyberpunk** | Neon dystopia | Street philosopher | Disruptive innovation |
| **professional** | professional | Standard | Business meetings |

## 🔧 Common Tasks

### Create Custom Style
```bash
cp styles/config.starwars.yaml styles/config.mystyle.yaml
# Edit input_folder, output_dir, language, and style sections
python main.py --style-config mystyle
```

### Test Single File
```bash
python main.py --pptx test.pptx --language en --style professional
```

### Process Specific Style
```bash
python main.py --style-config cyberpunk
```

### Check Configuration
```bash
# View available styles
ls styles/config.*.yaml

# Check specific config
cat styles/config.cyberpunk.yaml
```

### Performance Configuration
```bash
# High-performance caching (default: enabled)
export PROMPT_CACHE_ENABLED=true
export PROMPT_CACHE_MAX_SIZE_MB=100
export PROMPT_CACHE_TTL_DAYS=30

# TTS configuration
export MODEL_TTS=gemini-2.5-flash-tts
export TTS_TIMEOUT_SECONDS=90

# Check cache performance
ls -la cache/prompt_rewriter/
```

### Clean Up
```bash
rm -rf notes/*/generate/*
rm -rf logs/*
rm -rf cache/prompt_rewriter/*  # Clear prompt cache
```

## 📚 Documentation

- **Prompt Rewriter:** `docs/PROMPT_REWRITER.md`
- **Performance & Caching:** `docs/PERFORMANCE_CACHING.md`
- **Style Gallery:** `docs/STYLE_CONFIGS.md`
- **Run Scripts:** `docs/RUN_SCRIPTS_USAGE.md`
- **Test Commands:** `TEST_COMMANDS.md`
- **Documentation:** `docs/README.md`

## ⚡ Quick Checks

### Is it working?
```bash
# Check for LLM-powered rewriting
grep "LLM-POWERED" logs/*.log

# Check for successful rewrites
grep "✓.*rewritten successfully" logs/*.log
```

### Verify output
```bash
# List generated files
ls -lh tests/sample_data/generate/

# Check progress
cat tests/sample_data/generate/cloudtech_en_progress.json | jq '.slides_processed'
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Virtual environment not found" | Run `./setup.sh` |
| "Python not found" | Install Python 3.8+ |
| "Config file error" | Check YAML syntax |
| "Permission denied" | Run `chmod +x run.sh` |
| Styles not applied | Check logs for errors |

## 💡 Pro Tips

1. **Use config files** for complex styles (easier than CLI args)
2. **Test with sample data** before real presentations
3. **Check logs** to verify prompt rewriting
4. **Start with existing styles** then customize
5. **Be specific** in style descriptions for better results

## 🎯 Success Indicators

✅ Log shows "LLM-POWERED" initialization  
✅ "✓ prompt rewritten successfully" messages  
✅ Speaker notes use style-specific vocabulary  
✅ Visuals match color palette and aesthetic  
✅ Tone is consistent throughout  

## 🌟 Example Workflows

### Development Workflow
```bash
# 1. Test single file quickly
python main.py --pptx test.pptx --language en --style professional

# 2. Test specific style configuration
python main.py --style-config cyberpunk

# 3. Check output
ls notes/cyberpunk/generate/

# 4. Iterate if needed
# Edit styles/config.cyberpunk.yaml
python main.py --style-config cyberpunk
```

### Production Workflow
```bash
# 1. Process all styles for complete coverage
python main.py --styles

# 2. Check all outputs
ls notes/*/generate/

# 3. Review presentations
# Open notes/cyberpunk/generate/*_visuals.pptm
# Open notes/professional/generate/*_visuals.pptm
```

### Team Workflow
```bash
# Designer: Test their style
python main.py --style-config gundam

# Content team: Process everything
python main.py --styles

# QA: Validate specific style
python main.py --style-config professional
```

---

**Need help?** See `docs/README.md` for complete documentation.

**May the Force be with your presentations!** 🌌
