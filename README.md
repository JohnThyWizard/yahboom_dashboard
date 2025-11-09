# Yahboom Dashboard

Real-Time Robotic Control & Replay System

A unified, AI-assisted robotic monitoring and control system designed to provide real-time situational awareness, historical replay, and intelligent event logging for mobile robots running ROS2.

## Features

- **Live Monitoring**: Real-time camera feed and LiDAR/SLAM map visualization
- **Continuous Recording**: Data logging for later playback and analysis
- **Seamless Switching**: Instant toggle between live and replay views
- **Time-based Navigation**: Timeline scrubber for recorded data review
- **AI Event Tagging**: Intelligent event detection and timeline visualization
- **Mission Control UI**: Dark technical theme optimized for operational awareness

## Architecture

### Frontend
- **Streamlit Dashboard**: Modern, responsive interface with dual display layout
- **Timeline Scrubber**: DVR-style navigation through recorded frames
- **Recording Controls**: Start/stop live data capture
- **Playback Mode**: Smooth scrubbing and frame-by-frame inspection

### Backend
- **FastAPI Server**: REST/WebSocket endpoints for data streaming
- **ROS2 Integration**: Subscribes to camera, LiDAR, and odometry topics
- **Data Recording**: Synchronized logging to structured format
- **Real-time Streaming**: Low-latency data delivery to frontend

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Source ROS2 (if not already sourced)
source /opt/ros/humble/setup.bash  # Adjust for your ROS2 distribution

# Terminal 1: Run the backend
python backend/main.py

# Terminal 2: Run the frontend
streamlit run frontend/dashboard.py
```

**📖 For detailed setup and usage instructions, see [HOWTO.md](HOWTO.md)**

## Usage

1. Start the FastAPI backend to begin ROS2 topic subscription
2. Launch the Streamlit dashboard
3. Toggle recording to start capturing data
4. Use timeline scrubber to navigate recorded frames
5. Switch between live and replay modes seamlessly

## Configuration

Edit `config/config.yaml` to customize:
- ROS2 topic names
- Recording storage location
- Stream quality settings
- Alert thresholds

