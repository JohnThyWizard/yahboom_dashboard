# Yahboom Dashboard - How To Guide

Complete step-by-step guide for setting up and using the Yahboom Dashboard system.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Using the Dashboard](#using-the-dashboard)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

---

## Prerequisites

Before you begin, ensure you have:

### Required Software

1. **Python 3.8+** - Check with: `python3 --version`
2. **ROS2** (Humble, Foxy, or Galactic) - Check with: `ros2 --version`
3. **pip** - Python package manager
4. **A robot running ROS2** with the following topics:
   - Camera: `/camera/color/image_raw` (sensor_msgs/Image)
   - LiDAR: `/scan` (sensor_msgs/LaserScan)
   - Odometry: `/odom` (nav_msgs/Odometry)
   - Map (optional): `/map` (nav_msgs/OccupancyGrid)

### Verify ROS2 Topics

Before starting, verify your robot is publishing the required topics:

```bash
# Source ROS2 (adjust for your distribution)
source /opt/ros/humble/setup.bash  # or foxy, galactic, etc.

# List available topics
ros2 topic list

# Check if your topics are publishing
ros2 topic echo /camera/color/image_raw --once
ros2 topic echo /scan --once
ros2 topic echo /odom --once
```

---

## Installation

### Step 1: Clone or Navigate to Project Directory

```bash
cd /home/john/yahboom_dashboard
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Note:** If you encounter issues with ROS2 packages (`rclpy`, `cv-bridge`), you may need to install them separately:

```bash
# For ROS2 Humble
sudo apt install ros-humble-rclpy ros-humble-cv-bridge python3-colcon-common-extensions
```

### Step 4: Verify Installation

```bash
# Check if key packages are installed
python3 -c "import streamlit; import fastapi; import rclpy; print('✓ All packages installed')"
```

---

## Configuration

### Step 1: Edit Configuration File

Open `config/config.yaml` and adjust settings for your setup:

```yaml
ros2:
  topics:
    camera: "/camera/color/image_raw"  # Your camera topic
    lidar: "/scan"                     # Your LiDAR topic
    odom: "/odom"                      # Your odometry topic
    map: "/map"                        # Your map topic (optional)

recording:
  storage_path: "recordings"           # Where recordings are saved
  frame_format: "jpg"
  metadata_format: "json"
  sync_interval_ms: 100

streaming:
  image_quality: 85                    # JPEG quality (1-100)
  max_fps: 30                          # Maximum frames per second
  websocket_port: 8765

dashboard:
  refresh_rate_ms: 100                  # UI refresh rate
  max_history_hours: 24

alerts:
  enabled: true
  anomaly_threshold: 0.7
```

### Step 2: Create Recording Directory

```bash
mkdir -p recordings
```

---

## Running the System

The system consists of two components that must run simultaneously:

### Terminal 1: Start the Backend

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Source ROS2
source /opt/ros/humble/setup.bash  # Adjust for your ROS2 distribution

# Run the FastAPI backend
cd /home/john/yahboom_dashboard
python backend/main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
ROS2 subscribers initialized
```

The backend will:
- Connect to ROS2 topics
- Start listening for sensor data
- Serve API endpoints on `http://localhost:8000`

### Terminal 2: Start the Frontend Dashboard

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run Streamlit dashboard
cd /home/john/yahboom_dashboard
streamlit run frontend/dashboard.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

The dashboard will automatically open in your default browser, or navigate to `http://localhost:8501`.

---

## Using the Dashboard

### Initial Setup

1. **Check Backend Connection**
   - Look at the sidebar - you should see "🟢 Backend Status: Connected"
   - If you see "🔴 Disconnected", ensure the backend is running

2. **Verify Sensor Status**
   - Check the sidebar metrics:
     - Camera: Should show "🟢 Active" when receiving frames
     - LiDAR: Should show "🟢 Active" when receiving scans

### Live Monitoring Mode

**Default mode when dashboard starts**

1. **View Live Data**
   - **Left Panel**: Live camera feed with timestamp overlay
   - **Right Panel**: Real-time LiDAR/SLAM map visualization
   - Data updates automatically every 100ms

2. **Control Streams**
   - Use sidebar checkboxes to enable/disable:
     - 📷 Camera Feed
     - 📡 LiDAR/SLAM Map
   - Useful for saving bandwidth or focusing on one stream

3. **Monitor Odometry**
   - Scroll down to see real-time metrics:
     - Position (X, Y, Z)
     - Speed
     - Heading angle

### Recording Data

1. **Start Recording**
   - Click "▶️ Start" button in sidebar
   - Status changes to "🟢 Recording"
   - A new session is created with timestamp ID (e.g., `20240115_143022`)
   - Frames are saved to `recordings/[session_id]/`

2. **During Recording**
   - Recording continues in background
   - You can still view live data
   - Frame count and duration are displayed in sidebar

3. **Stop Recording**
   - Click "⏹️ Stop" button
   - Status changes to "🟡 Idle"
   - Metadata is saved to `recordings/[session_id]/metadata.json`

### Replay Mode

1. **Switch to Replay**
   - Select "Replay" radio button in sidebar
   - Dashboard switches to replay interface

2. **Select Session**
   - Choose a recording session from dropdown
   - Sessions show: `[session_id] ([frame_count] frames)`

3. **Navigate Timeline**
   - Use the slider to scrub through frames
   - Move slider left/right to jump to any frame
   - Frame number and timestamp are displayed

4. **View Recorded Data**
   - **Left Panel**: Recorded camera frame
   - **Right Panel**: Recorded LiDAR data visualization
   - Alert indicators (⚠️) appear for flagged frames

5. **Frame Information**
   - Timestamp shown below timeline
   - Alert warnings for anomalous events
   - Use stream toggles to focus on specific data

### Sidebar Controls

**Control Panel:**
- **Backend Status**: Connection indicator
- **Recording**: Start/Stop buttons and status
- **Display Mode**: Switch between Live/Replay
- **Stream Controls**: Toggle camera/LiDAR streams
- **System Metrics**: Real-time sensor status

---

## Troubleshooting

### Backend Won't Start

**Problem:** `ModuleNotFoundError` or import errors

**Solutions:**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check ROS2 is sourced
source /opt/ros/humble/setup.bash
echo $ROS_DISTRO  # Should show your ROS2 distribution

# Verify Python can find ROS2 packages
python3 -c "import rclpy; print(rclpy.__file__)"
```

### Backend Shows "ROS2 not initialized"

**Problem:** ROS2 topics not found

**Solutions:**
```bash
# Verify topics exist
ros2 topic list | grep -E "(camera|scan|odom)"

# Check topic types match
ros2 topic info /camera/color/image_raw
ros2 topic info /scan
ros2 topic info /odom

# Update config.yaml if topics are different
```

### Dashboard Shows "No Camera Data Available"

**Problem:** Camera topic not publishing or wrong topic name

**Solutions:**
```bash
# Check if camera is publishing
ros2 topic hz /camera/color/image_raw

# Verify topic name in config.yaml matches your setup
# Update config/config.yaml if needed
```

### Dashboard Shows "No LiDAR Data Available"

**Problem:** LiDAR topic not publishing or wrong topic name

**Solutions:**
```bash
# Check if LiDAR is publishing
ros2 topic hz /scan

# Verify topic name in config.yaml
# Some robots use different topic names like /laser_scan
```

### Recording Not Working

**Problem:** Frames not being saved

**Solutions:**
```bash
# Check recording directory exists and is writable
ls -la recordings/
chmod 755 recordings/

# Check disk space
df -h

# Verify backend has write permissions
touch recordings/test.txt && rm recordings/test.txt
```

### Dashboard Freezes or Slow Updates

**Problem:** Too many frames or network issues

**Solutions:**
- Disable one stream (camera or LiDAR) to reduce load
- Lower `max_fps` in `config/config.yaml`
- Increase `refresh_rate_ms` in config
- Check network connection if using remote robot

### Port Already in Use

**Problem:** `Address already in use` error

**Solutions:**
```bash
# Backend (port 8000)
lsof -i :8000
kill -9 <PID>

# Frontend (port 8501)
lsof -i :8501
kill -9 <PID>

# Or change ports in code/config
```

---

## Advanced Usage

### Custom Backend URL

If running backend on a different machine or port, edit `frontend/dashboard.py`:

```python
BACKEND_URL = "http://your-robot-ip:8000"  # Change this line
```

### Remote Access

To access dashboard from another computer:

1. **Backend**: Already listens on `0.0.0.0:8000` (all interfaces)
2. **Frontend**: Streamlit listens on all interfaces by default
3. **Access**: Use `http://your-computer-ip:8501`

**Security Note:** For production, add authentication and use HTTPS.

### Recording Storage Management

**View Recordings:**
```bash
ls -lh recordings/
du -sh recordings/*  # Check sizes
```

**Clean Old Recordings:**
```bash
# Remove recordings older than 7 days
find recordings/ -type d -mtime +7 -exec rm -rf {} \;
```

**Export Recording:**
```bash
# Compress a session
tar -czf session_20240115_143022.tar.gz recordings/20240115_143022/
```

### Performance Tuning

**For High-FPS Robots:**
- Lower `image_quality` in config (e.g., 70)
- Increase `sync_interval_ms` (e.g., 200)
- Disable unused streams

**For Low-Bandwidth Networks:**
- Lower `max_fps` (e.g., 10)
- Reduce `image_quality` (e.g., 60)
- Use stream toggles to view one at a time

### WebSocket Streaming

The backend supports WebSocket streaming for lower latency. To use:

1. Connect to `ws://localhost:8000/ws`
2. Receive JSON messages with base64-encoded frames
3. Implement custom client if needed

---

## Quick Reference

### Starting the System

```bash
# Terminal 1: Backend
source /opt/ros/humble/setup.bash
python backend/main.py

# Terminal 2: Frontend
streamlit run frontend/dashboard.py
```

### Key URLs

- **Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

### Important Files

- **Config**: `config/config.yaml`
- **Backend**: `backend/main.py`
- **Frontend**: `frontend/dashboard.py`
- **Recordings**: `recordings/[session_id]/`

### Useful Commands

```bash
# Check ROS2 topics
ros2 topic list
ros2 topic hz /camera/color/image_raw

# View API documentation
curl http://localhost:8000/docs

# List recording sessions
curl http://localhost:8000/api/recording/sessions

# Check system status
curl http://localhost:8000/api/status
```

---

## Next Steps

- **Customize UI**: Edit `frontend/dashboard.py` for theme/colors
- **Add Alerts**: Implement anomaly detection in `backend/recorder.py`
- **Export Data**: Create scripts to export recordings to other formats
- **Multi-Robot**: Extend to monitor multiple robots simultaneously

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review ROS2 topic names and types
3. Verify all dependencies are installed
4. Check backend logs for error messages

---

**Happy Monitoring! 🤖**

