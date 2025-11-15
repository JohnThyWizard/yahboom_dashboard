import os
import time
import json
import numpy as np
import cv2
from datetime import datetime
from typing import Optional, Dict, Any, List

class DataRecorder:
    """Manages recording session state and saves frames/data."""

    def __init__(self, base_dir: str = "recordings", config: Optional[Dict] = None):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self._is_recording = False
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[float] = None
        self.frame_count = 0
        self.session_path: Optional[str] = None
        self.session_metadata: Dict[str, Any] = {}
        # Configuration is stored but not actively used in this simple implementation
        self.config = config if config is not None else {}

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start_recording(self) -> Optional[str]:
        if self._is_recording:
            return self.current_session_id

        self.session_start_time = time.time()
        # Create a unique session ID based on timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = f"session_{timestamp_str}"
        
        # Structure: <base_dir>/<session_id>/
        #   - metadata.json
        #   - frames/frame_00000.jpg
        #   - sensor_data/frame_00000.json
        self.session_path = os.path.join(self.base_dir, self.current_session_id)
        self.frames_path = os.path.join(self.session_path, "frames")
        self.sensor_path = os.path.join(self.session_path, "sensor_data")
        
        os.makedirs(self.frames_path, exist_ok=True)
        os.makedirs(self.sensor_path, exist_ok=True)

        self.frame_count = 0
        self.session_metadata = {
            "session_id": self.current_session_id,
            "start_time": self.session_start_time,
            "end_time": None,
            "frame_count": 0,
            "frames": []
        }
        
        self._is_recording = True
        return self.current_session_id

    def stop_recording(self) -> bool:
        if not self._is_recording:
            return True

        self.session_metadata["end_time"] = time.time()
        self.session_metadata["frame_count"] = self.frame_count
        
        # Save metadata file
        metadata_path = os.path.join(self.session_path, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.session_metadata, f, indent=4)
            
        self._is_recording = False
        self.current_session_id = None
        return True

    def record_frame(self, frame: np.ndarray, lidar_data: Optional[Dict], odom_data: Optional[Dict], timestamp: float):
        if not self._is_recording or frame is None:
            return

        # Ensure paths are set
        if not self.frames_path or not self.sensor_path:
            return

        frame_id = f"frame_{self.frame_count:05d}"
        
        # 1. Save Camera Frame (JPEG)
        frame_filename = os.path.join(self.frames_path, f"{frame_id}.jpg")
        cv2.imwrite(frame_filename, frame) 

        # 2. Save Sensor Data (JSON)
        sensor_data = {
            "timestamp": timestamp,
            "lidar": lidar_data,
            "odom": odom_data,
        }
        sensor_filename = os.path.join(self.sensor_path, f"{frame_id}.json")
        with open(sensor_filename, 'w') as f:
            json.dump(sensor_data, f, indent=4)

        # 3. Update Session Metadata
        self.session_metadata["frames"].append({
            "frame_id": frame_id,
            "timestamp": timestamp,
            "filename": os.path.relpath(frame_filename, self.session_path), # Store relative path
        })
        
        self.frame_count += 1
        
    def get_session_info(self) -> Dict:
        """Returns metadata for the current session."""
        if self._is_recording:
            duration = time.time() - self.session_start_time
            return {
                "session_id": self.current_session_id,
                "frame_count": self.frame_count,
                "duration": duration
            }
        return {}

    def list_sessions(self) -> List[Dict]:
        """Lists all recorded sessions with summary info."""
        sessions = []
        for item in os.listdir(self.base_dir):
            session_path = os.path.join(self.base_dir, item)
            if os.path.isdir(session_path) and item.startswith("session_"):
                metadata_path = os.path.join(session_path, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            sessions.append({
                                "session_id": metadata["session_id"],
                                "start_time": metadata["start_time"],
                                "frame_count": metadata.get("frame_count", len(metadata["frames"])),
                                "duration": metadata.get("end_time", time.time()) - metadata["start_time"],
                            })
                    except Exception:
                        pass
        return sessions

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Loads full metadata for a specific session."""
        session_path = os.path.join(self.base_dir, session_id)
        metadata_path = os.path.join(session_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None

    # Helper for the API to fetch files from the new structure
    def get_frame_file_path(self, session_id: str, frame_id: str) -> Optional[str]:
        """Gets the file path for a specific camera frame."""
        file_path = os.path.join(self.base_dir, session_id, "frames", f"{frame_id}.jpg")
        return file_path if os.path.exists(file_path) else None

    def get_sensor_data_file_path(self, session_id: str, frame_id: str) -> Optional[str]:
        """Gets the file path for sensor data."""
        file_path = os.path.join(self.base_dir, session_id, "sensor_data", f"{frame_id}.json")
        return file_path if os.path.exists(file_path) else None