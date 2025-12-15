# TTS Model Configuration Update

## ✅ **Changes Applied**

### **1. Unified Model Configuration**
- **Removed**: `pro_model_id` (no longer needed)
- **Simplified**: Single `model_id` for all TTS operations
- **Default**: Always use `gemini-2.5-flash-tts`

### **2. Environment Variable Support**
Following the same pattern as other agents:

```bash
# Configure TTS model like other agents
export MODEL_TTS="gemini-2.5-flash-tts"    # Default (fast)
export MODEL_TTS="gemini-2.5-pro-tts"      # If you need pro model
export MODEL_TTS="custom-tts-model"        # Custom model
```

### **3. Consistent with Other Agents**
Now TTS follows the same pattern as:
- `MODEL_WRITER="gemini-2.5-flash"`
- `MODEL_DESIGNER="gemini-3-pro-image-preview"`
- `MODEL_TRANSLATOR="gemini-2.5-flash"`
- `MODEL_TTS="gemini-2.5-flash-tts"` ← **NEW**

## 🔧 **Configuration Options**

### **Default Configuration (Recommended)**
```bash
# No environment variables needed - uses fast flash model
python main.py --style hkcomic
```

### **Custom Model Configuration**
```bash
# Use pro model if needed
export MODEL_TTS="gemini-2.5-pro-tts"
python main.py --style hkcomic

# Use flash model explicitly
export MODEL_TTS="gemini-2.5-flash-tts"
python main.py --style hkcomic
```

### **Combined with Timeout Configuration**
```bash
# Optimal configuration for complex styles
export MODEL_TTS="gemini-2.5-flash-tts"
export TTS_TIMEOUT_SECONDS=90
export TTS_GEMINI_MAX_CONCURRENT=1
python main.py --style hkcomic
```

## 📋 **Code Changes Summary**

### **1. TTS Config (`config/tts_config.py`)**
```python
# Before
model_id: str = "gemini-2.5-flash-tts"
pro_model_id: str = "gemini-2.5-pro-tts"

# After
model_id: str = field(default_factory=lambda: os.getenv("MODEL_TTS", "gemini-2.5-flash-tts"))
```

### **2. Constants (`config/constants.py`)**
```python
# Before
TTS_GEMINI_FLASH: Final[str] = "gemini-2.5-flash-tts"
TTS_GEMINI_PRO: Final[str] = "gemini-2.5-pro-tts"

# After
TTS: Final[str] = "gemini-2.5-flash-tts"
MODEL_TTS: Final[str] = "MODEL_TTS"
```

### **3. TTS Engine (`services/tts/engines/gemini_tts_engine.py`)**
```python
# Before
if complexity_score >= 2:
    return self.config.pro_model_id
return self.config.model_id

# After
return self.config.model_id  # Always use configured model
```

## 🎯 **Benefits**

1. **Consistency**: TTS now follows same pattern as all other agents
2. **Simplicity**: No more pro/flash model switching logic
3. **Flexibility**: Easy to override model via environment variable
4. **Maintainability**: Single model configuration to manage

## 🧪 **Testing**

The configuration has been tested and works correctly:

```bash
# Test default
python -c "from config.tts_config import get_tts_config; print(get_tts_config().gemini.model_id)"
# Output: gemini-2.5-flash-tts

# Test override
MODEL_TTS=gemini-2.5-pro-tts python -c "from config.tts_config import get_tts_config; print(get_tts_config().gemini.model_id)"
# Output: gemini-2.5-pro-tts
```

## 🚀 **Ready to Use**

The TTS model configuration now follows the same pattern as all other agents in the system. You can configure it using the `MODEL_TTS` environment variable just like `MODEL_WRITER`, `MODEL_DESIGNER`, etc.

**Default behavior**: Uses `gemini-2.5-flash-tts` for optimal speed and cost efficiency.
**Override capability**: Set `MODEL_TTS` environment variable to use any model you prefer.