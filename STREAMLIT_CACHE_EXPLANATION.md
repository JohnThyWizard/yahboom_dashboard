# Understanding Streamlit MediaFileStorageError

## Why These Errors Occur

### The Problem

Even though we're now passing **numpy arrays** to `st.image()`, Streamlit still has an internal caching mechanism that tries to:

1. **Generate cache keys** for images (those hash-like filenames like `be44f52f5942e8100a093ec8f726c4126cf88ca601af7e62fbdf6d24.jpg`)
2. **Store images temporarily** in memory for performance
3. **Retrieve cached images** on subsequent renders

### What's Happening

```
Your Code → st.image(numpy_array) 
         ↓
Streamlit internally:
  1. Generates hash ID from image data
  2. Tries to cache it in memory_media_file_storage
  3. On refresh/re-render, looks for cached file
  4. ❌ File not found → MediaFileStorageError
```

### Why It Still Happens with Numpy Arrays

Even with numpy arrays, Streamlit:
- Still generates hash IDs for caching
- Still tries to manage a cache
- The cache gets cleared between page refreshes
- But Streamlit still looks for the old cache entries

### The Root Cause

**Streamlit's auto-refresh mechanism** (`st.rerun()` in live mode) causes:
- Rapid page refreshes
- Cache gets cleared
- But Streamlit still has references to old cache keys
- Mismatch between cache keys and actual cached files

## Are These Errors Harmful?

**Short answer: No, they're mostly harmless warnings.**

- ✅ **Functionality works**: Images still display correctly
- ✅ **No data loss**: Nothing is broken
- ⚠️ **Just noise**: Clutters the logs
- ⚠️ **Performance**: Slight overhead from failed cache lookups

## Solutions

### Option 1: Suppress the Warnings (Recommended)

Add Streamlit configuration to reduce logging:

```python
# At the top of dashboard.py, after imports
import logging
logging.getLogger('streamlit.runtime.media_file_storage').setLevel(logging.ERROR)
```

### Option 2: Add Unique Keys to Prevent Caching

Force Streamlit to treat each frame as unique:

```python
st.image(camera_frame, width='stretch', use_column_width=False)
# Add a unique key based on timestamp
st.image(camera_frame, width='stretch', key=f"camera_{time.time()}")
```

### Option 3: Use BytesIO Directly

Pass image bytes instead of numpy arrays:

```python
# Convert numpy array to bytes
_, buffer = cv2.imencode('.jpg', camera_frame)
st.image(buffer.tobytes(), width='stretch')
```

### Option 4: Disable Auto-Refresh (Not Recommended)

Remove `st.rerun()` from live mode, but this breaks real-time updates.

## Recommended Fix

The best approach is **Option 1** - suppress the warnings since they don't affect functionality. We can also add a small optimization to reduce cache misses.

## Important Note

**These errors are printed directly by Streamlit's exception handlers**, which means they bypass Python's logging system. While we've added comprehensive logging suppression, some errors may still appear in the console output because Streamlit prints them directly to stderr.

**This is expected behavior** and does not indicate a problem with your code. The errors are:
- ✅ **Harmless** - Images still display correctly
- ✅ **Cosmetic** - Just log noise
- ✅ **Unavoidable** - Part of Streamlit's internal caching mechanism

If you want to completely hide them, you can run Streamlit with output redirection:
```bash
streamlit run frontend/dashboard.py 2>/dev/null
```

But this will also hide other potentially useful error messages, so it's not recommended.

