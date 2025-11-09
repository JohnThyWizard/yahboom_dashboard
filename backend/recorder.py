"""
Data Recorder - Handles synchronized recording of sensor data
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
import threading
from collections import deque


class DataRecorder:
    """Records synchronized sensor data to disk"""
    
    def __init__(self, storage_path: str, config: dict):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.is_recording = False
        
        # Current session
        self.session_id: Optional[str] = None
        self.session_path: Optional[Path] = None
        self.metadata_file: Optional[Path] = None
        
        # Frame storage
        self.frame_buffer = deque(maxlen=1000)  # Buffer for synchronization
        self.frame_counter = 0
        
        # Thread safety
        self.recording_lock = threading.Lock()
        
        # Metadata structure
        self.metadata = {
            'session_id': None,
            'start_time': None,
            'end_time': None,
            'frames': [],
            'alerts': []
        }
    
    def start_recording(self) -> str:
        """Start a new recording session"""
        with self.recording_lock:
            if self.is_recording:
                return self.session_id
            
            # Generate session ID
            self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.session_path = self.storage_path / self.session_id
            self.session_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.session_path / 'frames').mkdir(exist_ok=True)
            (self.session_path / 'lidar').mkdir(exist_ok=True)
            
            # Initialize metadata
            self.metadata = {
                'session_id': self.session_id,
                'start_time': time.time(),
                'end_time': None,
                'frames': [],
                'alerts': []
            }
            
            self.metadata_file = self.session_path / 'metadata.json'
            self.frame_counter = 0
            self.is_recording = True
            
            return self.session_id
    
    def stop_recording(self):
        """Stop the current recording session"""
        with self.recording_lock:
            if not self.is_recording:
                return
            
            self.is_recording = False
            self.metadata['end_time'] = time.time()
            
            # Save metadata
            if self.metadata_file:
                with open(self.metadata_file, 'w') as f:
                    json.dump(self.metadata, f, indent=2)
            
            self.session_id = None
            self.session_path = None
    
    def record_frame(self, camera_frame: np.ndarray, lidar_data: Optional[Dict],
                     odom_data: Optional[Dict], timestamp: float, alert: bool = False):
        """Record a synchronized frame with all sensor data"""
        if not self.is_recording:
            return
        
        try:
            frame_id = f"frame_{self.frame_counter:08d}"
            frame_path = self.session_path / 'frames' / f"{frame_id}.jpg"
            
            # Save camera frame
            cv2.imwrite(str(frame_path), camera_frame, 
                       [cv2.IMWRITE_JPEG_QUALITY, self.config['streaming']['image_quality']])
            
            # Save LiDAR data if available
            lidar_path = None
            if lidar_data:
                lidar_path = self.session_path / 'lidar' / f"{frame_id}.json"
                with open(lidar_path, 'w') as f:
                    json.dump(lidar_data, f)
            
            # Create frame entry
            frame_entry = {
                'frame_id': frame_id,
                'timestamp': timestamp,
                'camera_frame': f"frames/{frame_id}.jpg",
                'lidar_data': f"lidar/{frame_id}.json" if lidar_path else None,
                'odom': odom_data,
                'alert': alert
            }
            
            # Add to metadata
            self.metadata['frames'].append(frame_entry)
            
            # Save alert if flagged
            if alert:
                self.metadata['alerts'].append({
                    'frame_id': frame_id,
                    'timestamp': timestamp,
                    'type': 'anomaly'
                })
            
            self.frame_counter += 1
            
            # Periodically save metadata (every 100 frames)
            if self.frame_counter % 100 == 0:
                self._save_metadata()
                
        except Exception as e:
            print(f"Error recording frame: {e}")
    
    def _save_metadata(self):
        """Save metadata to disk"""
        if self.metadata_file:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
    
    def get_session_info(self) -> Optional[Dict]:
        """Get information about current recording session"""
        if not self.is_recording:
            return None
        
        return {
            'session_id': self.session_id,
            'frame_count': self.frame_counter,
            'duration': time.time() - self.metadata['start_time'],
            'storage_path': str(self.session_path)
        }
    
    def list_sessions(self) -> list:
        """List all recorded sessions"""
        sessions = []
        for session_dir in sorted(self.storage_path.iterdir(), reverse=True):
            if session_dir.is_dir():
                metadata_file = session_dir / 'metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        sessions.append({
                            'session_id': metadata['session_id'],
                            'start_time': metadata['start_time'],
                            'end_time': metadata.get('end_time'),
                            'frame_count': len(metadata['frames']),
                            'path': str(session_dir)
                        })
                    except Exception as e:
                        print(f"Error reading session {session_dir}: {e}")
        return sessions
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load metadata for a specific session"""
        session_path = self.storage_path / session_id
        metadata_file = session_path / 'metadata.json'
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

