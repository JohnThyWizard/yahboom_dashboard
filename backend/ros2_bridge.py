import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from nav_msgs.msg import Odometry, OccupancyGrid
from cv_bridge import CvBridge
import numpy as np
import cv2
import threading
from typing import Optional, Tuple, Dict, Any, List

class ROS2Bridge(Node):
    """
    A communication bridge for connecting the FastAPI backend to ROS 2 topics.
    Subscribes to sensor data and provides the latest data via thread-safe accessors.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__('fastapi_ros2_bridge')
        self.bridge = CvBridge()
        
        # --- Latest Data Storage (Thread-safe) ---
        self._latest_camera_frame: Optional[np.ndarray] = None
        self._latest_camera_timestamp: Optional[float] = None
        self._latest_lidar_data: Optional[Dict[str, Any]] = None
        self._latest_odom_data: Optional[Dict[str, Any]] = None
        self._latest_map_data: Optional[Dict[str, Any]] = None
        self._data_lock = threading.Lock()

        # ❗ CRITICAL FIX: Read topics from the nested 'ros2:topics' structure
        ros2_topics = config.get('ros2', {}).get('topics', {})
        camera_topic = ros2_topics.get('camera', '/camera/raw_image') # Gets "/camera/image_raw"
        lidar_topic = ros2_topics.get('lidar', '/scan')
        odom_topic = ros2_topics.get('odom', '/odom')
        map_topic = ros2_topics.get('map', '/map')

        # --- Subscriptions ---
        # 1. Camera Subscription (Now uses the configured topic)
        self.camera_sub = self.create_subscription(
            Image,
            camera_topic,
            self.camera_callback,
            10
        )
        self.get_logger().info(f'Subscribed to camera topic: {camera_topic}')

        # 2. LiDAR Subscription
        self.lidar_sub = self.create_subscription(
            LaserScan,
            lidar_topic,
            self.lidar_callback,
            10
        )
        self.get_logger().info(f'Subscribed to lidar topic: {lidar_topic}')

        # 3. Odometry Subscription
        self.odom_sub = self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            10
        )
        self.get_logger().info(f'Subscribed to odometry topic: {odom_topic}')
        
        # 4. Map Subscription
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            map_topic,
            self.map_callback,
            1 # QoS=1 for static maps
        )
        self.get_logger().info(f'Subscribed to map topic: {map_topic}')

    # --- Callbacks ---

    def camera_callback(self, msg: Image):
        """Converts ROS Image message to OpenCV (numpy array)."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
            
            with self._data_lock:
                self._latest_camera_frame = cv_image
                self._latest_camera_timestamp = timestamp
        except Exception as e:
            self.get_logger().error(f"Camera frame conversion error: {e}")

    def lidar_callback(self, msg: LaserScan):
        """Processes ROS LaserScan message."""
        data = {
            'ranges': [float(r) for r in msg.ranges],
            'angles': [msg.angle_min + i * msg.angle_increment for i in range(len(msg.ranges))],
            'range_min': msg.range_min,
            'range_max': msg.range_max,
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        }
        with self._data_lock:
            self._latest_lidar_data = data
            
    def odom_callback(self, msg: Odometry):
        """Processes ROS Odometry message."""
        data = {
            'position': {
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'z': msg.pose.pose.position.z,
            },
            'linear_velocity': {
                'x': msg.twist.twist.linear.x,
                'y': msg.twist.twist.linear.y,
                'z': msg.twist.twist.linear.z,
            },
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        }
        with self._data_lock:
            self._latest_odom_data = data
            
    def map_callback(self, msg: OccupancyGrid):
        """Processes ROS OccupancyGrid message."""
        data = {
            'width': msg.info.width,
            'height': msg.info.height,
            'resolution': msg.info.resolution,
            'origin': {
                'x': msg.info.origin.position.x,
                'y': msg.info.origin.position.y,
                'z': msg.info.origin.position.z,
            },
            # Convert tuple/list to list of integers for JSON serialization
            'data': list(msg.data), 
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        }
        with self._data_lock:
            self._latest_map_data = data

    # --- Public Accessors for Backend ---

    def get_latest_camera_frame(self) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """Returns the latest frame and its timestamp, WITHOUT clearing the buffer."""
        with self._data_lock:
            frame = self._latest_camera_frame
            timestamp = self._latest_camera_timestamp
            
            # ❌ REMOVE THESE TWO LINES:
            # self._latest_camera_frame = None 
            # self._latest_camera_timestamp = None
            
            return frame, timestamp

    def get_latest_lidar_data(self) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
        """Returns the latest LiDAR data and its timestamp."""
        with self._data_lock:
            data = self._latest_lidar_data
            timestamp = data.get('timestamp') if data else None
            return data, timestamp

    def get_latest_odom(self) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
        """Returns the latest odometry data and its timestamp."""
        with self._data_lock:
            data = self._latest_odom_data
            timestamp = data.get('timestamp') if data else None
            return data, timestamp
            
    def get_latest_map(self) -> Optional[Dict[str, Any]]:
        """Returns the latest map data."""
        with self._data_lock:
            return self._latest_map_data
            
    # --- Status/Peek Accessors (for /api/status endpoint) ---

    @property
    def latest_camera_frame(self) -> Optional[np.ndarray]:
        """Peeks at the latest camera frame without clearing the buffer."""
        with self._data_lock:
            return self._latest_camera_frame

    @property
    def latest_lidar_data(self) -> Optional[Dict[str, Any]]:
        """Peeks at the latest LiDAR data."""
        with self._data_lock:
            return self._latest_lidar_data

    @property
    def latest_map(self) -> Optional[Dict[str, Any]]:
        """Peeks at the latest map data."""
        with self._data_lock:
            return self._latest_map_data