# Prompt Rewriter Fix

## Issues Encountered
The prompt rewriter service was failing with two sequential errors:

1. **First Error:**
```
Runner.__init__() missing 1 required keyword-only argument: 'session_service'
```

2. **Second Error (after initial fix):**
```
Runner.run() takes 1 positional argument but 2 were given
```

Both errors were causing the system to fall back to simple concatenation instead of using LLM-powered prompt rewriting.

## Root Causes
1. The `services/prompt_rewriter.py` file was importing `Runner` instead of `InMemoryRunner`
2. The code was not providing the required `app_name` parameter for `InMemoryRunner`
3. The `run()` method was being called incorrectly - it expects keyword arguments, not a direct message string

## Fix Applied

### 1. Updated Import
**Before:**
```python
from google.adk.runners import Runner
```

**After:**
```python
from google.adk.runners import InMemoryRunner
```

### 2. Updated Runner Initialization and Usage
**Before:**
```python
runner = Runner(agent=self.rewriter_agent)
result = runner.run(rewrite_request)
rewritten = result.text.strip()
```

**After:**
```python
runner = InMemoryRunner(agent=self.rewriter_agent, app_name="agents")

# Create session for the runner
user_id = "prompt_rewriter_user"
session_id = "designer_rewriter_session"

# Run the agent and collect response
response_text = ""
for event in runner.run(
    user_id=user_id,
    session_id=session_id,
    new_message=rewrite_request,
):
    if getattr(event, "content", None) and event.content.parts:
        for part in event.content.parts:
            txt = getattr(part, "text", "") or ""
            response_text += txt

rewritten = response_text.strip()
```

### 3. Updated Documentation
Also updated the documentation in `docs/PROMPT_REWRITER_ARCHITECTURE.md` to reflect the correct usage pattern.

## Files Modified
- `services/prompt_rewriter.py` - Fixed Runner usage in all 3 rewrite methods
- `docs/PROMPT_REWRITER_ARCHITECTURE.md` - Updated documentation

## Expected Result
After this fix, the prompt rewriter should work correctly and use LLM-powered rewriting instead of falling back to simple concatenation. The logs should show:
- "✓ Designer prompt rewritten successfully"
- "✓ Writer prompt rewritten successfully" 
- "✓ Title generator prompt rewritten successfully"

Instead of the previous error messages and fallback warnings.

## Verification
The fix follows the same pattern used successfully in other parts of the codebase:
- `services/presentation_processor.py`
- `utils/agent_utils.py`

All these files use the correct `InMemoryRunner` pattern with proper session management.