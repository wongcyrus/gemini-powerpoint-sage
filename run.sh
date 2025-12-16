#!/bin/bash

# Helper script to run the Gemini Powerpoint Sage
# Updated for the new three-mode system

# Ensure we are in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Show usage if no arguments or help requested
if [ $# -eq 0 ] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Gemini PowerPoint Sage - Three Processing Modes" >&2
    echo "" >&2
    echo "🌟 All Styles Processing (recommended):" >&2
    echo "  ./run.sh --styles" >&2
    echo "  ./run.sh                    # defaults to --styles" >&2
    echo "" >&2
    echo "🎨 Single Style Processing:" >&2
    echo "  ./run.sh --style-config cyberpunk      # case-insensitive" >&2
    echo "  ./run.sh --style-config professional   # case-insensitive" >&2
    echo "  ./run.sh --style-config gundam         # case-insensitive" >&2
    echo "  ./run.sh --style-config hkcomic        # includes video synthesis" >&2
    echo "" >&2
    echo "📄 Single File Processing:" >&2
    echo "  ./run.sh --pptx file.pptx --language en --style professional" >&2
    echo "  ./run.sh --pptx file.pptx --language 'en,zh-CN' --style cyberpunk" >&2
    echo "" >&2
    echo "🔧 Other Options:" >&2
    echo "  ./run.sh --refine progress.json" >&2
    echo "" >&2
    echo "ℹ️  All configuration is now handled through YAML files in styles/ directory" >&2
    echo "   Use --styles or --style-config for organized processing" >&2
    exit 1
fi


# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: Virtual environment not found. Run ./setup.sh first."
    echo "Continuing with system Python..."
fi

# Note: Environment variables are loaded from .env file by main.py using python-dotenv
# You can still override them here if needed:
# export GOOGLE_CLOUD_PROJECT="your-project-id"
# export GOOGLE_CLOUD_LOCATION="us-central1"

echo "Starting Gemini Powerpoint Sage..."
if [ -n "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "Project: $GOOGLE_CLOUD_PROJECT"
else
    echo "Project: (will be loaded from .env file)"
fi

# If no arguments provided, default to --styles
if [ $# -eq 0 ]; then
    echo "No arguments provided, defaulting to --styles mode"
    set -- --styles
fi

# Check if this is hkcomic style config for video synthesis
HKCOMIC_VIDEO_SYNTHESIS=false
if [[ "$1" == "--style-config" ]] && [[ "${2,,}" == "hkcomic" ]]; then
    HKCOMIC_VIDEO_SYNTHESIS=true
fi

# Run the python script
python3 main.py "$@"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Success!"
    
    # If hkcomic style was processed successfully, run video synthesis
    if [ "$HKCOMIC_VIDEO_SYNTHESIS" = true ]; then
        echo ""
        echo "🎬 Starting video synthesis for hkcomic style..."
        echo "=================================================="
        
        # Define paths based on hkcomic config
        SLIDES_DIR="notes/hkcomic/generate"
        
        # Find the actual generated directories (they have language suffixes)
        VISUALS_DIR=""
        SPEECH_DIR=""
        PRESENTATION_NAME=""
        LANGUAGE_CODE=""
        
        # Look for directories with _visuals and _speech suffixes
        for dir in "$SLIDES_DIR"/*_visuals; do
            if [ -d "$dir" ]; then
                VISUALS_DIR="$dir"
                # Extract presentation name and language from directory name
                # Format: "Presentation Name_language_visuals"
                DIR_BASENAME=$(basename "$dir")
                # Remove _visuals suffix
                NAME_LANG="${DIR_BASENAME%_visuals}"
                # Extract language code (last part after final underscore)
                LANGUAGE_CODE="${NAME_LANG##*_}"
                # Extract presentation name (everything before final underscore)
                PRESENTATION_NAME="${NAME_LANG%_*}"
                break
            fi
        done
        
        for dir in "$SLIDES_DIR"/*_speech; do
            if [ -d "$dir" ]; then
                SPEECH_DIR="$dir"
                # Double-check we have the same presentation and language
                DIR_BASENAME=$(basename "$dir")
                NAME_LANG="${DIR_BASENAME%_speech}"
                SPEECH_LANG="${NAME_LANG##*_}"
                SPEECH_NAME="${NAME_LANG%_*}"
                
                # Verify consistency
                if [ "$SPEECH_LANG" != "$LANGUAGE_CODE" ] || [ "$SPEECH_NAME" != "$PRESENTATION_NAME" ]; then
                    echo "⚠️  Warning: Mismatched presentation names or languages:"
                    echo "   Visuals: $PRESENTATION_NAME ($LANGUAGE_CODE)"
                    echo "   Speech:  $SPEECH_NAME ($SPEECH_LANG)"
                fi
                break
            fi
        done
        
        # Create descriptive video filename with presentation name and language
        if [ -n "$PRESENTATION_NAME" ] && [ -n "$LANGUAGE_CODE" ]; then
            # Clean up presentation name for filename (replace spaces with underscores, remove special chars)
            CLEAN_NAME=$(echo "$PRESENTATION_NAME" | sed 's/[^a-zA-Z0-9 ]//g' | sed 's/ /_/g')
            VIDEO_OUTPUT="$SLIDES_DIR/${CLEAN_NAME}_${LANGUAGE_CODE}_hkcomic.mp4"
        else
            # Fallback to generic name if we can't extract details
            VIDEO_OUTPUT="$SLIDES_DIR/hkcomic_presentation.mp4"
        fi
        
        # Check if we found the required directories
        if [ -z "$VISUALS_DIR" ] || [ -z "$SPEECH_DIR" ]; then
            echo "⚠️  Could not find generated visuals or speech directories in $SLIDES_DIR"
            echo "   Looking for directories ending with _visuals and _speech"
            echo "   Available directories:"
            ls -la "$SLIDES_DIR" 2>/dev/null || echo "   Directory $SLIDES_DIR not found"
            echo "   Skipping video synthesis."
        else
            echo "📁 Found visuals directory: $VISUALS_DIR"
            echo "📁 Found speech directory: $SPEECH_DIR"
            if [ -n "$PRESENTATION_NAME" ] && [ -n "$LANGUAGE_CODE" ]; then
                echo "📋 Presentation: $PRESENTATION_NAME"
                echo "🌐 Language: $LANGUAGE_CODE"
            fi
            echo "🎥 Output video: $VIDEO_OUTPUT"
            
            # Count files to give user an idea of processing time
            SLIDE_COUNT=$(find "$VISUALS_DIR" -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" | wc -l)
            AUDIO_COUNT=$(find "$SPEECH_DIR" -name "*.mp3" | wc -l)
            
            echo "📊 Found $SLIDE_COUNT slide images and $AUDIO_COUNT audio files"
            
            if [ "$SLIDE_COUNT" -eq 0 ] || [ "$AUDIO_COUNT" -eq 0 ]; then
                echo "⚠️  No slide images or audio files found. Skipping video synthesis."
            elif [ "$SLIDE_COUNT" -ne "$AUDIO_COUNT" ]; then
                echo "⚠️  Mismatch: $SLIDE_COUNT images vs $AUDIO_COUNT audio files. Skipping video synthesis."
            else
                echo "⏱️  Estimated processing time: $((SLIDE_COUNT * 10 / 60)) minutes (for $SLIDE_COUNT slides)"
                echo ""
                
                # Run video synthesis with hkcomic-optimized settings and timeout
                echo "🚀 Running video synthesis with FFmpeg implementation..."
                

                
                # Run with aggressive timeout protection using wrapper script
                python3 video_synthesis_wrapper.py \
                    "$VISUALS_DIR" \
                    "$SPEECH_DIR" \
                    "$VIDEO_OUTPUT" \
                    '{"resolution": [1280, 720], "fps": 24, "video_bitrate": "3M", "audio_bitrate": "192k"}'
                
                VIDEO_EXIT_CODE=$?
                
                # Check if it was killed by timeout
                if [ $VIDEO_EXIT_CODE -eq 124 ]; then
                    echo ""
                    echo "⏰ Video synthesis timed out after $TIMEOUT_MINUTES minutes"
                    echo "   This may indicate a hanging issue in the video processing."
                    echo ""
                    echo "🔧 You can try running with a longer timeout manually:"
                    echo "   timeout 3600s python3 main.py --synthesize-video \\"
                    echo "     --slides-dir \"$VISUALS_DIR\" \\"
                    echo "     --audio-dir \"$SPEECH_DIR\" \\"
                    echo "     --video-output \"$VIDEO_OUTPUT\""
                    echo ""
                    echo "📊 Or check if the video was partially created:"
                    if [ -f "$VIDEO_OUTPUT" ]; then
                        FILE_SIZE=$(du -h "$VIDEO_OUTPUT" 2>/dev/null | cut -f1 || echo "unknown")
                        echo "   ✅ Partial video exists: $VIDEO_OUTPUT ($FILE_SIZE)"
                        echo "   The video may have been created successfully despite the timeout."
                    else
                        echo "   ❌ No video file found at: $VIDEO_OUTPUT"
                    fi
                    VIDEO_EXIT_CODE=124  # Ensure we handle this as a timeout
                fi
                if [ $VIDEO_EXIT_CODE -eq 0 ]; then
                    echo ""
                    echo "🎉 Video synthesis completed successfully!"
                    echo "📹 Output video: $VIDEO_OUTPUT"
                    
                    # Show file size if video was created
                    if [ -f "$VIDEO_OUTPUT" ]; then
                        FILE_SIZE=$(du -h "$VIDEO_OUTPUT" | cut -f1)
                        echo "📊 File size: $FILE_SIZE"
                        echo ""
                        echo "✅ Complete hkcomic workflow finished!"
                        echo "   1. ✅ Generated speaker notes and visuals"
                        echo "   2. ✅ Created presentation video"
                        echo ""
                        echo "🎬 You can now view your hkcomic-style presentation video:"
                        echo "   $VIDEO_OUTPUT"
                    else
                        echo "⚠️  Video file was not created despite success code"
                    fi
                elif [ $VIDEO_EXIT_CODE -eq 124 ]; then
                    # Timeout case - already handled above
                    echo "   Video synthesis was terminated due to timeout."
                elif [ -f "$VIDEO_OUTPUT" ]; then
                    # Process failed but video exists - might be a hanging issue after completion
                    FILE_SIZE=$(du -h "$VIDEO_OUTPUT" 2>/dev/null | cut -f1 || echo "unknown")
                    echo ""
                    echo "⚠️  Process ended with error code $VIDEO_EXIT_CODE, but video was created!"
                    echo "📹 Output video: $VIDEO_OUTPUT"
                    echo "📊 File size: $FILE_SIZE"
                    echo ""
                    echo "🎯 This suggests the video was created successfully but the process hung afterward."
                    echo "✅ Complete hkcomic workflow finished!"
                    echo "   1. ✅ Generated speaker notes and visuals"
                    echo "   2. ✅ Created presentation video (despite process hanging)"
                    echo ""
                    echo "🎬 You can now view your hkcomic-style presentation video:"
                    echo "   $VIDEO_OUTPUT"
                else
                    echo ""
                    echo "❌ Video synthesis failed with error code $VIDEO_EXIT_CODE"
                    echo "   The speaker notes and visuals were generated successfully,"
                    echo "   but video creation encountered an error."
                    echo ""
                    echo "🔧 You can try running video synthesis manually:"
                    echo "   python3 main.py --synthesize-video \\"
                    echo "     --slides-dir \"$VISUALS_DIR\" \\"
                    echo "     --audio-dir \"$SPEECH_DIR\" \\"
                    echo "     --video-output \"$VIDEO_OUTPUT\""
                fi
            fi
        fi
        
        echo "=================================================="
    fi
else
    echo "Failed with error code $EXIT_CODE"
fi
exit $EXIT_CODE
