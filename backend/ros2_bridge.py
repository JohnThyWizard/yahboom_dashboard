"""
ROS2 Bridge - Handles subscription to ROS2 topics and data conversion
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from nav_msgs.msg import OccupancyGrid, Odometry
from cv_bridge import CvBridge
import numpy as np
from typing import Optional, Callable
import threading
import time


class ROS2Bridge(Node):
    """Bridge between ROS2 topics and Python data structures"""
    
    def __init__(self, config: dict):
        super().__init__('yahboom_dashboard_bridge')
        self.config = config
        self.bridge = CvBridge()
        
        # Latest data storage
        self.latest_camera_frame = None
        self.latest_lidar_data = None
        self.latest_odom = None
        self.latest_map = None
        
        # Timestamps
        self.camera_timestamp = None
        self.lidar_timestamp = None
        self.odom_timestamp = None
        
        # Callbacks for data updates
        self.camera_callback: Optional[Callable] = None
        self.lidar_callback: Optional[Callable] = None
        self.odom_callback: Optional[Callable] = None
        
        # Locks for thread safety
        self.camera_lock = threading.Lock()
        self.lidar_lock = threading.Lock()
        self.odom_lock = threading.Lock()
        
        # Initialize subscribers
        self._setup_subscribers()
        
    def _setup_subscribers(self):
        """Set up ROS2 topic subscribers"""
        topics = self.config['ros2']['topics']
        
        # Camera subscriber
        self.create_subscription(
            Image,
            topics['camera'],
            self._camera_callback,
            10
        )
        
        # LiDAR subscriber
        self.create_subscription(
            LaserScan,
            topics['lidar'],
            self._lidar_callback,
            10
        )
        
        # Odometry subscriber
        self.create_subscription(
            Odometry,
            topics['odom'],
            self._odom_callback,
            10
        )
        
        # Map subscriber (optional)
        if topics.get('map'):
            self.create_subscription(
                OccupancyGrid,
                topics['map'],
                self._map_callback,
                10
            )
        
        self.get_logger().info('ROS2 subscribers initialized')
    
    def _camera_callback(self, msg: Image):
        """Process incoming camera image"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            with self.camera_lock:
                self.latest_camera_frame = cv_image
                self.camera_timestamp = timestamp
            
            if self.camera_callback:
                self.camera_callback(cv_image, timestamp)
                
        except Exception as e:
            self.get_logger().error(f'Camera callback error: {e}')
    
    def _lidar_callback(self, msg: LaserScan):
        """Process incoming LiDAR scan"""
        try:
            # Convert LaserScan to numpy array
            ranges = np.array(msg.ranges)
            angles = np.linspace(msg.angle_min, msg.angle_max, len(ranges))
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            
            lidar_data = {
                'ranges': ranges.tolist(),
                'angles': angles.tolist(),
                'angle_min': msg.angle_min,
                'angle_max': msg.angle_max,
                'range_min': msg.range_min,
                'range_max': msg.range_max,
                'timestamp': timestamp
            }
            
            with self.lidar_lock:
                self.latest_lidar_data = lidar_data
                self.lidar_timestamp = timestamp
            
            if self.lidar_callback:
                self.lidar_callback(lidar_data, timestamp)
                
        except Exception as e:
            self.get_logger().error(f'LiDAR callback error: {e}')
    
    def _odom_callback(self, msg: Odometry):
        """Process incoming odometry data"""
        try:
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            pose = msg.pose.pose
            
            odom_data = {
                'position': {
                    'x': pose.position.x,
                    'y': pose.position.y,
                    'z': pose.position.z
                },
                'orientation': {
                    'x': pose.orientation.x,
                    'y': pose.orientation.y,
                    'z': pose.orientation.z,
                    'w': pose.orientation.w
                },
                'linear_velocity': {
                    'x': msg.twist.twist.linear.x,
                    'y': msg.twist.twist.linear.y,
                    'z': msg.twist.twist.linear.z
                },
                'angular_velocity': {
                    'x': msg.twist.twist.angular.x,
                    'y': msg.twist.twist.angular.y,
                    'z': msg.twist.twist.angular.z
                },
                'timestamp': timestamp
            }
            
            with self.odom_lock:
                self.latest_odom = odom_data
                self.odom_timestamp = timestamp
            
            if self.odom_callback:
                self.odom_callback(odom_data, timestamp)
                
        except Exception as e:
            self.get_logger().error(f'Odometry callback error: {e}')
    
    def _map_callback(self, msg: OccupancyGrid):
        """Process incoming map data"""
        try:
            map_data = {
                'width': msg.info.width,
                'height': msg.info.height,
                'resolution': msg.info.resolution,
                'origin': {
                    'x': msg.info.origin.position.x,
                    'y': msg.info.origin.position.y
                },
                'data': list(msg.data),
                'timestamp': time.time()
            }
            
            self.latest_map = map_data
            
        except Exception as e:
            self.get_logger().error(f'Map callback error: {e}')
    
    def get_latest_camera_frame(self):
        """Thread-safe getter for latest camera frame"""
        with self.camera_lock:
            return self.latest_camera_frame, self.camera_timestamp
    
    def get_latest_lidar_data(self):
        """Thread-safe getter for latest LiDAR data"""
        with self.lidar_lock:
            return self.latest_lidar_data, self.lidar_timestamp
    
    def get_latest_odom(self):
        """Thread-safe getter for latest odometry"""
        with self.odom_lock:
            return self.latest_odom, self.odom_timestamp
    
    def get_latest_map(self):
        """Get latest map data"""
        return self.latest_map

