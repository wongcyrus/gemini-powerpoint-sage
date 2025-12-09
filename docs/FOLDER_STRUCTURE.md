# Folder Structure Guide

## Overview

The Gemini PowerPoint Sage organizes outputs by file and language locale with **English as the required baseline** for translation workflows.

## Multi-Language Workflow

### Processing Order
1. **English (en) - REQUIRED FIRST**: Always processed from scratch to create baseline
2. **Other Languages**: Translated from English notes for consistency and speed

### Translation Mode Benefits
- **Faster**: Translation is quicker than full generation
- **Consistent**: All languages based on same English baseline
- **Cost-effective**: Reduces API calls for subsequent languages
- **Quality**: English serves as reviewed baseline

## Naming Convention

### All Languages (Including English)
All output files include the language suffix for consistency:
```
{filename}_{locale}_with_notes.pptx
{filename}_{locale}_with_visuals.pptx
{filename}_{locale}_progress.json
{filename}_{locale}_visuals/
```

### Examples
- English: `lecture_en_with_notes.pptx`, `lecture_en_progress.json`, `lecture_en_visuals/`
- Simplified Chinese: `lecture_zh-CN_with_notes.pptx`, `lecture_zh-CN_progress.json`, `lecture_zh-CN_visuals/`
- Cantonese: `lecture_yue-HK_with_notes.pptx`, `lecture_yue-HK_progress.json`, `lecture_yue-HK_visuals/`

## Example: Single File, Multiple Languages

Starting with:
```
presentations/
├── lecture.pptx
└── lecture.pdf
```

After processing with: `.\run.ps1 --pptx lecture.pptx --language "en,zh-CN,yue-HK"`

```
presentations/
├── lecture.pptx                              # Original source
├── lecture.pdf                               # Original PDF
│
├── lecture_en_with_notes.pptx                # English baseline (generated)
├── lecture_en_with_visuals.pptx
├── lecture_en_progress.json                  # ✓ Self-contained progress
├── lecture_en_visuals/
│   ├── slide_1_reimagined.png
│   ├── slide_2_reimagined.png
│   └── slide_3_reimagined.png
│
├── lecture_zh-CN_with_notes.pptx             # Simplified Chinese (translated from EN)
├── lecture_zh-CN_with_visuals.pptx
├── lecture_zh-CN_progress.json               # ✓ Self-contained progress
├── lecture_zh-CN_visuals/
│   ├── slide_1_reimagined.png                # Copied from English
│   ├── slide_2_reimagined.png
│   └── slide_3_reimagined.png
│
├── lecture_yue-HK_with_notes.pptx            # Cantonese (translated from EN)
├── lecture_yue-HK_with_visuals.pptx
├── lecture_yue-HK_progress.json              # ✓ Self-contained progress
└── lecture_yue-HK_visuals/
    ├── slide_1_reimagined.png                # Copied from English
    ├── slide_2_reimagined.png
    └── slide_3_reimagined.png
```

**Note:** Each language variant is self-contained with its own progress JSON file, making it easy to move, share, or archive individual language versions.

## Example: Multiple Files in Folder Mode

Starting with:
```
presentations/
├── module1.pptx
├── module1.pdf
├── module2.pptx
└── module2.pdf
```

After running: `.\run.ps1 --folder presentations --language zh-CN`

```
presentations/
├── module1.pptx
├── module1.pdf
├── module1_zh-CN_with_notes.pptx
├── module1_zh-CN_with_visuals.pptx
├── module1_zh-CN_progress.json               # ✓ Self-contained
├── module1_zh-CN_visuals/
│   ├── slide_1_reimagined.png
│   └── slide_2_reimagined.png
│
├── module2.pptx
├── module2.pdf
├── module2_zh-CN_with_notes.pptx
├── module2_zh-CN_with_visuals.pptx
├── module2_zh-CN_progress.json               # ✓ Self-contained
└── module2_zh-CN_visuals/
    ├── slide_1_reimagined.png
    └── slide_2_reimagined.png
```

**Each file's output is self-contained** with its own progress tracking, making batch processing results easy to manage.

## Common Locale Codes

| Locale | Language | Example Filename |
|--------|----------|------------------|
| `en` | English (baseline) | `lecture_en_with_notes.pptx` |
| `zh-CN` | Simplified Chinese | `lecture_zh-CN_with_notes.pptx` |
| `zh-TW` | Traditional Chinese | `lecture_zh-TW_with_notes.pptx` |
| `yue-HK` | Cantonese | `lecture_yue-HK_with_notes.pptx` |
| `es` | Spanish | `lecture_es_with_notes.pptx` |
| `fr` | French | `lecture_fr_with_notes.pptx` |
| `ja` | Japanese | `lecture_ja_with_notes.pptx` |
| `ko` | Korean | `lecture_ko_with_notes.pptx` |
| `de` | German | `lecture_de_with_notes.pptx` |
| `pt` | Portuguese | `lecture_pt_with_notes.pptx` |

## Benefits of This Structure

1. **Self-Contained**: Each output includes progress JSON - move/share folders independently
2. **No Conflicts**: Process the same presentation in multiple languages without overwriting files
3. **Clean Organization**: Easy to identify which language version you're working with
4. **Isolated Progress**: Each language maintains its own progress tracking
5. **Parallel Processing**: Can process different languages simultaneously
6. **Easy Cleanup**: Delete all files for a specific language using wildcard patterns
7. **Version Control Friendly**: Clear file naming makes it easy to track changes
8. **Portable**: Archive or distribute complete outputs with progress data intact

## Commands for Common Workflows

### Process one file in multiple languages (recommended)
```powershell
# English + Simplified Chinese + Cantonese
.\run.ps1 --pptx "lecture.pptx" --language "en,zh-CN,yue-HK"
```

### Process one language at a time
```powershell
# English first (required for translations)
.\run.ps1 --pptx "lecture.pptx" --language en

# Then other languages (will translate from English)
.\run.ps1 --pptx "lecture.pptx" --language zh-CN
.\run.ps1 --pptx "lecture.pptx" --language yue-HK
```

### Process entire folder in multiple languages
```powershell
.\run.ps1 --folder "presentations" --language "en,zh-CN,yue-HK"
```

### Clean up specific language outputs
```powershell
# Windows PowerShell
Remove-Item "presentations\*_zh-CN_*" -Recurse

# Linux/macOS
rm -rf presentations/*_zh-CN_*
```

## Progress File Structure

Each language version maintains its own progress file to track which slides have been processed:

**`lecture_en_progress.json`** (English baseline)
```json
{
  "slides": {
    "slide_1_a1b2c3d4": {
      "slide_index": 1,
      "existing_notes_hash": "a1b2c3d4",
      "original_notes": "Introduction to security",
      "note": "Welcome everyone. Today we'll explore...",
      "status": "success"
    }
  },
  "global_context": "This presentation covers..."
}
```

**`lecture_zh-CN_progress.json`** (Translated from English)
```json
{
  "slides": {
    "slide_1_a1b2c3d4": {
      "slide_index": 1,
      "existing_notes_hash": "a1b2c3d4",
      "original_notes": "Introduction to security",
      "note": "欢迎大家。今天我们将探讨...",
      "status": "success"
    }
  },
  "global_context": "本演示文稿涵盖..."
}
```

This allows you to:
- Resume interrupted processing for specific languages
- Regenerate only failed slides per language
- Track progress independently for each language version
- Use English as baseline for retranslation if needed
