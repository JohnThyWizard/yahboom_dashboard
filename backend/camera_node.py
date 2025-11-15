import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import sys
from typing import Dict, Any

# Configuration defaults
DEFAULT_VIDEO_SOURCE = 0
DEFAULT_FPS = 30  # Increased from 15 for smoother video
TOPIC_NAME = '/camera/raw_image'

class CameraNode(Node):
    """
    ROS 2 Node to capture video frames using OpenCV and publish them as Image messages.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__('camera_publisher')
        
        # Load configuration
        camera_config = config.get('camera', {})
        video_source = camera_config.get('video_source', DEFAULT_VIDEO_SOURCE)
        fps = camera_config.get('fps', DEFAULT_FPS)
        
        self.publisher_ = self.create_publisher(Image, TOPIC_NAME, 10)
        self.bridge = CvBridge()
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(video_source)
        
        # Performance optimizations
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer to reduce latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Fixed resolution
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            self.get_logger().error(f"Failed to open video source {video_source}. Exiting.")
            # Note: Do not exit the process here, just stop attempting to capture
            self.is_active = False
            return
        
        self.is_active = True
        
        # Set frame rate
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        self.timer_period = 1.0 / fps  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.get_logger().info(f'Camera Publisher started, publishing to {TOPIC_NAME} at {fps} FPS')

    def timer_callback(self):
        if not self.is_active:
            return
            
        ret, frame = self.cap.read()

        if ret:
            # Convert the frame to a ROS 2 Image message
            img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            # Set timestamp
            img_msg.header.stamp = self.get_clock().now().to_msg()
            
            self.publisher_.publish(img_msg)
        else:
            self.get_logger().warn('Failed to read frame from camera')

    def stop_camera(self):
        """Releases the camera resource."""
        if self.is_active:
            self.cap.release()
            self.get_logger().info('Camera resource released.')
            self.is_active = False

# Note: main function removed as this is now imported and managed by app.py