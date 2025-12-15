# TTS Complexity Score Cleanup

## 🧹 **Code Cleanup Applied**

Since we removed the pro/flash model switching logic, the complexity scoring system was no longer needed. Here's what was cleaned up:

### **Before Cleanup**
```python
def _select_model(self, style_prompt: str) -> str:
    """Select appropriate Gemini TTS model based on style complexity."""
    
    # Use Pro model for complex style requirements
    complex_indicators = [
        "emphasis", "emotion", "multiple", "complex", "nuanced", 
        "storytelling", "dramatic", "varied pace", "expression",
        "passionate", "enthusiastic", "urgent", "careful"
    ]
    
    style_lower = style_prompt.lower()
    complexity_score = sum(1 for indicator in complex_indicators if indicator in style_lower)
    
    # Use Pro model if multiple complexity indicators are present
    if complexity_score >= 2:
        logger.debug(f"Using Pro model due to style complexity (score: {complexity_score})")
        return self.config.pro_model_id
    
    # Default to Flash model for speed
    logger.debug(f"Using Flash model for standard style (complexity score: {complexity_score})")
    return self.config.model_id
```

### **After Cleanup**
```python
def _select_model(self, style_prompt: str = None) -> str:
    """Get the configured Gemini TTS model."""
    
    # Always use the configured model (style_prompt no longer affects model selection)
    logger.debug(f"Using configured TTS model: {self.config.model_id}")
    return self.config.model_id
```

## ✅ **What Was Removed**

1. **Complex indicators list** - No longer needed
2. **Complexity score calculation** - Redundant logic
3. **Pro/Flash model switching** - Simplified to single model
4. **Style analysis logic** - No longer affects model selection

## ✅ **What Was Kept**

1. **Method signature compatibility** - `style_prompt` parameter kept for backward compatibility
2. **Same return behavior** - Still returns the model ID
3. **Debug logging** - Still logs which model is being used

## 🎯 **Benefits**

1. **Simpler code** - Removed ~15 lines of unused logic
2. **Better performance** - No more string analysis on every call
3. **Clearer intent** - Method now clearly just returns configured model
4. **Easier maintenance** - Less complex logic to maintain

## 🔧 **Current Behavior**

- **Always uses**: The model configured via `MODEL_TTS` environment variable
- **Default**: `gemini-2.5-flash-tts`
- **Override**: Set `MODEL_TTS=gemini-2.5-pro-tts` if you want the pro model
- **No automatic switching**: Model selection is now explicit and predictable

## 📊 **Impact**

- ✅ **Functionality**: Unchanged - TTS still works the same
- ✅ **Performance**: Slightly improved (no complexity analysis)
- ✅ **Maintainability**: Much simpler code
- ✅ **Predictability**: Model selection is now explicit

The TTS system is now cleaner and more predictable, following the same configuration pattern as all other agents in the system!