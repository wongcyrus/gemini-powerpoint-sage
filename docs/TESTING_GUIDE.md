# Quick Test Commands

## Test the New Prompt Rewriter with Styles

### starwars Style (NEW!)
```bash
python main.py --style-config starwars
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
python main.py --style-config gundam
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
python main.py --style-config cyberpunk
```

**Expected Output:**
- Edgy, direct speaker notes
- Tech-savvy street philosopher voice
- Neon-colored slides (electric blue, hot pink, purple)
- Dark backgrounds with glowing elements
- Glitch effects and grid patterns

### Sample/Professional Style
```bash
python main.py --style-config professional
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
# starwars in Chinese (configure language in YAML)
python main.py --style-config starwars

# Gundam in Japanese (configure language in YAML)
python main.py --style-config gundam

# Multiple languages (configure in YAML)
python main.py --style-config cyberpunk
```

**Note:** Language settings are now configured in the YAML files (`styles/config.*.yaml`), not via CLI flags.

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
python main.py --style-config starwars

# Check logs for full rewritten prompts
grep -A 100 "FULL REWRITTEN" logs/gemini_powerpoint_sage_*.log
```

## Compare Styles

Run the same presentation with different styles to compare:

```bash
# starwars version
python main.py --style-config starwars
# Output goes to notes/starwars/generate/

# Gundam version  
python main.py --style-config gundam
# Output goes to notes/gundam/generate/

# Cyberpunk version
python main.py --style-config cyberpunk
# Output goes to notes/cyberpunk/generate/

# Now compare the three versions in their respective directories!
```

## Performance Testing

```bash
# Time the execution
time python main.py --style-config starwars

# Skip visuals for faster testing (notes only)
python main.py --style-config starwars --skip-visuals
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
python main.py --style-config starwars
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
