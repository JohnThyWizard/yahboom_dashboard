# Camera Data Setup Guide

## How the System Gets Camera Data

The Yahboom Dashboard gets camera data through **ROS2 topics**. Here's the complete data flow:

```
Physical Camera → ROS2 Camera Driver → ROS2 Topic → Dashboard Backend → Dashboard Frontend
```

### Data Flow Breakdown

1. **ROS2 Topic**: The system subscribes to `/camera/color/image_raw` (configurable in `config/config.yaml`)
2. **Message Type**: Expects `sensor_msgs/Image` messages
3. **ROS2 Bridge**: Converts ROS2 image messages to OpenCV format using `cv_bridge`
4. **FastAPI Backend**: Serves the latest frame via REST API
5. **Streamlit Dashboard**: Displays the camera feed

---

## What You Need

### Option 1: Physical Camera with ROS2 Driver

You need a **ROS2 camera driver** running that publishes to a ROS2 topic. Common options:

#### USB Camera (using `usb_cam`)
```bash
# Install usb_cam package
sudo apt install ros-humble-usb-cam

# Run the camera driver
ros2 run usb_cam usb_cam_node_exe \
    --ros-args \
    -p image_raw/compressed:=false \
    -p video_device:=/dev/video0 \
    -p framerate:=30.0
```

This publishes to `/image_raw` by default. You may need to update `config/config.yaml`:
```yaml
camera: "/image_raw"  # Instead of "/camera/color/image_raw"
```

#### RealSense Camera (Intel)
```bash
# Install RealSense ROS2 package
sudo apt install ros-humble-realsense2-camera

# Run RealSense node
ros2 launch realsense2_camera rs_launch.py
```

This publishes to `/camera/color/image_raw` (matches default config).

#### Yahboom Camera (if you have a Yahboom robot)
Check your Yahboom robot's documentation for the camera driver launch command.

---

### Option 2: ROS2 Bag File (for testing)

If you don't have a physical camera, you can use a recorded bag file:

```bash
# Play a bag file
ros2 bag play your_camera_bag.db3

# Check what topics it publishes
ros2 bag info your_camera_bag.db3
```

---

### Option 3: Simulation (Gazebo/Ignition)

If using a simulator:

```bash
# Launch your robot simulation
ros2 launch your_robot_sim.launch.py

# The simulation should publish camera topics automatically
```

---

## How to Check What Topics Your System Has

### Step 1: List All Topics

```bash
# Source ROS2 first
source /opt/ros/humble/setup.bash

# List all available topics
ros2 topic list
```

Look for camera-related topics like:
- `/camera/color/image_raw`
- `/image_raw`
- `/camera/image_raw`
- `/camera/rgb/image_raw`
- `/camera/image`

### Step 2: Check Topic Type

```bash
# Check what message type a topic uses
ros2 topic info /camera/color/image_raw

# Should show: Type: sensor_msgs/msg/Image
```

### Step 3: Verify Topic is Publishing

```bash
# Check if topic is actively publishing
ros2 topic hz /camera/color/image_raw

# Should show: average rate: ~30.000 Hz (or similar)
```

### Step 4: View One Frame (Test)

```bash
# View a single frame to verify it works
ros2 topic echo /camera/color/image_raw --once
```

---

## Updating Configuration for Your Camera

If your camera publishes to a different topic, edit `config/config.yaml`:

```yaml
ros2:
  topics:
    camera: "/your_camera_topic_here"  # Change this to match your topic
    lidar: "/scan"
    odom: "/odom"
    map: "/map"
```

**Then restart the backend** for changes to take effect.

---

## Common Camera Topics by Robot/Driver

| Robot/Driver | Default Topic | Message Type |
|-------------|--------------|--------------|
| RealSense | `/camera/color/image_raw` | `sensor_msgs/Image` |
| usb_cam | `/image_raw` | `sensor_msgs/Image` |
| OpenCV Camera | `/camera/image_raw` | `sensor_msgs/Image` |
| Gazebo | `/camera/image_raw` | `sensor_msgs/Image` |
| TurtleBot | `/camera/image_raw` | `sensor_msgs/Image` |

---

## Troubleshooting

### Problem: "No camera data available" in dashboard

**Check:**
1. Is ROS2 topic publishing?
   ```bash
   ros2 topic hz /camera/color/image_raw
   ```

2. Does topic name match config?
   ```bash
   ros2 topic list
   # Compare with config/config.yaml
   ```

3. Is backend running and connected?
   - Check backend logs for "ROS2 subscribers initialized"
   - Check for any error messages

### Problem: "404 Not Found" for camera endpoint

This means:
- Backend is running ✓
- ROS2 bridge is initialized ✓
- But no camera data has been received yet

**Solution:** Start your camera driver/robot.

### Problem: Wrong topic name

**Solution:** Update `config/config.yaml` and restart backend.

### Problem: Wrong message type

The system expects `sensor_msgs/Image`. If your camera publishes a different type:
- Check with: `ros2 topic info /your_topic`
- You may need to remap or convert the topic

---

## Quick Test: Verify Everything Works

```bash
# Terminal 1: Start camera driver (example for USB camera)
source /opt/ros/humble/setup.bash
ros2 run usb_cam usb_cam_node_exe

# Terminal 2: Check topic is publishing
source /opt/ros/humble/setup.bash
ros2 topic hz /image_raw  # or whatever your topic is

# Terminal 3: Start dashboard backend
cd /home/john/yahboom_dashboard
source streamlit-venv/bin/activate
python backend/main.py

# Terminal 4: Start dashboard frontend
cd /home/john/yahboom_dashboard
source streamlit-venv/bin/activate
streamlit run frontend/dashboard.py
```

---

## Example: Setting Up USB Camera

If you have a USB webcam, here's a complete setup:

```bash
# 1. Install USB camera driver
sudo apt install ros-humble-usb-cam

# 2. Find your camera device
ls -l /dev/video*

# 3. Launch camera driver
source /opt/ros/humble/setup.bash
ros2 run usb_cam usb_cam_node_exe \
    --ros-args \
    -p video_device:=/dev/video0 \
    -p framerate:=30.0 \
    -p image_width:=640 \
    -p image_height:=480

# 4. Update config/config.yaml
# Change: camera: "/image_raw"

# 5. Restart backend
```

---

## Summary

**The system expects:**
- A ROS2 topic publishing `sensor_msgs/Image` messages
- Default topic: `/camera/color/image_raw` (configurable)
- Topic must be actively publishing when backend starts

**You need to provide:**
- A camera driver node running (physical camera, simulation, or bag file)
- The topic name must match your `config/config.yaml` setting

**To verify:**
```bash
ros2 topic list          # See available topics
ros2 topic hz /topic     # Check publishing rate
ros2 topic info /topic   # Check message type
```

