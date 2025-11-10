"""
Camera Node - Publishes camera frames to ROS2 topic
Opens /dev/video0 (or configurable device) and publishes sensor_msgs/Image
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import time
from typing import Optional


class CameraNode(Node):
    """ROS2 node that publishes camera frames from OpenCV"""
    
    def __init__(self, config: dict):
        super().__init__('yahboom_camera_node')
        self.config = config
        self.bridge = CvBridge()
        
        # Camera settings from config
        camera_config = config.get('camera', {})
        self.device = camera_config.get('device', '/dev/video0')
        self.width = camera_config.get('width', 640)
        self.height = camera_config.get('height', 480)
        self.fps = camera_config.get('fps', 30)
        self.topic_name = config['ros2']['topics'].get('camera', '/camera/image_raw')
        
        # Camera object
        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self.camera_thread: Optional[threading.Thread] = None
        
        # Publisher
        self.publisher = self.create_publisher(Image, self.topic_name, 10)
        
        # Start camera
        self.start_camera()
        
        self.get_logger().info(f'Camera node initialized: {self.device} -> {self.topic_name}')
    
    def start_camera(self):
        """Initialize and start camera capture"""
        try:
            # Try to open camera device
            device_id = self.device
            if device_id.startswith('/dev/video'):
                # Extract device number from /dev/video0 -> 0
                device_id = int(device_id.replace('/dev/video', ''))
            
            self.cap = cv2.VideoCapture(device_id)
            
            if not self.cap.isOpened():
                self.get_logger().error(f'Failed to open camera device: {self.device}')
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Get actual properties (may differ from requested)
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            self.get_logger().info(
                f'Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps'
            )
            
            # Start capture thread
            self.running = True
            self.camera_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.camera_thread.start()
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'Error starting camera: {e}')
            return False
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        frame_time = 1.0 / self.fps
        
        while self.running and self.cap is not None:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    self.get_logger().warn('Failed to read frame from camera')
                    time.sleep(frame_time)
                    continue
                
                # Convert OpenCV image to ROS2 Image message
                try:
                    ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                    ros_image.header.stamp = self.get_clock().now().to_msg()
                    ros_image.header.frame_id = 'camera_frame'
                    
                    # Publish
                    self.publisher.publish(ros_image)
                    
                except Exception as e:
                    self.get_logger().error(f'Error converting/publishing frame: {e}')
                
                # Sleep to maintain framerate
                time.sleep(frame_time)
                
            except Exception as e:
                self.get_logger().error(f'Error in capture loop: {e}')
                time.sleep(0.1)
    
    def stop_camera(self):
        """Stop camera capture and cleanup"""
        self.running = False
        
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.get_logger().info('Camera stopped')
    
    def destroy_node(self):
        """Cleanup on node destruction"""
        self.stop_camera()
        super().destroy_node()

