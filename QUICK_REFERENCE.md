# Quick Reference Card

## 🚀 Run Commands

```bash
# Star Wars Style (NEW!)
./run.sh --config config.starwars.yaml

# Gundam Style
./run.sh --config config.gundam.yaml

# Cyberpunk Style
./run.sh --config config.cyberpunk.yaml

# Professional Style
./run.sh --config config.sample.yaml

# Custom file
./run.sh --pptx file.pptx --pdf file.pdf

# Folder batch
./run.sh --folder ./presentations

# Multiple languages
./run.sh --config config.starwars.yaml --language "en,zh-CN"
```

## 📁 Output Locations

```
tests/sample_data/generate/
├── cloudtech_en_with_notes.pptm      # Notes only
├── cloudtech_en_with_visuals.pptm    # With redesigned slides
├── cloudtech_en_progress.json        # Progress tracking
└── cloudtech_en_visuals/             # Generated slide images
    ├── slide_1_reimagined.png
    ├── slide_2_reimagined.png
    └── ...
```

## 🎨 Available Styles

| Style | Visual | Voice | Best For |
|-------|--------|-------|----------|
| **Star Wars** | Space opera, cinematic | Jedi Master | Strategic briefings |
| **Gundam** | Mecha anime | Char Aznable | Dramatic tech reveals |
| **Cyberpunk** | Neon dystopia | Street philosopher | Disruptive innovation |
| **Sample** | Professional | Standard | Business meetings |

## 🔧 Common Tasks

### Create Custom Style
```bash
cp config.starwars.yaml config.mystyle.yaml
# Edit visual_style and speaker_style
./run.sh --config config.mystyle.yaml
```

### Test Prompt Rewriter
```bash
python test_prompt_rewriter.py
```

### Check Logs
```bash
tail -f logs/gemini_powerpoint_sage_*.log
grep "PROMPT REWRITER" logs/*.log
```

### Clean Up
```bash
rm -rf tests/sample_data/generate/*
rm -rf logs/*
```

## 📚 Documentation

- **Prompt Rewriter:** `docs/PROMPT_REWRITER.md`
- **Style Gallery:** `docs/STYLE_CONFIGS.md`
- **Run Scripts:** `docs/RUN_SCRIPTS_USAGE.md`
- **Test Commands:** `TEST_COMMANDS.md`
- **Full Summary:** `UPDATES_SUMMARY.md`

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

## 🌟 Example Workflow

```bash
# 1. Choose or create style
./run.sh --config config.starwars.yaml

# 2. Check output
ls tests/sample_data/generate/

# 3. Review presentation
# Open cloudtech_en_with_visuals.pptm

# 4. Iterate if needed
# Edit config.starwars.yaml
./run.sh --config config.starwars.yaml

# 5. Use for real presentation
./run.sh --config config.starwars.yaml --pptx my-presentation.pptx
```

---

**Need help?** See `UPDATES_SUMMARY.md` for complete details.

**May the Force be with your presentations!** 🌌
