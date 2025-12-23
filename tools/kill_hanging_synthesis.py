#!/usr/bin/env python3
"""
Kill hanging video synthesis processes.
"""

import subprocess
import sys
import time


def find_synthesis_processes():
    """Find running video synthesis processes."""
    try:
        # Look for main.py processes with synthesize-video
        result = subprocess.run([
            'ps', 'aux'
        ], capture_output=True, text=True)
        
        processes = []
        for line in result.stdout.split('\n'):
            if 'main.py' in line and 'synthesize-video' in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    processes.append((pid, line))
        
        return processes
        
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []


def kill_processes(processes, force=False):
    """Kill the specified processes."""
    if not processes:
        print("No video synthesis processes found.")
        return
    
    print(f"Found {len(processes)} video synthesis processes:")
    for pid, line in processes:
        print(f"  PID {pid}: {line}")
    
    if not force:
        response = input("\nKill these processes? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    for pid, line in processes:
        try:
            print(f"Killing PID {pid}...")
            subprocess.run(['kill', pid], check=True)
            time.sleep(1)
            
            # Check if still running
            try:
                subprocess.run(['kill', '-0', pid], check=True)
                print(f"  Process {pid} still running, using SIGKILL...")
                subprocess.run(['kill', '-9', pid], check=True)
            except subprocess.CalledProcessError:
                print(f"  Process {pid} terminated successfully")
                
        except subprocess.CalledProcessError as e:
            print(f"  Failed to kill PID {pid}: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Kill hanging video synthesis processes')
    parser.add_argument('--force', action='store_true',
                       help='Kill without confirmation')
    
    args = parser.parse_args()
    
    print("🔍 Looking for hanging video synthesis processes...")
    
    processes = find_synthesis_processes()
    kill_processes(processes, force=args.force)
    
    # Also kill any FFmpeg processes that might be hanging
    print("\n🔍 Looking for hanging FFmpeg processes...")
    try:
        result = subprocess.run([
            'pgrep', '-f', 'ffmpeg.*segment_'
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            ffmpeg_pids = result.stdout.strip().split('\n')
            print(f"Found {len(ffmpeg_pids)} FFmpeg processes")
            
            if not args.force:
                response = input("Kill FFmpeg processes too? (y/N): ")
                if response.lower() != 'y':
                    return
            
            for pid in ffmpeg_pids:
                try:
                    print(f"Killing FFmpeg PID {pid}...")
                    subprocess.run(['kill', pid], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"  Failed to kill FFmpeg PID {pid}: {e}")
        else:
            print("No hanging FFmpeg processes found.")
            
    except Exception as e:
        print(f"Error checking FFmpeg processes: {e}")


if __name__ == '__main__':
    main()