# Migration Guide - Old to New System

## Overview

The system has been completely refactored to use a pure YAML-driven approach with three distinct processing modes. This guide helps you migrate from the old CLI-heavy system to the new streamlined approach.

## What Changed

### Old System (Complex)
- Multiple redundant CLI options (`--folder`, `--input-folder`, `--notes`)
- Complex override logic between CLI and YAML
- Confusing precedence rules
- Many running methods and command classes

### New System (Simple)
- Three clear processing modes
- Pure YAML-driven configuration
- No redundant options
- Single unified processor

## Migration Steps

### 1. Update Your Commands

#### Old Commands → New Commands

```bash
# OLD: Folder processing with CLI parameters
./run.sh --folder presentations --language en,zh-CN --style Cyberpunk --output-dir output/

# NEW: YAML-driven processing
python main.py --style-config cyberpunk
```

```bash
# OLD: Input folder with overrides
./run.sh --input-folder notes --language en --style Professional

# NEW: Single style processing
python main.py --style-config professional
```

```bash
# OLD: Notes directory processing
./run.sh --notes --language zh-CN

# NEW: All styles processing (or specific style)
python main.py --styles
# or
python main.py --style-config professional
```

### 2. Create YAML Configurations

Move your CLI parameters into YAML configuration files:

#### Example Migration

**Old CLI Command:**
```bash
./run.sh --folder presentations --language "en,zh-CN,yue-HK" --style Cyberpunk --output-dir cyberpunk/output --generate-videos
```

**New YAML Config:** `styles/config.cyberpunk.yaml`
```yaml
input_folder: "presentations"
output_dir: "cyberpunk/output"
language: "en,zh-CN,yue-HK"
generate_videos: true
style:
  visual_style: "Cyberpunk Edgerunners aesthetic with neon colors..."
  speaker_style: "Night City edgerunner persona..."
```

**New Command:**
```bash
python main.py --style-config cyberpunk
```

### 3. Organize Your Files

#### Recommended Directory Structure

```
project/
├── styles/                          # Style configurations
│   ├── config.cyberpunk.yaml
│   ├── config.professional.yaml
│   └── config.gundam.yaml
├── notes/                           # Input files (from YAML configs)
│   ├── presentation1.pptx
│   ├── presentation1.pdf
│   ├── presentation2.pptx
│   └── presentation2.pdf
└── notes/                           # Output directories (from YAML configs)
    ├── cyberpunk/generate/
    ├── professional/generate/
    └── gundam/generate/
```

## Command Mapping

### Processing Modes

| Old Command | New Command | Description |
|-------------|-------------|-------------|
| `./run.sh --folder path/` | `python main.py --styles` | Process all styles |
| `./run.sh --input-folder path/` | `python main.py --style-config <style>` | Process one style |
| `./run.sh --notes` | `python main.py --styles` | Process all styles |
| `./run.sh --pptx file.pptx` | `python main.py --pptx file.pptx` | Single file (unchanged) |

### Parameters

| Old Parameter | New Location | Notes |
|---------------|--------------|-------|
| `--folder path` | YAML `input_folder` | Specified in config file |
| `--input-folder path` | YAML `input_folder` | Specified in config file |
| `--language "en,zh-CN"` | YAML `language` | Specified in config file |
| `--style "Cyberpunk"` | YAML `style` | Detailed style definition |
| `--output-dir path` | YAML `output_dir` | Specified in config file |
| `--generate-videos` | YAML `generate_videos` | Boolean in config file |
| `--skip-visuals` | YAML `skip_visuals` | Boolean in config file |

## YAML Configuration Template

Create your YAML configs using this template:

```yaml
# styles/config.{your-style}.yaml

# Input and output
input_folder: "notes"                    # Where to find PPTX/PDF pairs
output_dir: "notes/{your-style}/generate" # Where to save results

# Processing settings
language: "en,zh-CN"                     # Languages to process
skip_visuals: false                      # Skip visual generation
generate_videos: false                   # Generate video prompts
retry_errors: false                      # Retry failed slides

# Style definition
style:
  visual_style: |
    Your detailed visual style description here.
    Include colors, typography, layout, mood, etc.
    
  speaker_style: |
    Your detailed speaker persona description here.
    Include tone, vocabulary, personality, examples, etc.
```

## Benefits of Migration

### ✅ Simplified Usage
- **Before**: `./run.sh --folder notes --language en,zh-CN --style Cyberpunk --output-dir output --generate-videos`
- **After**: `python main.py --style-config cyberpunk`

### ✅ Consistent Configuration
- All settings in version-controlled YAML files
- No configuration drift between team members
- Complex style definitions possible

### ✅ Clear Modes
- Three distinct modes for different use cases
- No confusion about which options to use
- Predictable behavior

### ✅ Team Collaboration
- Shared YAML configurations
- Easy to review and modify styles
- Consistent results across team

## Troubleshooting Migration

### Common Issues

#### "No configuration file found"
```bash
# Error: No configuration file found for style: mystyle
```
**Solution**: Create `styles/config.mystyle.yaml` or use existing style name

#### "Configuration must specify 'input_folder'"
```bash
# Error: Configuration file must specify 'input_folder'
```
**Solution**: Add `input_folder: "path/to/files"` to your YAML config

#### "No PPTX/PDF pairs found"
```bash
# Warning: No PPTX/PDF pairs found in input folder: notes
```
**Solution**: Check that your `input_folder` path is correct and contains matching PPTX/PDF files

### Validation Steps

1. **Check your YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('styles/config.mystyle.yaml'))"
   ```

2. **Verify file structure**:
   ```bash
   ls styles/config.*.yaml  # Should show your config files
   ls notes/*.pptx          # Should show your input files
   ```

3. **Test with single style**:
   ```bash
   python main.py --style-config professional  # Test with known working style
   ```

## Getting Help

If you encounter issues during migration:

1. Check the [FINAL_SYSTEM_SUMMARY.md](FINAL_SYSTEM_SUMMARY.md) for complete system overview
2. Review [examples/usage_examples.py](examples/usage_examples.py) for working examples
3. Look at existing YAML configs in `styles/config.*.yaml` for reference
4. Use single file mode for testing: `python main.py --pptx test.pptx --language en --style Professional`

The new system is much simpler once you have your YAML configurations set up!