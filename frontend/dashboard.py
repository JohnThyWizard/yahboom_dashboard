"""
Yahboom Dashboard - Streamlit Frontend
Real-Time Robotic Control & Replay System
"""
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
REFRESH_INTERVAL = 0.1  # 100ms for smooth updates

# Page configuration
st.set_page_config(
    page_title="Yahboom Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark technical theme
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
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-recording {
        background-color: #00ff00;
        box-shadow: 0 0 10px #00ff00;
    }
    
    .status-idle {
        background-color: #ffaa00;
    }
    
    .status-alert {
        background-color: #ff0000;
        box-shadow: 0 0 10px #ff0000;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Data highlights */
    .data-highlight {
        color: #00ffff;
        font-weight: bold;
    }
    
    .metric-card {
        background-color: #1a1f3a;
        border: 1px solid #00ffff;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Timeline styling */
    .timeline-container {
        background-color: #1a1f3a;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #00ffff;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_connection() -> bool:
    """Check if backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_status() -> Optional[Dict]:
    """Get system status from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Backend connection error: {e}")
    return None


def get_latest_camera_frame() -> Optional[Image.Image]:
    """Get latest camera frame from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/camera/latest", timeout=2)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
    return None


def get_latest_lidar_data() -> Optional[Dict]:
    """Get latest LiDAR data from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/lidar/latest", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_latest_odom() -> Optional[Dict]:
    """Get latest odometry data from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/odom/latest", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
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


def get_frame_from_session(session_id: str, frame_id: str) -> Optional[Image.Image]:
    """Get a specific frame from a session"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recording/session/{session_id}/frame/{frame_id}", timeout=2)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
    return None


def get_lidar_from_session(session_id: str, frame_id: str) -> Optional[Dict]:
    """Get LiDAR data for a specific frame from a session"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/recording/session/{session_id}/lidar/{frame_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def visualize_lidar(lidar_data: Dict) -> go.Figure:
    """Create LiDAR visualization"""
    if not lidar_data or 'data' not in lidar_data:
        return None
    
    data = lidar_data['data']
    ranges = np.array(data.get('ranges', []))
    angles = np.array(data.get('angles', []))
    
    # Filter invalid ranges
    valid_mask = (ranges > data.get('range_min', 0)) & (ranges < data.get('range_max', 30))
    ranges = ranges[valid_mask]
    angles = angles[valid_mask]
    
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
        title="LiDAR/SLAM Map",
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
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    
    return fig


def visualize_odom(odom_data: Dict) -> Dict[str, float]:
    """Extract odometry metrics"""
    if not odom_data or 'data' not in odom_data:
        return {}
    
    data = odom_data['data']
    pos = data.get('position', {})
    vel = data.get('linear_velocity', {})
    
    return {
        'x': pos.get('x', 0),
        'y': pos.get('y', 0),
        'z': pos.get('z', 0),
        'vx': vel.get('x', 0),
        'vy': vel.get('y', 0),
        'speed': np.sqrt(vel.get('x', 0)**2 + vel.get('y', 0)**2)
    }


# Initialize session state
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
        st.metric("Camera", "🟢 Active" if status.get('camera_available') else "🔴 Inactive")
        st.metric("LiDAR", "🟢 Active" if status.get('lidar_available') else "🔴 Inactive")
        
        if recording_status and status.get('recording_session'):
            session_info = status['recording_session']
            st.metric("Frames Recorded", f"{session_info.get('frame_count', 0):,}")
            duration = session_info.get('duration', 0)
            st.metric("Duration", f"{duration:.1f}s")


# Main content area
if st.session_state.playback_mode:
    # Replay mode
    st.header("📼 Replay Mode")
    
    # Session selection
    sessions = list_recording_sessions()
    if sessions:
        session_options = {s['session_id']: f"{s['session_id']} ({s['frame_count']} frames)" 
                          for s in sessions}
        selected_session_id = st.selectbox(
            "Select Recording Session",
            options=list(session_options.keys()),
            format_func=lambda x: session_options[x]
        )
        
        if selected_session_id:
            session_data = get_session_data(selected_session_id)
            if session_data and 'frames' in session_data:
                frames = session_data['frames']
                
                if frames:
                    # Timeline scrubber
                    st.subheader("⏱️ Timeline")
                    max_idx = len(frames) - 1
                    frame_idx = st.slider(
                        "Frame",
                        0,
                        max_idx,
                        value=st.session_state.current_frame_idx,
                        key="frame_slider"
                    )
                    st.session_state.current_frame_idx = frame_idx
                    
                    # Frame info
                    current_frame = frames[frame_idx]
                    frame_time = datetime.fromtimestamp(current_frame['timestamp'])
                    st.markdown(f"**Timestamp:** `{frame_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}`")
                    
                    # Alert indicator
                    if current_frame.get('alert'):
                        st.warning("⚠️ Alert detected at this frame")
                    
                    # Display frame
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.session_state.camera_enabled:
                            st.subheader("📷 Camera Feed")
                            frame_id = current_frame['frame_id']
                            frame_img = get_frame_from_session(selected_session_id, frame_id)
                            if frame_img:
                                st.image(frame_img, use_container_width=True)
                            else:
                                st.error("Frame not available")
                        else:
                            st.info("Camera feed disabled")
                    
                    with col2:
                        if st.session_state.lidar_enabled:
                            st.subheader("📡 LiDAR/SLAM Map")
                            # Load LiDAR data from frame
                            frame_id = current_frame['frame_id']
                            lidar_data = get_lidar_from_session(selected_session_id, frame_id)
                            if lidar_data:
                                fig = visualize_lidar(lidar_data)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Could not visualize LiDAR data")
                            else:
                                st.warning("No LiDAR data for this frame")
                        else:
                            st.info("LiDAR map disabled")
                else:
                    st.warning("No frames in this session")
            else:
                st.error("Could not load session data")
    else:
        st.info("No recording sessions available. Start recording to create sessions.")
else:
    # Live mode
    st.header("🔴 Live Monitoring")
    
    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_icon = "🟢 Recording" if (status and status.get('recording')) else "🟡 Idle"
        st.markdown(f"**Status:** {status_icon}")
    with col2:
        if status:
            camera_status = "🟢" if status.get('camera_available') else "🔴"
            st.markdown(f"**Camera:** {camera_status}")
    with col3:
        if status:
            lidar_status = "🟢" if status.get('lidar_available') else "🔴"
            st.markdown(f"**LiDAR:** {lidar_status}")
    with col4:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"**Time:** `{current_time}`")
    
    # Main display area
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.camera_enabled:
            st.subheader("📷 Live Camera Feed")
            camera_placeholder = st.empty()
            
            # Get and display latest frame
            camera_frame = get_latest_camera_frame()
            if camera_frame:
                camera_placeholder.image(camera_frame, use_container_width=True)
                # Timestamp overlay
                if status:
                    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            else:
                camera_placeholder.warning("⚠️ No camera data available")
        else:
            st.info("📷 Camera feed disabled")
    
    with col2:
        if st.session_state.lidar_enabled:
            st.subheader("📡 LiDAR/SLAM Map")
            lidar_placeholder = st.empty()
            
            # Get and display latest LiDAR data
            lidar_data = get_latest_lidar_data()
            if lidar_data:
                fig = visualize_lidar(lidar_data)
                if fig:
                    lidar_placeholder.plotly_chart(fig, use_container_width=True)
                else:
                    lidar_placeholder.warning("⚠️ Could not visualize LiDAR data")
            else:
                lidar_placeholder.warning("⚠️ No LiDAR data available")
        else:
            st.info("📡 LiDAR map disabled")
    
    # Odometry metrics
    st.subheader("📊 Odometry")
    odom_data = get_latest_odom()
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
                st.metric("Heading", f"{np.degrees(np.arctan2(metrics.get('y', 0), metrics.get('x', 0))):.1f}°")
    else:
        st.warning("⚠️ No odometry data available")

# Auto-refresh for live mode
if not st.session_state.playback_mode:
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

