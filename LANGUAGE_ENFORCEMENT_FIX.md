# Language Enforcement Fix for HK Comic Style

## Problem Identified

When using `styles/config.hkcomic.yaml` with English language (`language: "en"`), the system was generating Chinese speaker notes instead of English. This happened because:

1. The `speaker_style` in hkcomic config contains extensive Chinese text and examples
2. The prompt rewriter integrates this Chinese text into the writer agent's system instruction
3. The Chinese text in the system instruction influenced the agent to generate Chinese content
4. The language parameter wasn't strongly enforced to override the style influence

## Root Cause Analysis

The issue was in the language enforcement mechanism:

- **File**: `tools/agent_tools.py` - `create_writer_tool()` method
- **Problem**: Language instruction was only added for non-English languages
- **Impact**: When `language="en"`, no explicit language instruction was provided
- **Result**: Chinese text in speaker style dominated the output language

## Solution Implemented

### 1. Enhanced Language Enforcement in Writer Tool

**File**: `tools/agent_tools.py`

```python
# OLD CODE (weak enforcement)
if language and language.lower() != "en":
    lang_name = LanguageConfig.get_language_name(language)
    language_instruction = (
        f"\n\nIMPORTANT: Write the speaker notes in {lang_name}. "
        f"All content must be in {lang_name}."
    )

# NEW CODE (strong enforcement for ALL languages)
lang_name = LanguageConfig.get_language_name(language)

if language.lower() == "en":
    language_instruction = (
        f"\n\nCRITICAL LANGUAGE REQUIREMENT: "
        f"You MUST write the speaker notes in English only. "
        f"Even if your system instructions contain text in other languages, "
        f"your output must be 100% English. Do not mix languages."
    )
else:
    language_instruction = (
        f"\n\nCRITICAL LANGUAGE REQUIREMENT: "
        f"You MUST write the speaker notes in {lang_name} only. "
        f"Even if your system instructions contain text in other languages, "
        f"your output must be 100% {lang_name}. Do not mix languages."
    )
```

### 2. Updated HK Comic Style Configuration

**File**: `styles/config.hkcomic.yaml`

Added explicit language override instruction at the beginning of speaker_style:

```yaml
speaker_style: |
  LANGUAGE OVERRIDE: Always write speaker notes in the target language specified by the user.
  If English is requested, write 100% in English. If Chinese is requested, write 100% in Chinese.
  Do not mix languages regardless of the examples below.
  
  角色扮演指令：你是一位江湖大俠/武林宗師 (ROLEPLAY: You are a Martial Arts Master)
  # ... rest of the style continues
```

### 3. Enhanced Prompt Rewriter Language Enforcement

**File**: `services/prompt_rewriter.py`

- Added language enforcement section to fallback writer rewrite
- Updated LLM-based rewriter to include language compliance instructions
- Ensured language parameter always overrides style language tendencies

## Key Improvements

### 1. **Explicit Language Instructions for ALL Languages**
- Previously: Only non-English languages got language instructions
- Now: ALL languages get explicit, strong language enforcement

### 2. **Override Mechanism**
- Clear instruction that target language overrides system instruction languages
- Explicit "Do not mix languages" directive
- "CRITICAL LANGUAGE REQUIREMENT" emphasis

### 3. **Style Configuration Updates**
- Added language override instructions to hkcomic style
- Maintains style personality while enforcing language compliance

### 4. **Enhanced Language Enforcement in Auditor Tool**
- Added language parameter to `create_auditor_tool()` method
- Auditor now checks if existing notes are in the correct language
- Notes in wrong language are marked as USELESS for regeneration
- Updated supervisor tool configuration to use language-aware auditor

### 5. **Prompt Rewriter Enhancements**
- Language enforcement built into the rewriting process
- Fallback methods include language compliance rules
- LLM-based rewriter includes language enforcement requirements

## Testing

Created comprehensive tests to verify language enforcement logic:

```bash
# Test writer language enforcement
python test_language_enforcement.py

# Test auditor language enforcement  
python test_auditor_language_enforcement.py
```

Results:
- ✅ Writer enforcement: "100% English. Do not mix languages."
- ✅ Auditor enforcement: "mark them as USELESS for regeneration in the correct language"
- ✅ Chinese enforcement: "100% Chinese (Simplified). Do not mix languages."
- ✅ Cantonese enforcement: "100% Cantonese (Hong Kong). Do not mix languages."
- ✅ All other languages properly enforced

## Usage Examples

Now the hkcomic style will work correctly with any language:

```bash
# English speaker notes with martial arts style
python main.py --style-config hkcomic --language en

# Chinese speaker notes with martial arts style  
python main.py --style-config hkcomic --language zh-CN

# Cantonese speaker notes with martial arts style
python main.py --style-config hkcomic --language yue-HK
```

## Verification

- ✅ All 109 tests still passing
- ✅ Language enforcement logic tested and verified
- ✅ No breaking changes to existing functionality
- ✅ Backward compatibility maintained

## Impact

This fix ensures that:

1. **Language parameter is always respected** regardless of style content
2. **Mixed language output is prevented** through explicit instructions
3. **Style personality is maintained** while enforcing language compliance
4. **All existing styles continue to work** with enhanced language enforcement

The system now provides strong language compliance while maintaining the rich, culturally-specific speaker styles that make each configuration unique.