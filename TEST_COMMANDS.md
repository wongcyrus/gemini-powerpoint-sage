# Quick Test Commands

## Test the New Prompt Rewriter with Styles

### starwars Style (NEW!)
```bash
./run.sh --config config.starwars.yaml
```

**Expected Output:**
- Speaker notes with Jedi Master voice
- References to "the Force", "the Rebellion", "the Empire"
- Epic, inspirational tone
- Slides with deep space backgrounds and cinematic lighting
- Gold/yellow text on black backgrounds
- Holographic effects and starfield backgrounds

### Gundam Style
```bash
./run.sh --config config.gundam.yaml
```

**Expected Output:**
- Speaker notes with Char Aznable-style dramatic speeches
- References to "gravity", "evolution", "Newtypes"
- Aristocratic, philosophical tone
- Mecha anime aesthetic slides
- Tricolor schemes (Blue, White, Red, Yellow)
- Space colony backgrounds

### Cyberpunk Style
```bash
./run.sh --config config.cyberpunk.yaml
```

**Expected Output:**
- Edgy, direct speaker notes
- Tech-savvy street philosopher voice
- Neon-colored slides (electric blue, hot pink, purple)
- Dark backgrounds with glowing elements
- Glitch effects and grid patterns

### Sample/Professional Style
```bash
./run.sh --config config.sample.yaml
```

**Expected Output:**
- Standard professional speaker notes
- Clean, modern slide design
- Conservative color palette
- Business-appropriate tone

## Test Prompt Rewriter Directly

```bash
# Run the test script
python test_prompt_rewriter.py
```

This will:
1. Create a PromptRewriter with sample styles
2. Rewrite designer and writer prompts
3. Show statistics and previews
4. Verify the LLM integration works

## Test with Different Languages

```bash
# starwars in Chinese
./run.sh --config config.starwars.yaml --language zh-CN

# Gundam in Japanese (fitting!)
./run.sh --config config.gundam.yaml --language ja

# Multiple languages
./run.sh --config config.cyberpunk.yaml --language "en,zh-CN,yue-HK"
```

## Test Output Locations

After running, check these directories:

```bash
# Generated files
tests/sample_data/generate/

# Speaker notes (notes only)
tests/sample_data/generate/cloudtech_en_with_notes.pptm

# With visuals
tests/sample_data/generate/cloudtech_en_with_visuals.pptm

# Visual assets
tests/sample_data/generate/cloudtech_en_visuals/

# Progress tracking
tests/sample_data/generate/cloudtech_en_progress.json

# Logs
logs/gemini_powerpoint_sage_*.log
```

## Verify Prompt Rewriting

Check the logs to see the prompt rewriter in action:

```bash
# View latest log
tail -f logs/gemini_powerpoint_sage_*.log | grep -A 20 "PROMPT REWRITER"
```

Look for:
- "PROMPT REWRITER INITIALIZED (LLM-POWERED)"
- "REWRITING DESIGNER PROMPT WITH LLM"
- "REWRITING WRITER PROMPT WITH LLM"
- "✓ Designer prompt rewritten successfully"
- "✓ Writer prompt rewritten successfully"

## Debug Mode

For detailed prompt inspection:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with config
./run.sh --config config.starwars.yaml

# Check logs for full rewritten prompts
grep -A 100 "FULL REWRITTEN" logs/gemini_powerpoint_sage_*.log
```

## Compare Styles

Run the same presentation with different styles to compare:

```bash
# starwars version
./run.sh --config config.starwars.yaml
mv tests/sample_data/generate/cloudtech_en_with_notes.pptm \
   tests/sample_data/generate/cloudtech_starwars.pptm

# Gundam version
./run.sh --config config.gundam.yaml
mv tests/sample_data/generate/cloudtech_en_with_notes.pptm \
   tests/sample_data/generate/cloudtech_gundam.pptm

# Cyberpunk version
./run.sh --config config.cyberpunk.yaml
mv tests/sample_data/generate/cloudtech_en_with_notes.pptm \
   tests/sample_data/generate/cloudtech_cyberpunk.pptm

# Now compare the three versions!
```

## Performance Testing

```bash
# Time the execution
time ./run.sh --config config.starwars.yaml

# Skip visuals for faster testing (notes only)
time ./run.sh --config config.starwars.yaml --skip-visuals
```

## Troubleshooting Tests

### If prompts aren't being rewritten:

1. Check that the agent is initialized:
   ```bash
   grep "prompt_rewriter_agent" logs/*.log
   ```

2. Check for LLM errors:
   ```bash
   grep "Failed to rewrite" logs/*.log
   ```

3. Verify fallback is working:
   ```bash
   grep "Falling back to simple concatenation" logs/*.log
   ```

### If styles aren't being applied:

1. Check config file syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.starwars.yaml'))"
   ```

2. Verify styles are loaded:
   ```bash
   grep "Visual Style:" logs/*.log
   grep "Speaker Style:" logs/*.log
   ```

3. Check agent creation:
   ```bash
   grep "CREATING AGENTS WITH PROMPT REWRITER" logs/*.log
   ```

## Clean Up Test Outputs

```bash
# Remove generated files
rm -rf tests/sample_data/generate/*

# Remove logs
rm -rf logs/*

# Start fresh
./run.sh --config config.starwars.yaml
```

## Quick Validation Checklist

After running a test, verify:

- [ ] Output files created in `tests/sample_data/generate/`
- [ ] Speaker notes contain style-appropriate language
- [ ] Visuals match the described aesthetic
- [ ] Progress file shows all slides processed
- [ ] No errors in log file
- [ ] Prompt rewriter logged successful rewrites
- [ ] Styles are deeply integrated (not just appended)

## Success Indicators

**Good Signs:**
- ✅ Log shows "LLM-POWERED" rewriter initialization
- ✅ "✓ Designer prompt rewritten successfully"
- ✅ "✓ Writer prompt rewritten successfully"
- ✅ Speaker notes use style-specific vocabulary
- ✅ Visuals match color palette and aesthetic
- ✅ Tone is consistent throughout presentation

**Warning Signs:**
- ⚠️ "Falling back to simple concatenation" (LLM failed, but still works)
- ⚠️ Generic speaker notes (style not applied)
- ⚠️ Visuals don't match style description

**Error Signs:**
- ❌ "Failed to rewrite" without fallback
- ❌ Missing output files
- ❌ Crash or exception in logs
