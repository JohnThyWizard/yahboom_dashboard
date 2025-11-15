#!/usr/bin/env python3
"""
Video Creation Utility
Creates MP4 videos from recorded sessions with proper FPS
"""
import cv2
import os
import sys
import json
from pathlib import Path
import argparse


def create_video(session_id: str, storage_path: str = "recordings", 
                 output_name: str = None, fps: float = None):
    """
    Create a video from a recorded session
    
    Args:
        session_id: Session ID to convert
        storage_path: Base recordings directory
        output_name: Output video filename (default: session_id.mp4)
        fps: Target FPS for video (default: use session average FPS)
    """
    session_path = Path(storage_path) / session_id
    frames_dir = session_path / "frames"
    
    if not frames_dir.exists():
        print(f"❌ Error: Session '{session_id}' not found in {storage_path}")
        return False
    
    # Load session metadata
    metadata_path = session_path / "session_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            if fps is None:
                fps = metadata.get('average_fps', 30.0)
            print(f"📊 Session Info:")
            print(f"   Duration: {metadata['duration']:.2f}s")
            print(f"   Total Frames: {metadata['total_frames']}")
            print(f"   Average FPS: {metadata['average_fps']:.2f}")
            print(f"   Alerts: {metadata['alert_count']}")
    else:
        if fps is None:
            fps = 30.0
        print(f"⚠️  Warning: No metadata found, using default FPS: {fps}")
    
    # Get all frame files
    frame_files = sorted([f for f in frames_dir.iterdir() if f.suffix == '.jpg'])
    
    if not frame_files:
        print("❌ Error: No frames found in session")
        return False
    
    print(f"\n🎬 Creating video...")
    print(f"   Frames: {len(frame_files)}")
    print(f"   Target FPS: {fps:.2f}")
    
    # Read first frame to get dimensions
    first_frame = cv2.imread(str(frame_files[0]))
    if first_frame is None:
        print("❌ Error: Failed to read first frame")
        return False
    
    height, width = first_frame.shape[:2]
    print(f"   Resolution: {width}x{height}")
    
    # Output filename
    if output_name is None:
        output_name = f"{session_id}.mp4"
    
    output_path = session_path / output_name
    
    # Initialize VideoWriter
    # Try different codecs in order of preference
    codecs = [
        ('mp4v', 'MP4V'),  # Most compatible
        ('avc1', 'H.264'), # Better quality
        ('XVID', 'XVID'),  # Fallback
    ]
    
    out = None
    for codec, name in codecs:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            if out.isOpened():
                print(f"   Codec: {name}")
                break
        except:
            continue
    
    if out is None or not out.isOpened():
        print("❌ Error: Failed to initialize video writer")
        return False
    
    # Write frames
    print(f"\n⏳ Processing frames...")
    for i, frame_file in enumerate(frame_files):
        frame = cv2.imread(str(frame_file))
        if frame is not None:
            out.write(frame)
        
        # Progress indicator
        if (i + 1) % 100 == 0 or (i + 1) == len(frame_files):
            progress = (i + 1) / len(frame_files) * 100
            print(f"   Progress: {i + 1}/{len(frame_files)} ({progress:.1f}%)")
    
    out.release()
    
    # Get file size
    file_size_mb = output_path.stat().st_size / 1024 / 1024
    
    print(f"\n✅ Video created successfully!")
    print(f"   Output: {output_path}")
    print(f"   Size: {file_size_mb:.2f} MB")
    print(f"   Duration: {len(frame_files) / fps:.2f}s")
    
    return True


def list_sessions(storage_path: str = "recordings"):
    """List all available sessions"""
    storage = Path(storage_path)
    
    if not storage.exists():
        print(f"❌ Error: Storage path '{storage_path}' not found")
        return
    
    sessions = []
    for session_dir in sorted(storage.iterdir(), reverse=True):
        if not session_dir.is_dir():
            continue
        
        metadata_path = session_dir / "session_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                sessions.append({
                    'id': session_dir.name,
                    'metadata': metadata
                })
    
    if not sessions:
        print("📭 No sessions found")
        return
    
    print(f"📁 Available Sessions ({len(sessions)}):\n")
    for session in sessions:
        meta = session['metadata']
        print(f"   ID: {session['id']}")
        print(f"   Duration: {meta['duration']:.2f}s")
        print(f"   Frames: {meta['total_frames']}")
        print(f"   FPS: {meta['average_fps']:.2f}")
        print(f"   Alerts: {meta['alert_count']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Create videos from recorded sessions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all sessions
  python create_video.py --list

  # Create video from session
  python create_video.py 20250115_143022

  # Create video with custom FPS
  python create_video.py 20250115_143022 --fps 60

  # Create video with custom output name
  python create_video.py 20250115_143022 --output my_video.mp4
        """
    )
    
    parser.add_argument('session_id', nargs='?', help='Session ID to convert')
    parser.add_argument('--list', action='store_true', help='List all available sessions')
    parser.add_argument('--storage', default='recordings', help='Recordings storage path')
    parser.add_argument('--fps', type=float, help='Target FPS for video (default: use session FPS)')
    parser.add_argument('--output', help='Output video filename')
    
    args = parser.parse_args()
    
    if args.list:
        list_sessions(args.storage)
        return
    
    if not args.session_id:
        parser.print_help()
        return
    
    success = create_video(
        session_id=args.session_id,
        storage_path=args.storage,
        output_name=args.output,
        fps=args.fps
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
