"""
FastAPI Backend - Main server for Yahboom Dashboard
"""
import rclpy
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import json
import yaml
import asyncio
from pathlib import Path
import base64
from typing import Optional
import threading
import time

from ros2_bridge import ROS2Bridge
from recorder import DataRecorder

app = FastAPI(title="Yahboom Dashboard API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
ros2_bridge: Optional[ROS2Bridge] = None
recorder: Optional[DataRecorder] = None
config: dict = {}


def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_ros2():
    """Initialize ROS2 node"""
    global ros2_bridge
    if not rclpy.ok():
        rclpy.init()
    
    if ros2_bridge is None:
        ros2_bridge = ROS2Bridge(config)
        
        # Start ROS2 executor in background thread
        def spin_ros2():
            executor = rclpy.executors.SingleThreadedExecutor()
            executor.add_node(ros2_bridge)
            try:
                executor.spin()
            except KeyboardInterrupt:
                pass
        
        ros2_thread = threading.Thread(target=spin_ros2, daemon=True)
        ros2_thread.start()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global config, recorder
    config = load_config()
    recorder = DataRecorder(
        config['recording']['storage_path'],
        config
    )
    init_ros2()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "yahboom_dashboard"}


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    recording_info = recorder.get_session_info() if recorder else None
    
    return {
        "ros2_connected": ros2_bridge is not None,
        "recording": recorder.is_recording if recorder else False,
        "recording_session": recording_info,
        "camera_available": ros2_bridge.latest_camera_frame is not None if ros2_bridge else False,
        "lidar_available": ros2_bridge.latest_lidar_data is not None if ros2_bridge else False
    }


@app.get("/api/camera/latest")
async def get_latest_camera():
    """Get latest camera frame as JPEG"""
    if not ros2_bridge:
        return JSONResponse({"error": "ROS2 not initialized"}, status_code=503)
    
    frame, timestamp = ros2_bridge.get_latest_camera_frame()
    if frame is None:
        return JSONResponse({"error": "No camera data available"}, status_code=404)
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame, 
                            [cv2.IMWRITE_JPEG_QUALITY, config['streaming']['image_quality']])
    
    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg",
        headers={"X-Timestamp": str(timestamp)}
    )


@app.get("/api/lidar/latest")
async def get_latest_lidar():
    """Get latest LiDAR data"""
    if not ros2_bridge:
        return JSONResponse({"error": "ROS2 not initialized"}, status_code=503)
    
    lidar_data, timestamp = ros2_bridge.get_latest_lidar_data()
    if lidar_data is None:
        return JSONResponse({"error": "No LiDAR data available"}, status_code=404)
    
    return {
        "data": lidar_data,
        "timestamp": timestamp
    }


@app.get("/api/odom/latest")
async def get_latest_odom():
    """Get latest odometry data"""
    if not ros2_bridge:
        return JSONResponse({"error": "ROS2 not initialized"}, status_code=503)
    
    odom_data, timestamp = ros2_bridge.get_latest_odom()
    if odom_data is None:
        return JSONResponse({"error": "No odometry data available"}, status_code=404)
    
    return {
        "data": odom_data,
        "timestamp": timestamp
    }


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
    
    recorder.stop_recording()
    return {"status": "stopped"}


@app.get("/api/recording/sessions")
async def list_sessions():
    """List all recording sessions"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    sessions = recorder.list_sessions()
    return {"sessions": sessions}


@app.get("/api/recording/session/{session_id}")
async def get_session(session_id: str):
    """Get session metadata"""
    if not recorder:
        return JSONResponse({"error": "Recorder not initialized"}, status_code=503)
    
    session_data = recorder.load_session(session_id)
    if session_data is None:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    return session_data


@app.get("/api/recording/session/{session_id}/frame/{frame_id}")
async def get_frame(session_id: str, frame_id: str):
    """Get a specific frame from a session"""
    session_path = Path(config['recording']['storage_path']) / session_id / 'frames' / f"{frame_id}.jpg"
    
    if not session_path.exists():
        return JSONResponse({"error": "Frame not found"}, status_code=404)
    
    frame = cv2.imread(str(session_path))
    _, buffer = cv2.imencode('.jpg', frame)
    
    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg"
    )


@app.get("/api/recording/session/{session_id}/lidar/{frame_id}")
async def get_lidar_from_session(session_id: str, frame_id: str):
    """Get LiDAR data for a specific frame from a session"""
    lidar_path = Path(config['recording']['storage_path']) / session_id / 'lidar' / f"{frame_id}.json"
    
    if not lidar_path.exists():
        return JSONResponse({"error": "LiDAR data not found"}, status_code=404)
    
    try:
        with open(lidar_path, 'r') as f:
            lidar_data = json.load(f)
        return {"data": lidar_data}
    except Exception as e:
        return JSONResponse({"error": f"Error reading LiDAR data: {str(e)}"}, status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await websocket.accept()
    
    try:
        while True:
            # Send latest camera frame
            if ros2_bridge:
                frame, timestamp = ros2_bridge.get_latest_camera_frame()
                lidar_data, lidar_ts = ros2_bridge.get_latest_lidar_data()
                odom_data, odom_ts = ros2_bridge.get_latest_odom()
                
                if frame is not None:
                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Prepare message
                    message = {
                        "type": "frame",
                        "camera": {
                            "data": frame_b64,
                            "timestamp": timestamp
                        },
                        "lidar": lidar_data,
                        "odom": odom_data,
                        "recording": recorder.is_recording if recorder else False
                    }
                    
                    await websocket.send_json(message)
            
            # Record frame if recording
            if recorder and recorder.is_recording and ros2_bridge:
                frame, timestamp = ros2_bridge.get_latest_camera_frame()
                lidar_data, _ = ros2_bridge.get_latest_lidar_data()
                odom_data, _ = ros2_bridge.get_latest_odom()
                
                if frame is not None:
                    recorder.record_frame(frame, lidar_data, odom_data, timestamp)
            
            await asyncio.sleep(1.0 / config['streaming']['max_fps'])
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

