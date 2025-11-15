"""
Enhanced Fast Recorder with Alert Support
Integrates fast frame recording with metadata tracking for alerts
"""
import time
import os
import shutil
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import cv2
import numpy as np
from pathlib import Path


class FastRecorder:
    """
    High-performance recorder that saves frames directly to disk
    with minimal processing overhead and alert metadata tracking.
    """
    
    def __init__(self, storage_path: str = "recordings"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.current_session_id: Optional[str] = None
        self.current_session_path: Optional[Path] = None
        self.frame_count = 0
        self.start_time: Optional[float] = None
        
        # FPS tracking
        self.fps_log: Optional[object] = None
        self.frame_timestamps: List[float] = []
        
        # Alert tracking
        self.alerts: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.prev_time = time.time()
        self.fps_frame_count = 0
        self.current_fps = 0.0
        
    def start_recording(self) -> str:
        """Start a new recording session"""
        if self.is_recording:
            raise RuntimeError("Already recording")
        
        # Create session directory
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_path = self.storage_path / self.current_session_id
        self.current_session_path.mkdir(parents=True, exist_ok=True)
        
        # Create frames subdirectory
        frames_dir = self.current_session_path / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        # Initialize tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.frame_timestamps = []
        self.alerts = []
        
        # Open FPS log
        fps_log_path = self.current_session_path / "frame_timestamps.txt"
        self.fps_log = open(fps_log_path, 'w')
        
        self.is_recording = True
        print(f"[FastRecorder] Recording started: {self.current_session_id}")
        
        return self.current_session_id
    
    def record_frame(self, frame: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a single frame with optional metadata
        
        Args:
            frame: OpenCV image (numpy array)
            metadata: Optional metadata dict (lidar, odom, etc.)
        
        Returns:
            True if frame was recorded successfully
        """
        if not self.is_recording or frame is None:
            return False
        
        try:
            current_time = time.time()
            self.frame_count += 1
            
            # Log timestamp
            self.fps_log.write(f"{current_time}\n")
            self.fps_log.flush()  # Ensure immediate write
            self.frame_timestamps.append(current_time)
            
            # Save frame (JPEG for speed)
            frame_filename = f"frame_{self.frame_count:06d}.jpg"
            frame_path = self.current_session_path / "frames" / frame_filename
            
            # Fast JPEG encoding (quality 90 for good balance)
            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # Save metadata if provided
            if metadata:
                metadata_filename = f"frame_{self.frame_count:06d}.json"
                metadata_path = self.current_session_path / "frames" / metadata_filename
                
                # Add timestamp to metadata
                metadata['timestamp'] = current_time
                metadata['frame_number'] = self.frame_count
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
            
            # Update FPS calculation (every 1 second)
            self.fps_frame_count += 1
            if current_time - self.prev_time >= 1.0:
                self.current_fps = self.fps_frame_count / (current_time - self.prev_time)
                self.prev_time = current_time
                self.fps_frame_count = 0
                print(f"[FastRecorder] Current FPS: {self.current_fps:.2f}")
            
            return True
            
        except Exception as e:
            print(f"[FastRecorder] Error recording frame: {e}")
            return False
    
    def add_alert(self, alert_type: str = "manual", description: str = "", 
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add an alert marker to the current recording
        
        Args:
            alert_type: Type of alert ("manual", "anomaly", "event", etc.)
            description: Human-readable description
            metadata: Additional metadata
        
        Returns:
            Alert dict with timestamp and frame number
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")
        
        alert = {
            'timestamp': time.time(),
            'frame_number': self.frame_count,
            'type': alert_type,
            'description': description,
            'metadata': metadata or {}
        }
        
        self.alerts.append(alert)
        print(f"[FastRecorder] Alert added at frame {self.frame_count}: {alert_type}")
        
        return alert
    
    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop recording and save session metadata
        
        Returns:
            Session summary dict
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Close FPS log
        self.fps_log.close()
        
        # Calculate average FPS
        if len(self.frame_timestamps) > 1:
            first_time = self.frame_timestamps[0]
            last_time = self.frame_timestamps[-1]
            avg_fps = len(self.frame_timestamps) / (last_time - first_time) if (last_time - first_time) > 0 else 0
        else:
            avg_fps = 0
        
        # Create session metadata
        session_metadata = {
            'session_id': self.current_session_id,
            'start_time': self.start_time,
            'end_time': end_time,
            'duration': duration,
            'total_frames': self.frame_count,
            'average_fps': avg_fps,
            'alerts': self.alerts,
            'alert_count': len(self.alerts)
        }
        
        # Save session metadata
        metadata_path = self.current_session_path / "session_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(session_metadata, f, indent=2)
        
        # Save alerts separately for easy access
        if self.alerts:
            alerts_path = self.current_session_path / "alerts.json"
            with open(alerts_path, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        
        print(f"[FastRecorder] Recording stopped")
        print(f"[FastRecorder] Total frames: {self.frame_count}")
        print(f"[FastRecorder] Duration: {duration:.2f}s")
        print(f"[FastRecorder] Average FPS: {avg_fps:.2f}")
        print(f"[FastRecorder] Alerts: {len(self.alerts)}")
        
        self.is_recording = False
        self.current_session_id = None
        self.current_session_path = None
        
        return session_metadata
    
    def get_recording_status(self) -> Dict[str, Any]:
        """Get current recording status"""
        if not self.is_recording:
            return {
                'is_recording': False,
                'session_id': None,
                'frames_recorded': 0,
                'duration': 0,
                'current_fps': 0,
                'alerts': 0
            }
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            'is_recording': True,
            'session_id': self.current_session_id,
            'frames_recorded': self.frame_count,
            'duration': duration,
            'current_fps': self.current_fps,
            'alerts': len(self.alerts)
        }
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all recorded sessions"""
        sessions = []
        
        for session_dir in sorted(self.storage_path.iterdir(), reverse=True):
            if not session_dir.is_dir():
                continue
            
            metadata_path = session_dir / "session_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    sessions.append(metadata)
        
        return sessions
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific session"""
        session_path = self.storage_path / session_id
        metadata_path = session_path / "session_metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def get_frame(self, session_id: str, frame_number: int) -> Optional[np.ndarray]:
        """Load a specific frame from a session"""
        session_path = self.storage_path / session_id
        frame_filename = f"frame_{frame_number:06d}.jpg"
        frame_path = session_path / "frames" / frame_filename
        
        if not frame_path.exists():
            return None
        
        return cv2.imread(str(frame_path))
    
    def get_frame_metadata(self, session_id: str, frame_number: int) -> Optional[Dict[str, Any]]:
        """Load metadata for a specific frame"""
        session_path = self.storage_path / session_id
        metadata_filename = f"frame_{frame_number:06d}.json"
        metadata_path = session_path / "frames" / metadata_filename
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)


# Standalone video creation utility
def create_video_from_session(session_id: str, storage_path: str = "recordings", 
                              output_name: Optional[str] = None, fps: float = 30.0):
    """
    Create a video from a recorded session
    
    Args:
        session_id: Session ID to convert
        storage_path: Base recordings directory
        output_name: Output video filename (default: session_id.mp4)
        fps: Target FPS for video
    """
    session_path = Path(storage_path) / session_id
    frames_dir = session_path / "frames"
    
    if not frames_dir.exists():
        print(f"Error: Session {session_id} not found")
        return
    
    # Get all frame files
    frame_files = sorted([f for f in frames_dir.iterdir() if f.suffix == '.jpg'])
    
    if not frame_files:
        print("Error: No frames found in session")
        return
    
    # Read first frame to get dimensions
    first_frame = cv2.imread(str(frame_files[0]))
    height, width = first_frame.shape[:2]
    
    # Output filename
    if output_name is None:
        output_name = f"{session_id}.mp4"
    
    output_path = session_path / output_name
    
    # Initialize VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    print(f"Creating video with {len(frame_files)} frames at {fps} FPS...")
    
    for i, frame_file in enumerate(frame_files):
        frame = cv2.imread(str(frame_file))
        out.write(frame)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(frame_files)} frames...")
    
    out.release()
    
    print(f"Video created: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    # Example usage
    print("FastRecorder Test")
    
    recorder = FastRecorder()
    
    # Start recording
    session_id = recorder.start_recording()
    
    # Simulate recording frames
    for i in range(100):
        # Create dummy frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Add alert at frame 50
        if i == 50:
            recorder.add_alert("manual", "Test alert at frame 50")
        
        recorder.record_frame(frame, metadata={'frame_id': i})
        time.sleep(0.033)  # ~30 FPS
    
    # Stop recording
    summary = recorder.stop_recording()
    print(f"\nSession summary: {summary}")
    
    # Create video
    create_video_from_session(session_id)
