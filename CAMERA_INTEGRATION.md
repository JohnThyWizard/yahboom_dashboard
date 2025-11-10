# Built-in Camera Integration

The Yahboom Dashboard now includes a **built-in camera driver** that automatically opens your camera and publishes to ROS2 topics. No separate camera driver needed!

## How It Works

When you start the backend, if `camera.enabled: true` in `config/config.yaml`, the system will:

1. **Open your camera** (default: `/dev/video0`)
2. **Publish frames** to ROS2 topic `/camera/image_raw`
3. **Bridge automatically** receives the frames and serves them to the dashboard

## Configuration

Edit `config/config.yaml`:

```yaml
camera:
  enabled: true              # Set to false to disable
  device: "/dev/video0"      # Camera device path
  width: 640                 # Frame width
  height: 480                # Frame height
  fps: 30                    # Frames per second

ros2:
  topics:
    camera: "/camera/image_raw"  # Topic name (matches camera node)
```

### Available Camera Devices

Check what cameras are available:
```bash
ls -l /dev/video*
```

Common devices:
- `/dev/video0` - First camera (default)
- `/dev/video1` - Second camera
- `/dev/video2` - Third camera, etc.

### Resolution Options

Common resolutions:
- `640x480` (default) - VGA
- `1280x720` - HD 720p
- `1920x1080` - Full HD 1080p

**Note:** Your camera may not support all resolutions. The system will use the closest supported resolution.

## Usage

### Start the Backend

```bash
cd /home/john/yahboom_dashboard
source streamlit-venv/bin/activate
source /opt/ros/humble/setup.bash
python backend/main.py
```

**Expected output:**
```
[INFO] [yahboom_camera_node]: Camera node initialized: /dev/video0 -> /camera/image_raw
[INFO] [yahboom_camera_node]: Camera opened: 640x480 @ 30fps
[INFO] [yahboom_dashboard_bridge]: ROS2 subscribers initialized
```

### Verify Camera is Working

```bash
# Check if topic is publishing
ros2 topic hz /camera/image_raw

# Should show: average rate: ~30.000 Hz
```

### View Camera Feed

1. Start backend (as above)
2. Start dashboard: `streamlit run frontend/dashboard.py`
3. Camera feed should appear automatically!

## Troubleshooting

### "Failed to open camera device"

**Problem:** Cannot access `/dev/video0`

**Solutions:**

1. **Check device exists:**
   ```bash
   ls -l /dev/video0
   ```

2. **Check permissions:**
   ```bash
   # Add user to video group (if not already)
   sudo usermod -a -G video $USER
   # Log out and back in for changes to take effect
   ```

3. **Check if camera is in use:**
   ```bash
   # See what's using the camera
   lsof /dev/video0
   # Close other applications using the camera
   ```

4. **Try different device:**
   ```yaml
   # In config/config.yaml
   camera:
     device: "/dev/video1"  # Try video1, video2, etc.
   ```

### "Camera opened but no frames"

**Problem:** Camera opens but publishes no data

**Solutions:**

1. **Check camera is working:**
   ```bash
   # Test with v4l2-utils (if installed)
   v4l2-ctl --device=/dev/video0 --all
   ```

2. **Try different resolution:**
   ```yaml
   camera:
     width: 320
     height: 240
   ```

3. **Check camera format:**
   - Some cameras only support specific formats
   - The system uses BGR8 (standard webcam format)

### Camera is Slow/Laggy

**Solutions:**

1. **Reduce resolution:**
   ```yaml
   camera:
     width: 320
     height: 240
   ```

2. **Reduce framerate:**
   ```yaml
   camera:
     fps: 15
   ```

3. **Check system resources:**
   ```bash
   htop  # Check CPU usage
   ```

### Want to Disable Camera

Set in `config/config.yaml`:
```yaml
camera:
  enabled: false
```

Then restart backend.

## Multiple Cameras

To use a different camera:

1. **Find available cameras:**
   ```bash
   ls -l /dev/video*
   ```

2. **Update config:**
   ```yaml
   camera:
     device: "/dev/video1"  # Use second camera
   ```

3. **Restart backend**

## Advanced: Using External Camera Driver

If you prefer to use an external ROS2 camera driver (like `usb_cam`), you can:

1. **Disable built-in camera:**
   ```yaml
   camera:
     enabled: false
   ```

2. **Update topic name** to match your external driver:
   ```yaml
   ros2:
     topics:
       camera: "/image_raw"  # Or whatever your driver uses
   ```

3. **Run your external driver** separately

## Summary

✅ **Built-in camera driver** - No separate installation needed  
✅ **Automatic startup** - Starts when backend starts  
✅ **Configurable** - Device, resolution, framerate  
✅ **ROS2 compatible** - Publishes standard `sensor_msgs/Image`  
✅ **Easy to disable** - Set `enabled: false` in config

The camera integration makes the dashboard **self-contained** - just start the backend and your camera feed is available!

