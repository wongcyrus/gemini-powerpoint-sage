# Run All Styles - Batch Processing

Process a presentation with all available style configurations automatically.

## Overview

The `run_all_styles` scripts process a single presentation through all style configurations found in the `styles/` directory. This is useful for:

- Comparing different styles side-by-side
- Generating multiple style variants at once
- Testing style configurations
- Creating a style showcase

## Available Scripts

All scripts automatically activate the virtual environment (`.venv`) if it exists.

**Important Notes:**
- PPTX and PDF file paths are read from each YAML config file
- Language parameter is optional (defaults to `en` if not specified)
- All output filenames include the language code (e.g., `presentation_en_notes.pptx`)

### Bash (Linux/macOS)
```bash
./run_all_styles.sh [language]
```

### Python (Cross-platform)
```bash
python run_all_styles.py [language]
```

### PowerShell (Windows)
```powershell
.\run_all_styles.ps1 [language]
```

## Usage Examples

### Basic Usage (English - Default)
```bash
# Bash/Linux/macOS (defaults to en)
./run_all_styles.sh

# Or explicitly specify English
./run_all_styles.sh en

# Python (any platform, defaults to en)
python run_all_styles.py

# PowerShell/Windows (defaults to en)
.\run_all_styles.ps1
```

**Note:** If no language is specified, defaults to `en` (English).

### With Other Languages
```bash
# Chinese
./run_all_styles.sh zh-CN

# Japanese
python run_all_styles.py ja

# Cantonese
.\run_all_styles.ps1 yue-HK
```

**Note:** Process one language at a time. For multiple languages, run the script multiple times.

## What It Does

1. **Discovers Styles**: Finds all `config.*.yaml` files in `styles/` directory
2. **Validates Input**: Checks that PPTX and PDF files exist
3. **Processes Each Style**: Runs `main.py` with each style configuration
4. **Tracks Results**: Reports success/failure for each style
5. **Displays Summary**: Shows final statistics and output locations

## Output Structure

Each style creates its own **self-contained** output directory with all files including progress JSON:

```
project/
├── presentation.pptx
├── presentation.pdf
├── cyberpunk/
│   └── generate/
│       ├── presentation_en_notes.pptx
│       ├── presentation_en_visuals.pptx
│       ├── presentation_en_progress.json
│       └── presentation_en_visuals/
├── gundam/
│   └── generate/
│       ├── presentation_en_notes.pptx
│       ├── presentation_en_visuals.pptx
│       ├── presentation_en_progress.json
│       └── presentation_en_visuals/
├── star_wars/
│   └── generate/
│       ├── presentation_en_notes.pptx
│       ├── presentation_en_visuals.pptx
│       ├── presentation_en_progress.json
│       └── presentation_en_visuals/
└── professional/
    └── generate/
        ├── presentation_en_notes.pptx
        ├── presentation_en_visuals.pptx
        ├── presentation_en_progress.json
        └── presentation_en_visuals/
```

**Each folder is self-contained** with:
- Generated PPTX files (notes and visuals)
- Progress JSON for resume capability
- Visual assets directory
- Video prompts (if generated)

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║          Running All Style Configurations                 ║
╚════════════════════════════════════════════════════════════╝

Input Files:
  PPTX: presentation.pptx
  PDF:  presentation.pdf
  Language: en

Found 4 style configuration(s):
  - cyberpunk
  - gundam
  - professional
  - star_wars

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing Style: cyberpunk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Processing output...]

✓ Successfully processed: cyberpunk

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing Style: gundam
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Processing output...]

✓ Successfully processed: gundam

[... continues for all styles ...]

╔════════════════════════════════════════════════════════════╗
║                    Processing Summary                      ║
╚════════════════════════════════════════════════════════════╝

Successful: 4
Failed: 0

🎉 All styles processed successfully!

Output locations:
  - cyberpunk/generate/
  - gundam/generate/
  - professional/generate/
  - star_wars/generate/
```

## Error Handling

If a style fails to process:

```
✗ Failed to process: cyberpunk
Error: [error message]

╔════════════════════════════════════════════════════════════╗
║                    Processing Summary                      ║
╚════════════════════════════════════════════════════════════╝

Successful: 3
Failed: 1

Failed styles:
  - cyberpunk
```

The script will:
- Continue processing remaining styles
- Report which styles failed
- Exit with error code 1

## Adding New Styles

To add a new style to the batch processing:

1. Create a new config file: `styles/config.mystyle.yaml`
2. Include `output_dir: "mystyle/generate"`
3. Run the script - it will automatically discover and process the new style

Example:
```yaml
# styles/config.mystyle.yaml
pptx: "presentation.pptx"
pdf: "presentation.pdf"
output_dir: "mystyle/generate"
style: "My Custom Style"
language: "en"
```

## Performance Considerations

### Sequential Processing
The scripts process styles **sequentially** (one at a time):
- Easier to debug
- Clear progress tracking
- Prevents resource contention

### Time Estimates
Processing time depends on:
- Number of slides
- Number of styles
- Whether visuals are generated
- Language processing

**Example:** 20-slide presentation with 4 styles:
- Notes only: ~10-15 minutes per style = 40-60 minutes total
- With visuals: ~20-30 minutes per style = 80-120 minutes total

### Optimization Tips

1. **Skip Visuals for Testing**
   ```yaml
   skip_visuals: true  # In config files
   ```

2. **Process English First**
   ```bash
   # English first (fastest)
   ./run_all_styles.sh deck.pptx deck.pdf en
   
   # Then other languages (uses translation mode)
   ./run_all_styles.sh deck.pptx deck.pdf zh-CN
   ```

3. **Use Specific Styles**
   ```bash
   # Instead of all styles, run specific ones:
   python main.py --config styles/config.cyberpunk.yaml --pptx deck.pptx --pdf deck.pdf
   python main.py --config styles/config.gundam.yaml --pptx deck.pptx --pdf deck.pdf
   ```

## Troubleshooting

### Script Not Found
```bash
# Make scripts executable (Linux/macOS)
chmod +x run_all_styles.sh
chmod +x run_all_styles.py

# Or run with interpreter
bash run_all_styles.sh presentation.pptx presentation.pdf
python run_all_styles.py presentation.pptx presentation.pdf
```

### No Styles Found
```
Error: No style configuration files found in styles/
```

**Solution:** Ensure you have `config.*.yaml` files in the `styles/` directory.

### Permission Denied (PowerShell)
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run
.\run_all_styles.ps1 presentation.pptx presentation.pdf
```

### Python Import Errors
```bash
# Ensure you're in the project root directory
cd /path/to/gemini-powerpoint-sage

# Activate virtual environment if using one
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Run script
python run_all_styles.py presentation.pptx presentation.pdf
```

## Advanced Usage

### Custom Style Selection

To process only specific styles, temporarily move unwanted configs:

```bash
# Create a backup directory
mkdir styles/backup

# Move configs you don't want to process
mv styles/config.professional.yaml styles/backup/

# Run script (will only process remaining configs)
./run_all_styles.sh presentation.pptx presentation.pdf

# Restore configs
mv styles/backup/*.yaml styles/
```

### Parallel Processing (Advanced)

For faster processing, you can run styles in parallel manually:

```bash
# Run each style in background
python main.py --config styles/config.cyberpunk.yaml --pptx deck.pptx --pdf deck.pdf &
python main.py --config styles/config.gundam.yaml --pptx deck.pptx --pdf deck.pdf &
python main.py --config styles/config.starwars.yaml --pptx deck.pptx --pdf deck.pdf &

# Wait for all to complete
wait
```

**Warning:** This may cause resource contention and API rate limits.

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Generate All Styles

on:
  push:
    paths:
      - 'presentations/*.pptx'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Process all styles
        run: |
          python run_all_styles.py \
            presentations/deck.pptx \
            presentations/deck.pdf
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: styled-presentations
          path: |
            cyberpunk/generate/
            gundam/generate/
            star_wars/generate/
```

## See Also

- [Style Configuration Guide](STYLE_CONFIGS.md)
- [Output Organization](OUTPUT_ORGANIZATION.md)
- [YAML Configuration](../styles/README.md)
- [Main Documentation](../README.md)
