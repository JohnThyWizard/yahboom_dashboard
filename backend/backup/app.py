"""
FastAPI Backend - Main server for Yahboom Dashboard
"""
import rclpy
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import cv2
import json
import yaml
import asyncio
from pathlib import Path
import base64
from typing import Optional, Dict, Any
import threading
import time
import io
import os 

import numpy as np
from PIL import Image

# Local Imports (Assuming these are in the same directory structure)
from ros2_bridge import ROS2Bridge
from fast_recorder_integrated import FastRecorder, create_video_from_session
from camera_node import CameraNode 

# --- Global State ---
ros2_bridge: Optional[ROS2Bridge] = None
camera_node: Optional[CameraNode] = None
recorder: Optional[FastRecorder] = None
config: dict = {}
recording_fps: float = 10.0  
# Cache for the latest data sent over the WebSocket for Streamlit polling
latest_stream_cache: Dict[str, Any] = {}


# --- Helper Functions ---

def load_config():
    """Load configuration from YAML file (Requires a config/config.yaml file)"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    # Fallback to an empty dict if config file isn't found
    if not config_path.exists():
        print("Warning: config/config.yaml not found. Using default settings.")
        return {
            "camera": {"enabled": True, "video_source": 0, "fps": 15},
            "streaming": {"max_fps": 10.0, "image_quality": 85},
            "recording": {"storage_path": "recordings", "sync_interval_ms": 100}
        }

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_ros2():
    """Initialize ROS2 node and start executor in background thread"""
    global ros2_bridge, camera_node
    if not rclpy.ok():
        rclpy.init()
    
    # Initialize camera node if enabled
    if config.get('camera', {}).get('enabled', False):
        if camera_node is None:
            try:
                # CameraNode now takes the full config
                camera_node = CameraNode(config) 
            except Exception as e:
                print(f"Warning: Could not initialize camera node: {e}")
                camera_node = None
    
    # Initialize ROS2 bridge
    if ros2_bridge is None:
        ros2_bridge = ROS2Bridge(config)
        
        # Start ROS2 executor in background thread
        def spin_ros2():
            executor = rclpy.executors.SingleThreadedExecutor()
            executor.add_node(ros2_bridge)
            # Add camera node to executor if it exists
            if camera_node:
                executor.add_node(camera_node)
            try:
                executor.spin()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"ROS 2 Executor error: {e}")
        
        ros2_thread = threading.Thread(target=spin_ros2, daemon=True)
        ros2_thread.start()


# ❗ CRITICAL CHANGE: The conflicting 'async def recording_task()' function is removed.
# Recording is now handled inside the websocket_endpoint loop.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    global config, recorder
    config = load_config()
    
    # Initialize FastRecorder with storage path from config
    storage_path = config.get('recording', {}).get('storage_path', 'recordings')
    recorder = FastRecorder(storage_path=storage_path)
    print(f"[FastRecorder] Initialized with storage: {storage_path}")
    
    # Initialize ROS 2 bridge and nodes
    init_ros2()
    
    # ❗ CRITICAL CHANGE: Removed: recording_task_handle = asyncio.create_task(recording_task())
    
    print("FastAPI startup complete. ROS 2 and Recorder initialized.")
    yield
    
    # Shutdown
    # ❗ CRITICAL CHANGE: Removed cancellation for recording_task_handle
    
    global camera_node
    if camera_node:
        camera_node.stop_camera()
        camera_node.destroy_node()
    if ros2_bridge:
        ros2_bridge.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
    
    print("FastAPI shutdown complete.")


app = FastAPI(title="Yahboom Dashboard API", lifespan=lifespan)

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Endpoints ---

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "yahboom_dashboard"}


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    recording_info = recorder.get_recording_status() if recorder else None

    # Use peek properties for status checks
    cam_active = ros2_bridge.latest_camera_frame is not None if ros2_bridge else False
    lidar_active = ros2_bridge.latest_lidar_data is not None if ros2_bridge else False
    map_active = ros2_bridge.latest_map is not None if ros2_bridge else False
    
    return {
        "ros2_connected": ros2_bridge is not None,
        "recording": recorder.is_recording if recorder else False,
        "recording_session": recording_info,
        "camera_available": cam_active,
        "lidar_available": lidar_active,
        "map_available": map_active
    }


# The original /api/camera/latest, /api/lidar/latest, /api/odom/latest are now redundant 
# for the Streamlit frontend because of the new /api/latest_stream_data endpoint, 
# but we keep them for direct API access and to match the template structure.

@app.get("/api/camera/latest")
async def get_latest_camera():
    """Get latest camera frame as JPEG"""
    if not ros2_bridge:
        return JSONResponse({"error": "ROS2 not initialized"}, status_code=503)
    
    # Use get_latest_camera_frame() which clears the frame
    frame, timestamp = ros2_bridge.get_latest_camera_frame() 
    if frame is None:
        return JSONResponse({"error": "No camera data available"}, status_code=404)
    
    # Encode as JPEG
    quality = config.get('streaming', {}).get('image_quality', 85)
    _, buffer = cv2.imencode('.jpg', frame, 
                            [cv2.IMWRITE_JPEG_QUALITY, quality])
    
    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg",
        headers={"X-Timestamp": str(timestamp)}
    )

# ... (other REST endpoints like /api/lidar/latest, /api/map/latest, /api/odom/latest remain as in your template) ...

@app.get("/api/map/latest")
async def get_latest_map():
    """Get latest occupancy grid map rendered as PNG"""
    if not ros2_bridge:
        return JSONResponse({"error": "ROS2 not initialized"}, status_code=503)
    
    map_data = ros2_bridge.get_latest_map()
    if map_data is None:
        return JSONResponse({"error": "No map data available"}, status_code=404)
    
    try:
        width = map_data['width']
        height = map_data['height']
        # Ensure data is treated as numpy array
        data = np.array(map_data['data'], dtype=np.int8) 
        if data.size != width * height:
            return JSONResponse({"error": "Invalid map data size"}, status_code=500)
        
        grid = data.reshape((height, width))
        
        # Create RGB image: free (0) -> white, occupied (> 50) -> black, unknown (-1) -> gray
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:] = (127, 127, 127)  # Unknown default (Gray)
        
        free_mask = grid == 0
        occ_mask = grid > 50
        
        image[free_mask] = (220, 220, 220) # White/Light Gray
        image[occ_mask] = (0, 0, 0) # Black
        
        # Flip vertically so origin matches typical SLAM conventions
        image = np.flipud(image)
        
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "map": {
                "width": width,
                "height": height,
                "resolution": map_data.get("resolution"),
                "origin": map_data.get("origin"),
                "timestamp": map_data.get("timestamp"),
                "image": encoded
            }
        }
    except Exception as e:
        return JSONResponse({"error": f"Map processing error: {str(e)}"}, status_code=500)


# --- Recording Endpoints ---

@app.post("/api/recording/start")
async def start_recording():
    """Start recording session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    session_id = recorder.start_recording() 
    return {"session_id": session_id, "status": "recording"}


@app.post("/api/recording/stop")
async def stop_recording():
    """Stop recording session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    if not recorder.is_recording:
        return JSONResponse({"error": "Not recording"}, status_code=400)
    
    summary = recorder.stop_recording()
    return summary


@app.get("/api/recording/status")
async def get_recording_status():
    """Get current recording status"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    return recorder.get_recording_status()


@app.get("/api/recording/sessions")
async def get_sessions():
    """Get list of all recorded sessions"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    sessions = recorder.get_sessions()
    return {"sessions": sessions}


@app.get("/api/recording/session/{session_id}")
async def get_session(session_id: str):
    """Get metadata for a specific session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    metadata = recorder.get_session_metadata(session_id)
    
    if not metadata:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    return metadata


@app.post("/api/recording/alert")
async def add_alert(alert_data: dict):
    """Add alert to current recording"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    if not recorder.is_recording:
        return JSONResponse({"error": "Not recording"}, status_code=400)
    
    try:
        alert = recorder.add_alert(
            alert_type=alert_data.get('type', 'manual'),
            description=alert_data.get('description', ''),
            metadata=alert_data.get('metadata', {})
        )
        return {"success": True, "alert": alert}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/recording/session/{session_id}/alerts")
async def get_session_alerts(session_id: str):
    """Get alerts for a session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    metadata = recorder.get_session_metadata(session_id)
    
    if not metadata:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    return {"alerts": metadata.get('alerts', [])}


@app.post("/api/recording/session/{session_id}/create_video")
async def create_session_video(session_id: str, video_params: dict = None):
    """Create video from session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    if video_params is None:
        video_params = {}
    
    fps = video_params.get('fps', 30.0)
    output_name = video_params.get('output_name')
    
    try:
        create_video_from_session(
            session_id=session_id,
            storage_path=str(recorder.storage_path),
            output_name=output_name,
            fps=fps
        )
        return {"success": True, "session_id": session_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/recording/session/{session_id}/frame/{frame_id}")
async def get_frame(session_id: str, frame_id: str):
    """Get a specific frame from a session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    try:
        frame_number = int(frame_id)
        frame = recorder.get_frame(session_id, frame_number)
        
        if frame is None:
            return JSONResponse({"error": "Frame not found"}, status_code=404)
        
        _, buffer = cv2.imencode('.jpg', frame)
        
        return StreamingResponse(
            iter([buffer.tobytes()]),
            media_type="image/jpeg"
        )
    except ValueError:
        return JSONResponse({"error": "Invalid frame ID"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/recording/session/{session_id}/frame/{frame_id}/metadata")
async def get_frame_metadata(session_id: str, frame_id: str):
    """Get metadata for a specific frame"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    try:
        frame_number = int(frame_id)
        metadata = recorder.get_frame_metadata(session_id, frame_number)
        
        if metadata is None:
            return JSONResponse({"error": "Metadata not found"}, status_code=404)
        
        return metadata
    except ValueError:
        return JSONResponse({"error": "Invalid frame ID"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/recording/session/{session_id}/lidar/{frame_id}")
async def get_lidar_from_session(session_id: str, frame_id: str):
    """Get LiDAR data for a specific frame from a session"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)

    lidar_path = recorder.get_sensor_data_file_path(session_id, frame_id)
    
    if not lidar_path or not os.path.exists(lidar_path):
        return JSONResponse({"error": "LiDAR data not found"}, status_code=404)
    
    try:
        with open(lidar_path, 'r') as f:
            lidar_data = json.load(f)
        return lidar_data
    except Exception as e:
        return JSONResponse({"error": f"Error reading LiDAR data: {str(e)}"}, status_code=500)


# --- Streamlit Polling Endpoint (CRITICAL for Streamlit Frontend) ---

@app.get("/api/latest_stream_data")
async def get_latest_stream_data_endpoint():
    """Endpoint for Streamlit frontend to poll the latest stream data directly from ROS2.
    
    ✅ FIXED: This endpoint now reads directly from ros2_bridge instead of relying on
    the WebSocket cache (which was never populated because no WebSocket client connects).
    """
    global ros2_bridge, recorder, config
    
    if not ros2_bridge:
        return {
            "type": "frame",
            "camera": {"data": None, "timestamp": None},
            "lidar": None,
            "odom": None,
            "recording": False
        }
    
    # ✅ CRITICAL FIX: Read data DIRECTLY from ros2_bridge
    frame, timestamp = ros2_bridge.get_latest_camera_frame()
    lidar_data, _ = ros2_bridge.get_latest_lidar_data()
    odom_data, _ = ros2_bridge.get_latest_odom()
    
    # Record frame if recording is active
    if recorder and recorder.is_recording and frame is not None:
        recorder.record_frame(frame, metadata={
            'timestamp': timestamp,
            'lidar': lidar_data,
            'odom': odom_data
        })
    
    # Encode frame to base64
    frame_b64 = None
    if frame is not None:
        quality = config.get('streaming', {}).get('image_quality', 60)
        if frame.size > 0:
            is_success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if is_success:
                frame_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
    
    return {
        "type": "frame",
        "camera": {
            "data": frame_b64,
            "timestamp": timestamp
        },
        "lidar": lidar_data,
        "odom": odom_data,
        "recording": recorder.is_recording if recorder else False
    }


# --- WebSocket Endpoint (Main Data Stream) ---

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming and Streamlit cache updates."""
    await websocket.accept()
    global ros2_bridge, recorder, latest_stream_cache
    
    if not ros2_bridge:
        await websocket.close(code=1011, reason="ROS2 Bridge not initialized")
        return

    try:
        while True:
            # 1. Get ALL latest data (CRITICAL: Called only once per loop)
            # This consumes the frame from the ROS2 buffer for all purposes.
            frame, timestamp = ros2_bridge.get_latest_camera_frame()
            lidar_data, _ = ros2_bridge.get_latest_lidar_data()
            odom_data, _ = ros2_bridge.get_latest_odom()

            # --- Encoding and Frame Caching ---
            frame_b64 = None
            if frame is not None:
                # Encode frame 
                quality = config.get('streaming', {}).get('image_quality', 85)
                # Ensure frame is not empty before encoding (robustness check)
                if frame.size > 0:
                    is_success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                    if is_success:
                        frame_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            
            # 2. Prepare message (ALWAYS prepare a message, even if data is None)
            message = {
                "type": "frame",
                "camera": {
                    "data": frame_b64,  # This will be None if the camera failed
                    "timestamp": timestamp
                },
                "lidar": lidar_data,
                "odom": odom_data,
                "recording": recorder.is_recording if recorder else False
            }
            
            # 3. Update the stream cache (CRITICAL for Streamlit's /api/latest_stream_data polling)
            latest_stream_cache = message
            
            # 4. Send the message to WebSocket clients (if any are connected)
            await websocket.send_json(message)

            # 5. Record frame (using the SAME frame retrieved in step 1)
            if recorder and recorder.is_recording and ros2_bridge:
                if frame is not None:
                    recorder.record_frame(frame, lidar_data, odom_data, timestamp)
            
            # 6. Control loop rate
            max_fps = config.get('streaming', {}).get('max_fps', 10.0)
            await asyncio.sleep(1.0 / max_fps)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    # Use the application object initialized with lifespan
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
