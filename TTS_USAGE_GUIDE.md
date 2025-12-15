# TTS System Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: Gemini TTS requires `google-cloud-texttospeech>=2.29.0`

### 2. Set Up Google Cloud Authentication
```bash
# Set up service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"

# Optional: Configure TTS settings
export TTS_ENABLED="true"
export TTS_CACHE_ENABLED="true"
export TTS_STORAGE_BUCKET="your-gcs-bucket-name"
```

### 3. Test TTS System
```bash
# Test if TTS engines are working
python run_tts.py --test
```

## Usage Options

### Option 1: Simple TTS Script (Recommended)
```bash
# Generate TTS for existing presentation
python run_tts.py presentation_progress.json --language en-US

# Test TTS engines
python run_tts.py --test

# Get system statistics
python run_tts.py --stats

# Clean up old cache files
python run_tts.py --cleanup --max-age 7
```

### Option 2: TTS CLI Utility
```bash
# Generate TTS
python -m utils.tts_cli_utils generate presentation_progress.json --language en-US

# Test engines
python -m utils.tts_cli_utils test

# Get stats
python -m utils.tts_cli_utils stats

# Cleanup
python -m utils.tts_cli_utils cleanup --max-age 7
```

### Option 3: Main CLI with TTS-Only Mode
```bash
# Generate only TTS (skip notes/visuals)
python -m application.cli --tts-only --pptx presentation_progress.json --language en-US
```

### Option 4: Integrated with Full Processing
```bash
# Full processing with TTS enabled
python -m application.cli --pptx presentation.pptx --pdf presentation.pdf --language en-US
```

## Workflow Examples

### Complete Workflow
```bash
# Step 1: Generate speaker notes first
python -m application.cli --pptx presentation.pptx --pdf presentation.pdf --language en-US

# Step 2: Generate TTS from the progress file
python run_tts.py output/presentation_en_progress.json --language en-US
```

### TTS-Only Workflow
```bash
# If you already have speaker notes and just want TTS
python run_tts.py existing_progress.json --language ja-JP
```

### Multi-Language TTS
```bash
# Generate TTS for multiple languages
python run_tts.py presentation_en_progress.json --language en-US
python run_tts.py presentation_zh_progress.json --language zh-CN
python run_tts.py presentation_yue_progress.json --language yue-HK
```

## Configuration

### Environment Variables
```bash
# Enable/disable TTS
export TTS_ENABLED="true"

# Cache settings
export TTS_CACHE_ENABLED="true"
export TTS_CACHE_TTL_HOURS="24"

# Storage settings
export TTS_STORAGE_BUCKET="your-bucket-name"

# Processing settings
export TTS_PARALLEL_PROCESSING="true"
export TTS_MAX_CONCURRENT_SLIDES="3"

# Engine-specific concurrency (recommended for stability)
export TTS_GEMINI_MAX_CONCURRENT="1"        # Gemini TTS is unstable with multi-threading
export TTS_TRADITIONAL_MAX_CONCURRENT="3"   # Traditional TTS can handle more concurrency
```

### Supported Languages

#### Gemini TTS (Advanced, with style prompts)
- English US (en-US)
- English India (en-IN)
- Japanese (ja-JP)
- Korean (ko-KR)
- French (fr-FR)
- German (de-DE)
- Spanish (es-ES)
- Italian (it-IT)
- Portuguese Brazil (pt-BR)
- Russian (ru-RU)
- Hindi (hi-IN)
- Arabic Egypt (ar-EG)
- Dutch (nl-NL)
- Polish (pl-PL)
- Romanian (ro-RO)
- Bengali Bangladesh (bn-BD)
- Indonesian (id-ID)
- Marathi India (mr-IN)
- Tamil India (ta-IN)

#### Traditional TTS (Fallback & Primary)
- **Primary**: Chinese languages that require Traditional TTS
  - Chinese Simplified (zh-CN → cmn-CN)
  - Chinese Traditional (zh-TW → cmn-TW)
  - Chinese Hong Kong (zh-HK → yue-HK)
  - Cantonese (yue-HK)
- **Fallback**: When Gemini TTS fails
  - English (en-US) using Chirp 3: HD voices
  - Any other language not supported by Gemini TTS

## Output Structure

TTS generates organized audio files:
```
output/
├── presentation_en_speech/
│   ├── slide_1_a1b2c3d4.mp3
│   ├── slide_2_e5f6g7h8.mp3
│   └── ...
├── presentation_zh_speech/
│   ├── slide_1_i9j0k1l2.mp3
│   └── ...
└── cache/
    ├── tts/
    └── speech/
```

## Troubleshooting

### Common Issues

1. **"TTS system is disabled"**
   ```bash
   export TTS_ENABLED="true"
   ```

2. **"Missing Google Cloud credentials"**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   ```

3. **"No slides found for TTS generation"**
   - Make sure you're using a progress JSON file with successful speaker notes
   - Run the main processing first to generate notes

4. **"Traditional TTS failed"**
   - Check Google Cloud TTS API is enabled
   - Verify service account has TTS permissions

5. **"Either `input.text` or `input.prompt` is longer than the limit of 4000 bytes"**
   - This happens when TTS prompts are too long
   - The system automatically creates concise prompts to stay under limits
   - If you see this error, the system will fallback to Traditional TTS

### Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from utils.tts_cli_utils import TTSCLIUtility
asyncio.run(TTSCLIUtility().test_tts_engines())
"
```

## Performance Tips

1. **Use Caching**: Keep `TTS_CACHE_ENABLED="true"` to avoid regenerating identical content
2. **Engine-Specific Concurrency**: 
   - Keep `TTS_GEMINI_MAX_CONCURRENT="1"` for stability (Gemini TTS is unstable with multi-threading)
   - Adjust `TTS_TRADITIONAL_MAX_CONCURRENT` based on your system (default: 3)
3. **Cleanup Regularly**: Run cleanup to manage disk space
4. **Batch Processing**: Process multiple slides at once for better efficiency

## Integration with Existing Workflow

The TTS system integrates seamlessly with the existing presentation processing:

1. **Automatic Integration**: TTS runs automatically after notes generation when enabled
2. **Progress File Updates**: TTS results are saved in the progress JSON files
3. **Graceful Degradation**: If TTS fails, the system continues with notes and visuals
4. **Cache Sharing**: Multiple presentations can share cached audio files