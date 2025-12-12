# Language Enforcement Strengthening Fix

## Issue Identified

After fixing the prompt rewriter Content object bug, the HK Comic style is now working, but there's a **language enforcement issue**:

- **Configuration**: English processing (`_en_progress.json`)
- **Expected**: English speaker notes with martial arts master style
- **Actual**: Chinese speaker notes with martial arts master style

Example from logs:
```json
"slide_12_2b2d0ca0": {
  "slide_index": 12,
  "original_notes": "Building on our discussion of how MFA helps ensure *confidentiality*...", // English
  "note": "諸位武林同道，方才吾等論及鞏固據點之法，守護內功心法之門戶...", // Chinese!
  "status": "success"
}
```

## Root Cause Analysis

### The Problem
The HK Comic speaker style contains **extensive Chinese examples** (5,728 chars) that overwhelm the language enforcement:

```yaml
speaker_style: |
  LANGUAGE OVERRIDE: Always write speaker notes in the target language specified by the user.
  If English is requested, write 100% in English. If Chinese is requested, write 100% in Chinese.
  Do not mix languages regardless of the examples below.
  
  角色扮演指令：你是一位江湖大俠/武林宗師 (ROLEPLAY: You are a Martial Arts Master)
  
  **開場語 (Opening Phrases):**
  - "各位武林同道，請聽我一言..."
  - "今日召集眾位，實有要事相商"
  - "江湖風雲變幻，吾等當如何應對？"
  # ... hundreds more lines of Chinese examples
```

### Why Language Enforcement Failed
1. **Weak Override**: The "LANGUAGE OVERRIDE" instruction at the top was too weak
2. **Overwhelming Examples**: 5,728 chars of Chinese examples vs. small language instruction
3. **LLM Bias**: The model was influenced by the dominant Chinese content
4. **Fallback Method**: The original fallback language enforcement wasn't strong enough

## Solution Implemented

### Reordered and Strengthened Language Enforcement
The key insight was that the fallback method was structured incorrectly:

```python
# PROBLEMATIC ORDER - Language enforcement came AFTER Chinese examples
{base_prompt}
{self.speaker_style}  # ← 5,728 chars of Chinese examples influence LLM first
LANGUAGE ENFORCEMENT  # ← Too late, LLM already influenced

# FIXED ORDER - Language enforcement comes FIRST
{base_prompt}
🚨 ABSOLUTE LANGUAGE ENFORCEMENT 🚨  # ← LLM sees this first
{self.speaker_style}  # ← Now clearly labeled as "reference to translate"
```

Updated the fallback method in `services/prompt_rewriter.py` with:

```python
# OLD - Weak language enforcement
🌍 LANGUAGE PRIORITY RULES:
1. The target language specified in the user request ALWAYS takes precedence
2. If English is requested, write 100% in English regardless of style examples
# ... basic rules

# NEW - Absolute language enforcement
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚨 ABSOLUTE LANGUAGE ENFORCEMENT 🚨                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔴 ABSOLUTE PRIORITY: The target language specified by the user OVERRIDES EVERYTHING
🔴 IGNORE ALL LANGUAGE EXAMPLES in the style above - they are for reference only
🔴 If English is requested → Write 100% in English, translate all style concepts
🔴 NEVER mix languages - use ONLY the requested target language

⚠️  CRITICAL INSTRUCTION: Even though the style above contains Chinese examples,
    you MUST translate the style concepts to the target language.
    The Chinese text is for understanding the style, NOT for copying directly.

🎯 LANGUAGE ENFORCEMENT EXAMPLES:
    - Style says "各位武林同道" → If English requested → "Fellow martial artists"
    - Style says "此乃絕世武功" → If English requested → "This is an ultimate technique"
    - Style says "江湖風雲變幻" → If English requested → "The martial world is changing"

🚨 FINAL WARNING: Language compliance is MORE IMPORTANT than style accuracy.
    Better to have correct language with approximate style than wrong language.
```

### Key Improvements
1. **Visual Emphasis**: Used emojis and visual separators to make language enforcement stand out
2. **Explicit Instructions**: Clearly stated that Chinese examples are for reference only
3. **Translation Examples**: Showed how to translate style concepts to target language
4. **Priority Declaration**: Made it clear that language compliance overrides style accuracy
5. **Stronger Warning**: Emphasized that wrong language is worse than imperfect style

## Expected Results

After this fix, when running `./run.sh --style-config hkcomic` for English:

### Before Fix
```
"諸位武林同道，方才吾等論及鞏固據點之法，守護內功心法之門戶..."
```
*(Chinese martial arts master style - wrong language)*

### After Fix
```
"Fellow martial artists, we have just discussed the methods of fortifying our strongholds 
and protecting the gateways to our internal cultivation techniques..."
```
*(English martial arts master style - correct language with style)*

## Technical Details

### Current Status
- ✅ **Prompt rewriter Content object bug fixed**
- ✅ **HK Comic style is working** (martial arts master tone)
- ✅ **Fallback method is being used** (LLM rewriting still failing)
- ⚠️ **Language enforcement strengthened** (needs testing)

### Next Steps
1. **Test the strengthened language enforcement**
2. **Investigate why LLM-based rewriting is still failing**
3. **Consider simplifying the HK Comic style** to reduce Chinese content dominance
4. **Add language validation** in the auditor agent

## Files Modified
- `services/prompt_rewriter.py` - Strengthened language enforcement in `_fallback_writer_rewrite()`

## Related Issues
This same issue likely affects:
- Other styles with non-English examples
- Any style configuration with dominant foreign language content
- Multi-language processing where style examples conflict with target language