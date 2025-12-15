# TTS Timeout Configuration Fix

## 🔍 **Current Issue**
```
WARNING:services.tts.engines.gemini_tts_engine:Gemini TTS attempt 1 failed: . Exception type: TimeoutError. Retrying in 1 seconds...
```

## ⏱️ **Timeout Settings - UPDATED**

### **Before Fix**
- **Gemini TTS Timeout**: 30 seconds
- **Traditional TTS Timeout**: 30 seconds
- **No environment variable override**

### **After Fix**
- **Gemini TTS Timeout**: 90 seconds (3x longer)
- **Traditional TTS Timeout**: 90 seconds (3x longer)
- **Environment variable support**: `TTS_TIMEOUT_SECONDS`

## 🚀 **How to Configure Timeout**

### **Option 1: Use Default (Recommended)**
The new default of **90 seconds** should handle most cases including:
- Complex martial arts style prompts
- Network latency issues
- Server processing delays

### **Option 2: Custom Timeout via Environment Variable**
```bash
# Set custom timeout (in seconds)
export TTS_TIMEOUT_SECONDS=120  # 2 minutes
export TTS_TIMEOUT_SECONDS=180  # 3 minutes for very complex cases
export TTS_TIMEOUT_SECONDS=60   # 1 minute for faster networks

# Then run your application
python main.py --style hkcomic
```

### **Option 3: Reduce Concurrency to Avoid Rate Limits**
```bash
# Reduce concurrent TTS calls to avoid overwhelming the API
export TTS_GEMINI_MAX_CONCURRENT=1
export TTS_MAX_CONCURRENT_SLIDES=1
export TTS_TIMEOUT_SECONDS=120
```

## 📊 **Timeout Recommendations by Use Case**

| Use Case | Timeout | Reasoning |
|----------|---------|-----------|
| **Simple prompts** | 60s | Basic TTS generation |
| **Complex styles (martial arts)** | 90s | Style processing overhead |
| **Slow network** | 120s | Network latency buffer |
| **High load periods** | 180s | Server processing delays |
| **Development/testing** | 300s | Maximum patience for debugging |

## 🔧 **Additional Optimizations Applied**

### **1. Retry Strategy**
- **Max retries**: 3 attempts
- **Exponential backoff**: 1s, 2s, 4s delays
- **Graceful degradation**: Falls back to traditional TTS

### **2. Concurrency Limits**
- **Gemini TTS**: 1 concurrent call (API stability)
- **Traditional TTS**: 3 concurrent calls (more stable)
- **Overall limit**: 3 slides processed simultaneously

### **3. Caching Benefits**
- **TTS style prompts**: Now cached to avoid regeneration
- **Prompt rewriter**: Cached to speed up style processing
- **Audio files**: Cached to avoid re-synthesis

## 🎯 **Expected Results**

After this fix, you should see:
- ✅ **Fewer timeout errors** (90s vs 30s timeout)
- ✅ **Better handling of complex styles** (martial arts prompts)
- ✅ **Configurable timeout** via environment variables
- ✅ **Improved reliability** with longer processing time allowance

## 🧪 **Testing the Fix**

1. **Run with new defaults**:
   ```bash
   python main.py --style hkcomic
   ```

2. **Monitor logs for**:
   - `TTS timeout set to X seconds via environment variable`
   - Fewer `TimeoutError` warnings
   - More successful TTS generations

3. **If still timing out, increase timeout**:
   ```bash
   export TTS_TIMEOUT_SECONDS=180
   python main.py --style hkcomic
   ```

## 📈 **Performance Impact**

- **Positive**: Fewer failed TTS calls, better success rate
- **Neutral**: Slightly longer wait time for actual timeouts (rare)
- **Overall**: Much better user experience with reliable TTS generation

The timeout has been increased from **30 seconds to 90 seconds** and is now configurable via the `TTS_TIMEOUT_SECONDS` environment variable!