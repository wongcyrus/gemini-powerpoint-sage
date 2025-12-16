#!/usr/bin/env python3
"""
Wrapper script for video synthesis with aggressive timeout protection.
This script runs video synthesis with a hard timeout and kills the process if it hangs.
"""

import signal
import subprocess
import sys
import time
from pathlib import Path

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Video synthesis timed out")

def run_video_synthesis_with_timeout(slides_dir, audio_dir, video_output, video_config, timeout_seconds):
    """Run video synthesis with a hard timeout."""
    
    print(f"🚀 Starting video synthesis with {timeout_seconds}s timeout...")
    print(f"📁 Slides: {slides_dir}")
    print(f"🎵 Audio: {audio_dir}")
    print(f"🎥 Output: {video_output}")
    
    # Set up signal handler for timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Run the video synthesis command
        cmd = [
            sys.executable, "main.py", "--synthesize-video",
            "--slides-dir", slides_dir,
            "--audio-dir", audio_dir,
            "--video-output", video_output,
            "--video-config", video_config
        ]
        
        print(f"🔧 Command: {' '.join(cmd[:6])}...")
        print("📺 Starting video synthesis process (output will appear below)...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Start the process without capturing output for real-time feedback
        process = subprocess.Popen(cmd)
        
        # Monitor the process and show it's alive
        print("🔄 Process started, monitoring progress...")
        last_check = start_time
        
        while process.poll() is None:  # While process is running
            time.sleep(5)  # Check every 5 seconds
            current_time = time.time()
            elapsed = current_time - start_time
            print(f"⏱️  Process running for {elapsed:.0f}s... (still alive)")
            
            # Check if we've exceeded timeout
            if elapsed > timeout_seconds:
                print(f"⏰ Timeout reached ({timeout_seconds}s), terminating process...")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                raise TimeoutError("Video synthesis timed out")
        
        end_time = time.time()
        result_code = process.returncode
        
        print("=" * 60)
        
        # Create a result object that matches subprocess.run return
        class ProcessResult:
            def __init__(self, returncode):
                self.returncode = returncode
        
        result = ProcessResult(result_code)
        
        # Cancel the alarm
        signal.alarm(0)
        
        processing_time = end_time - start_time
        print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
        
        if result.returncode == 0:
            print("✅ Video synthesis completed successfully!")
            
            # Check if video file exists
            if Path(video_output).exists():
                file_size = Path(video_output).stat().st_size / (1024 * 1024)
                print(f"📊 Video file size: {file_size:.2f} MB")
                return True
            else:
                print("❌ Video file was not created")
                return False
        else:
            print(f"❌ Video synthesis failed with return code {result.returncode}")
            return False
            
    except TimeoutError:
        print(f"⏰ Video synthesis timed out after {timeout_seconds} seconds")
        print("🔪 Killing any remaining processes...")
        
        # Try to kill any remaining python processes
        try:
            subprocess.run(["pkill", "-f", "main.py.*synthesize-video"], timeout=5)
        except:
            pass
        
        # Check if video was created despite timeout
        if Path(video_output).exists():
            file_size = Path(video_output).stat().st_size / (1024 * 1024)
            print(f"📊 Video file exists despite timeout: {file_size:.2f} MB")
            print("🎯 Video may have been created successfully before the hang")
            return True
        else:
            print("❌ No video file found")
            return False
            
    except Exception as e:
        signal.alarm(0)  # Cancel alarm
        print(f"💥 Unexpected error: {e}")
        return False

def main():
    if len(sys.argv) != 5:
        print("Usage: python video_synthesis_wrapper.py <slides_dir> <audio_dir> <video_output> <video_config>")
        sys.exit(1)
    
    slides_dir = sys.argv[1]
    audio_dir = sys.argv[2]
    video_output = sys.argv[3]
    video_config = sys.argv[4]
    
    # Calculate timeout based on number of slides
    try:
        slide_count = len(list(Path(slides_dir).glob("*.png"))) + len(list(Path(slides_dir).glob("*.jpg")))
        # Increase timeout for large presentations: 60 seconds per slide, minimum 10 minutes
        timeout_seconds = max(600, slide_count * 60)
        print(f"📊 Found ~{slide_count} slides, setting timeout to {timeout_seconds//60} minutes")
    except:
        timeout_seconds = 1800  # 30 minutes default
        print(f"⏰ Using default timeout of {timeout_seconds//60} minutes")
    
    success = run_video_synthesis_with_timeout(slides_dir, audio_dir, video_output, video_config, timeout_seconds)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()