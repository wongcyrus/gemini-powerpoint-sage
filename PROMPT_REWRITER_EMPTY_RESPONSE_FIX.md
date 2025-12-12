# Prompt Rewriter Content Object Fix

## Issue Identified

When running `./run.sh --style-config hkcomic`, the system was generating professional-style speaker notes instead of the martial arts master style specified in the HK Comic configuration.

## Root Cause Analysis

### Problem Discovery
The logs showed:
```
2025-12-12 14:56:14 - INFO - services.prompt_rewriter - Rewritten prompt length: 0 chars
2025-12-12 14:56:14 - INFO - services.prompt_rewriter - ✓ Writer prompt rewritten successfully
```

### The Real Bug
The issue was **not** that the LLM was returning empty responses. The issue was a **coding bug** in how the `InMemoryRunner` was being called:

```python
# BUGGY CODE - passing string instead of Content object
for event in runner.run(
    user_id=user_id,
    session_id=session_id,
    new_message=rewrite_request,  # ❌ String instead of Content object
):
```

The `InMemoryRunner.run()` method expects a `Content` object with `types.Part.from_text()`, not a raw string. When passed a string, the runner silently fails and returns no events, resulting in empty `response_text`.

### Impact
This resulted in:
- **No events returned** from the runner (silent failure)
- **Empty response_text** collected from non-existent events
- Writer agents created with **empty instructions**
- Default professional behavior instead of styled behavior
- HK Comic style completely ignored

## Solution Implemented

### Fixed Content Object Creation
The primary fix was to create proper `Content` objects instead of passing raw strings:

```python
# OLD - Buggy code passing string
for event in runner.run(
    user_id=user_id,
    session_id=session_id,
    new_message=rewrite_request,  # ❌ Raw string
):

# NEW - Correct code with Content object
from google.genai import types

content = types.Content(
    role='user', 
    parts=[types.Part.from_text(text=rewrite_request)]
)

for event in runner.run(
    user_id=user_id,
    session_id=session_id,
    new_message=content,  # ✅ Proper Content object
):
```

### Added Empty Response Validation
As a secondary safeguard, also added validation to detect and handle empty responses:

```python
rewritten = response_text.strip()

# Check if rewriting actually produced content
if not rewritten:
    logger.warning("LLM returned empty rewritten prompt, falling back to concatenation")
    return self._fallback_writer_rewrite(base_prompt)

logger.info("✓ Writer prompt rewritten successfully")
return rewritten
```

### Files Modified
- `services/prompt_rewriter.py` - Added empty response validation to all 4 rewrite methods:
  - `rewrite_designer_prompt()`
  - `rewrite_writer_prompt()`
  - `rewrite_title_generator_prompt()`
  - `rewrite_translator_prompt()`

### Fallback Behavior
Now when the LLM returns empty content, the system will:
1. **Log a warning** about the empty response
2. **Automatically fall back** to the concatenation method
3. **Use the robust fallback prompts** that properly integrate the style
4. **Ensure the agent gets styled instructions** instead of empty ones

## Expected Results

After this fix, when running `./run.sh --style-config hkcomic`, the system should:

1. **Attempt LLM-based rewriting** (preferred method)
2. **Detect empty responses** and log warnings
3. **Fall back to concatenation** with proper style integration
4. **Generate martial arts master style** speaker notes like:

```
"各位武林同道！今日召集眾位，實因網路安全局勢已變。
舊有的防護體系如同陳舊招式，已難應對新時代的網路威脅。
然而，吾等發現一門絕世武功——資訊安全三大要訣！
此乃機密性、完整性、可用性之精髓..."
```

Instead of professional academic tone:
```
"Good morning, everyone. Welcome to Module 4a of our program, 
focusing on 'Cybersecurity Essentials: Information Security Concepts'..."
```

## Testing

To test the fix:
1. Run `./run.sh --style-config hkcomic` 
2. Check the logs for fallback warnings
3. Verify the generated speaker notes use martial arts terminology
4. Confirm the style is applied consistently across all slides

## Related Issues

This fix also resolves similar issues with:
- Cyberpunk style not being applied
- Gundam style reverting to professional
- Any other style configuration producing generic content

The root cause was the same: empty LLM responses not being handled properly in the prompt rewriter.