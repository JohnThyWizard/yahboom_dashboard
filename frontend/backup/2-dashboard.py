"""
Yahboom Dashboard - Streamlit Frontend
Real-Time Robotic Control & Replay System
"""
# IMPORTANT: Configure logging BEFORE importing Streamlit
import logging
import warnings
import sys

# Suppress Streamlit media file storage warnings (harmless cache lookup errors)
logging.getLogger('streamlit.runtime.media_file_storage').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.web.server.media_file_handler').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime').setLevel(logging.ERROR)
logging.getLogger('streamlit.web').setLevel(logging.ERROR)
logging.getLogger('streamlit').setLevel(logging.ERROR)

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Create a filter to suppress MediaFileStorageError messages
class MediaFileErrorFilter(logging.Filter):
    def filter(self, record):
        try:
            msg = str(record.getMessage())
            return not any([
                'MediaFileStorageError' in msg,
                'media_file_storage' in msg.lower(),
                'media_file_handler' in msg.lower(),
                'Bad filename' in msg,
                'Missing file' in msg,
                ('KeyError' in msg and 'media' in msg.lower())
            ])
        except:
            return True

# Apply filter to all relevant loggers
for logger_name in ['streamlit', 'streamlit.runtime', 'streamlit.web', 'root']:
    logger = logging.getLogger(logger_name if logger_name != 'root' else '')
    logger.addFilter(MediaFileErrorFilter())
    if logger_name != 'root':
        logger.setLevel(logging.ERROR)

# Now import Streamlit and other modules
import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from PIL import Image
import io
import base64

# Configuration
BACKEND_URL = "http://localhost:8000"
REFRESH_INTERVAL = 0.033  # 33ms for smooth updates (30 FPS) - Optimized from 0.1

# Page configuration
st.set_page_config(
    page_title="Yahboom Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark technical theme and stability fix
st.markdown("""
<style>
    /* Dark theme styling */
    .main {
        background-color: #0a0e27;
        color: #e0e0e0;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    /* Camera feed container styling */
    div[data-testid="column"] {
        background-color: rgba(10, 14, 39, 0.8);
        border-radius: 8px;
    }
    
    /* Image container with cyan border */
    div[data-testid="stImage"] {
        border: 2px solid #00ffff;
        border-radius: 8px;
        padding: 10px;
        background-color: rgba(0, 0, 0, 0.3);
        max-height: 540px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Actual image styling - contained within border */
    div[data-testid="stImage"] > img {
        max-height: 500px;
        max-width: 100%;
        width: auto !important;
        height: auto !important;
        object-fit: contain;
        display: block;
        margin: 0 auto;
    }
    
    /* Warning/error messages */
    .stWarning, .stError {
        text-align: center;
        padding: 20px;
        border-radius: 8px;
    }
    
    /* LiDAR/SLAM container with red outline */
    div[data-testid="stVerticalBlock"]:has(div[data-testid="stPlotlyChart"]) {
        border: 2px solid #ff0000;
        border-radius: 8px;
        padding: 10px;
        background-color: rgba(0, 0, 0, 0.3);
    }
    
    /* Plotly chart container styling */
    div[data-testid="stPlotlyChart"] {
        border-radius: 4px;
    }
    
    /* Tabs styling for LiDAR/SLAM */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 0, 0, 0.2);
        border-bottom: 2px solid #ff0000;
    }
</style>
""", unsafe_allow_html=True)

## Live Data Streaming Functions

def get_latest_stream_data() -> Optional[Dict]:
    """
    Get the latest aggregated data (camera, lidar, odom, status) from the backend's
    internal stream buffer via the polling endpoint.
    """
    try:
        # Uses the new polling endpoint added to app.py
        response = requests.get(f"{BACKEND_URL}/api/latest_stream_data", timeout=0.5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        # Silently fail for fast polling
        pass
    return None

def process_camera_data(camera_data: Dict) -> Optional[np.ndarray]:
    """
    Process base64 image data from the aggregated stream message into a numpy array.
    """
    if camera_data and 'data' in camera_data and camera_data['data'] is not None:
        try:
            image_bytes = base64.b64decode(camera_data["data"])
            img = Image.open(io.BytesIO(image_bytes))
            # Convert PIL Image to numpy array (RGB format)
            img_array = np.array(img)
            # Ensure it's RGB
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            return img_array
        except Exception:
            pass
    return None

# The rest of the API/Helper functions (get_status, start_recording, visualize_lidar, etc.) 
# remain the same as they correctly target the FastAPI REST endpoints.

def check_backend_connection() -> bool:
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/status", timeout=2) 
        return response.status_code == 200
    except:
        return False

def get_status() -> Optional[Dict]:
    """Get system status from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def start_recording() -> bool:
    """Start recording session"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/recording/start", timeout=2)
        return response.status_code == 200
    except:
        return False


def stop_recording() -> bool:
    """Stop recording session"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/recording/stop", timeout=2)
        return response.status_code == 200
    except:
        return False


def list_recording_sessions() -> list:
    """List all recording sessions"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recording/sessions", timeout=2)
        if response.status_code == 200:
            return response.json().get('sessions', [])
    except:
        pass
    return []


def get_session_data(session_id: str) -> Optional[Dict]:
    """Get session metadata"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recording/session/{session_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_frame_from_session(session_id: str, frame_id: str) -> Optional[np.ndarray]:
    """Get a specific frame from a session as numpy array (Replay mode)"""
    try:
        # This endpoint returns raw image bytes
        response = requests.get(f"{BACKEND_URL}/api/recording/session/{session_id}/frame/{frame_id}", timeout=5)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_array = np.array(img)
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            return img_array
        if response.status_code == 404:
            return None
    except Exception:
        pass
    return None


def get_lidar_from_session(session_id: str, frame_id: str) -> Optional[Dict]:
    """Get LiDAR data for a specific frame from a session (Replay mode)"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recording/session/{session_id}/lidar/{frame_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_latest_map_image() -> Optional[Dict[str, Any]]:
    """Get latest SLAM map image and metadata from backend (retained as it's a separate entity)."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/map/latest", timeout=2)
        if response.status_code == 200:
            payload = response.json()
            map_payload = payload.get("map")
            if map_payload and map_payload.get("image"):
                image_bytes = base64.b64decode(map_payload["image"])
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                map_payload["image_object"] = image
                return map_payload
    except:
        pass
    return None

def visualize_lidar(lidar_data: Dict) -> go.Figure:
    """Create LiDAR visualization"""
    if not lidar_data or 'ranges' not in lidar_data or not lidar_data['ranges']:
        return None
    
    data = lidar_data
    ranges = np.array(data.get('ranges', []))
    angles = np.array(data.get('angles', []))
    
    # Filter invalid ranges
    valid_mask = (ranges > data.get('range_min', 0)) & (ranges < data.get('range_max', 30))
    
    # Apply filter to both arrays
    angles = angles[valid_mask]
    ranges = ranges[valid_mask]

    
    # Convert to Cartesian
    x = ranges * np.cos(angles)
    y = ranges * np.sin(angles)
    
    # Create scatter plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=3,
            color=ranges,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Range (m)")
        ),
        name='LiDAR Scan'
    ))
    
    # Add robot position (origin)
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(size=15, color='cyan', symbol='circle'),
        name='Robot'
    ))
    
    fig.update_layout(
        title="LiDAR Scan Visualization",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        template="plotly_dark",
        height=500,
        showlegend=True,
        plot_bgcolor='#0a0e27',
        paper_bgcolor='#0a0e27',
        font=dict(color='#e0e0e0')
    )
    
    # Set equal aspect ratio
    fig.update_xaxes(scaleanchor="y", scaleratio=1, range=[-3, 3])
    fig.update_yaxes(range=[-3, 3])
    
    return fig


def visualize_odom(odom_data: Dict) -> Dict[str, float]:
    """Extract odometry metrics"""
    if not odom_data or 'position' not in odom_data:
        return {}
    
    # Data is expected to be under 'data' key if fetched via API. 
    # Since it's from stream_data, it's the raw dictionary.
    data = odom_data 
    pos = data.get('position', {})
    vel = data.get('linear_velocity', {})
    
    # Assuming z-rotation (yaw) is not available in the simple odom data, 
    # but still calculate position and speed.
    
    return {
        'x': pos.get('x', 0),
        'y': pos.get('y', 0),
        'z': pos.get('z', 0),
        'vx': vel.get('x', 0),
        'vy': vel.get('y', 0),
        'speed': np.sqrt(vel.get('x', 0)**2 + vel.get('y', 0)**2)
    }

# Initialize session state (retained from previous iteration)
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'playback_mode' not in st.session_state:
    st.session_state.playback_mode = False
if 'selected_session' not in st.session_state:
    st.session_state.selected_session = None
if 'current_frame_idx' not in st.session_state:
    st.session_state.current_frame_idx = 0
if 'camera_enabled' not in st.session_state:
    st.session_state.camera_enabled = True
if 'lidar_enabled' not in st.session_state:
    st.session_state.lidar_enabled = True
if 'cached_session_data' not in st.session_state:
    st.session_state.cached_session_data = {}
if 'last_loaded_frame' not in st.session_state:
    st.session_state.last_loaded_frame = None
if 'cached_frames' not in st.session_state:
    st.session_state.cached_frames = {}
if 'failed_frames' not in st.session_state:
    st.session_state.failed_frames = set()
if 'enable_frame_cache' not in st.session_state:
    st.session_state.enable_frame_cache = False


# Main dashboard
st.title("🤖 Yahboom Dashboard")
st.markdown("---")

# Sidebar controls
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Backend status
    backend_connected = check_backend_connection()
    status_icon = "🟢" if backend_connected else "🔴"
    st.markdown(f"**Backend Status:** {status_icon} {'Connected' if backend_connected else 'Disconnected'}")
    
    if not backend_connected:
        st.error("⚠️ Cannot connect to backend. Please ensure the FastAPI server is running.")
        st.stop()
    
    # Get system status
    status = get_status()
    
    # Recording controls
    st.subheader("📹 Recording")
    recording_status = status.get('recording', False) if status else False
    status_indicator = "🟢" if recording_status else "🟡"
    st.markdown(f"**Status:** {status_indicator} {'Recording' if recording_status else 'Idle'}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start", disabled=recording_status, use_container_width=True):
            if start_recording():
                st.success("Recording started")
                st.rerun()
    
    with col2:
        if st.button("⏹️ Stop", disabled=not recording_status, use_container_width=True):
            if stop_recording():
                st.success("Recording stopped")
                st.rerun()
    
    # Display mode
    st.subheader("🎬 Display Mode")
    display_mode = st.radio(
        "Mode",
        ["Live", "Replay"],
        index=0 if not st.session_state.playback_mode else 1,
        label_visibility="collapsed"
    )
    st.session_state.playback_mode = (display_mode == "Replay")
    
    # Stream controls
    st.subheader("📡 Stream Controls")
    st.session_state.camera_enabled = st.checkbox("📷 Camera Feed", value=st.session_state.camera_enabled)
    st.session_state.lidar_enabled = st.checkbox("📡 LiDAR/SLAM Map", value=st.session_state.lidar_enabled)
    
    # System metrics
    if status:
        st.subheader("📊 System Metrics")
        # Note: Status check is now based on active topics, not just 'is_connected'
        st.metric("ROS2", "🟢 Active" if status.get('ros2_connected') else "🔴 Inactive")
        st.metric("Camera", "🟢 Active" if status.get('camera_available') else "🔴 Inactive")
        st.metric("LiDAR", "🟢 Active" if status.get('lidar_available') else "🔴 Inactive")
        st.metric("Map", "🟢 Active" if status.get('map_available') else "🔴 Inactive")
        
        if recording_status and status.get('recording_session'):
            session_info = status['recording_session']
            st.metric("Frames Recorded", f"{session_info.get('frame_count', 0):,}")
            duration = session_info.get('duration', 0)
            st.metric("Duration", f"{duration:.1f}s")


# Main content area
if st.session_state.playback_mode:
    # --- Replay Mode (Retained) ---
    st.header("📼 Replay Mode")
    
    # ... (Replay logic remains the same) ...
    
    # Simplified Replay Logic Placeholder (Full code should be used)
    sessions = list_recording_sessions()

    # ⭐ ADD THE PRINT STATEMENT HERE ⭐
    print(f"DEBUG: Sessions data returned by API: {sessions}", file=sys.stderr)

    if sessions:
        # FIX: Use 'sessions' variable and keys 'session_id', 'total_frames', and 'duration'
        session_options = {s['session_id']: f"{s['session_id']} ({s.get('total_frames', 0)} frames, {s.get('duration', 0):.1f}s)"
                           for s in sessions}
        selected_session_id = st.selectbox(
            "Select Recording Session",
            options=list(session_options.keys()),
            format_func=lambda x: session_options[x]
        )
        
        if selected_session_id:
            cache_key = f"session_{selected_session_id}"
            if cache_key not in st.session_state.cached_session_data:
                session_data = get_session_data(selected_session_id)
                st.session_state.cached_session_data[cache_key] = session_data
            else:
                session_data = st.session_state.cached_session_data[cache_key]
            
            if st.session_state.selected_session != selected_session_id:
                st.session_state.current_frame_idx = 0
                st.session_state.selected_session = selected_session_id
                st.session_state.last_loaded_frame = None
                st.session_state.cached_frames = {}
                st.session_state.failed_frames = set()
            
            if session_data and 'frames' in session_data:
                frames = session_data['frames']
                
                if frames:
                    st.subheader("⏱️ Timeline")
                    max_idx = len(frames) - 1
                    
                    col_reset, col_cache, col_info = st.columns([1, 1, 2])
                    with col_reset:
                        if st.button("🔄 Reset", help="Reset to first frame and clear cache"):
                            st.session_state.current_frame_idx = 0
                            st.session_state.last_loaded_frame = None
                            st.session_state.cached_frames = {}
                            st.session_state.failed_frames = set()
                            st.rerun()
                    with col_cache:
                        st.session_state.enable_frame_cache = st.checkbox(
                            "💾 Cache Frames", 
                            value=st.session_state.enable_frame_cache,
                            help="Enable frame caching (uses more memory but faster navigation)"
                        )
                    
                    frame_idx = st.slider(
                        "Frame",
                        0,
                        max_idx,
                        value=st.session_state.current_frame_idx,
                        key="frame_slider"
                    )
                    st.session_state.current_frame_idx = frame_idx
                    
                    current_frame = frames[frame_idx]
                    frame_time = datetime.fromtimestamp(current_frame['timestamp'])
                    st.markdown(f"**Timestamp:** `{frame_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}` | **Frame:** {frame_idx + 1}/{len(frames)}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.session_state.camera_enabled:
                            st.subheader("📷 Camera Feed")
                            frame_id = current_frame['frame_id']
                            camera_placeholder = st.empty()
                            
                            frame_cache_key = f"{selected_session_id}_{frame_id}"
                            frame_img = None
                            
                            if st.session_state.enable_frame_cache and frame_cache_key in st.session_state.cached_frames:
                                frame_img = st.session_state.cached_frames[frame_cache_key]
                            
                            if frame_img is None:
                                if frame_cache_key not in st.session_state.failed_frames:
                                    try:
                                        frame_img = get_frame_from_session(selected_session_id, frame_id)
                                        if frame_img is not None:
                                            if st.session_state.enable_frame_cache:
                                                st.session_state.cached_frames[frame_cache_key] = frame_img
                                            st.session_state.failed_frames.discard(frame_cache_key)
                                        else:
                                            st.session_state.failed_frames.add(frame_cache_key)
                                    except Exception:
                                        st.session_state.failed_frames.add(frame_cache_key)
                            
                            if frame_img is not None:
                                camera_placeholder.image(frame_img, use_container_width=True)
                            else:
                                camera_placeholder.warning(f"⚠️ Frame {frame_id} not available or failed to load")
                        else:
                            st.info("Camera feed disabled")
                    
                    with col2:
                        if st.session_state.lidar_enabled:
                            st.subheader("📡 LiDAR/SLAM Map")
                            lidar_placeholder = st.empty()
                            
                            try:
                                frame_id = current_frame['frame_id']
                                lidar_data = get_lidar_from_session(selected_session_id, frame_id)
                                if lidar_data:
                                    fig = visualize_lidar(lidar_data)
                                    if fig:
                                        lidar_placeholder.plotly_chart(fig, use_container_width=True)
                                    else:
                                        lidar_placeholder.warning("Could not visualize LiDAR data")
                                else:
                                    lidar_placeholder.warning("No LiDAR data for this frame")
                            except Exception:
                                lidar_placeholder.error("Error loading LiDAR data")
                        else:
                            st.info("LiDAR map disabled")
                else:
                    st.warning("No frames in this session")
            else:
                st.error("Could not load session data")
    else:
        st.info("No recording sessions available. Start recording to create sessions.")

else:
    # --- Live Mode (Updated for Polling and Stability) ---
    st.header("🔴 Live Monitoring")
    
    # Fetch aggregated stream data once per rerun
    stream_data = get_latest_stream_data()
    
    # Extract components
    camera_data = stream_data.get('camera', {}) if stream_data else {}
    lidar_data = stream_data.get('lidar', {}) if stream_data else {}
    odom_data = stream_data.get('odom', {}) if stream_data else {}
    
    # Status bar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        is_recording = stream_data.get('recording', False) if stream_data else status.get('recording', False)
        status_icon = "🟢 Recording" if is_recording else "🟡 Idle"
        st.markdown(f"**Status:** {status_icon}")
    with col2:
        camera_status = "🟢" if camera_data.get('data') else "🔴"
        st.markdown(f"**Camera:** {camera_status}")
    with col3:
        lidar_status = "🟢" if lidar_data else "🔴"
        st.markdown(f"**LiDAR:** {lidar_status}")
    with col4:
        map_status = "🟢" if status.get('map_available') else "🔴"
        st.markdown(f"**Map:** {map_status}")
    with col5:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"**Time:** `{current_time}`")
    
    # Main display area
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.camera_enabled:
            st.subheader("📷 Live Camera Feed")
            
            # Process and display latest frame from the aggregated stream data
            camera_frame = process_camera_data(camera_data)
            
            # --- Display Logic ---
            if camera_frame is not None:
                # ✅ FIXED: Direct image display without custom HTML container
                st.image(camera_frame, use_container_width=True)
            else:
                # 2. Frame missing: Display warning
                st.warning("⚠️ NO CAMERA FEED AVAILABLE")
            
            # Timestamp below the image
            frame_timestamp = camera_data.get('timestamp')
            if frame_timestamp:
                try:
                    time_str = datetime.fromtimestamp(frame_timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    st.caption(f"🕐 {time_str}")
                except:
                    st.caption(f"🕐 Stream updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            else:
                st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        else:
            st.info("📷 Camera feed disabled")
    
    with col2:
        if st.session_state.lidar_enabled:
            st.subheader("📡 LiDAR/SLAM Map")
            # ✅ SWAPPED: Laser Scan first, SLAM Map second
            scan_tab, map_tab = st.tabs(["🔴 Laser Scan", "🗺️ SLAM Map"])
            
            with scan_tab:
                # LiDAR Laser Scan visualization
                if lidar_data:
                    fig = visualize_lidar(lidar_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("⚠️ Could not visualize LiDAR data")
                else:
                    st.warning("⚠️ No LiDAR data available in stream")
            
            with map_tab:
                # SLAM Map visualization
                map_payload = get_latest_map_image()
                if map_payload and map_payload.get("image_object"):
                    st.image(map_payload["image_object"], use_container_width=True)
                    resolution = map_payload.get("resolution")
                    timestamp = map_payload.get("timestamp")
                    if resolution:
                        st.caption(f"🗺️ Resolution: {resolution:.2f} m/pixel")
                    if timestamp:
                        try:
                            map_time = datetime.fromtimestamp(timestamp)
                            st.caption(f"🕐 Map updated: {map_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        except Exception:
                            pass
                else:
                    st.warning("⚠️ No SLAM map available")
        else:
            st.info("📡 LiDAR map disabled")
    
    # 🚧 Odometry metrics - TO BE ENHANCED LATER
    # The robot has: tf, odom, imu, map, scan topics available
    # Future enhancement: Full odometry visualization with trajectory, IMU data, etc.
    st.subheader("📊 Odometry (Basic)")
    if odom_data:
        metrics = visualize_odom(odom_data)
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Position X", f"{metrics.get('x', 0):.2f} m")
            with col2:
                st.metric("Position Y", f"{metrics.get('y', 0):.2f} m")
            with col3:
                st.metric("Speed", f"{metrics.get('speed', 0):.2f} m/s")
            with col4:
                # 🚧 TODO: Add heading from IMU/TF data
                st.metric("Heading", f"N/A") 
    else:
        st.info("ℹ️ Odometry visualization will be enhanced in next version")

# Auto-refresh for live mode
if not st.session_state.playback_mode:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
