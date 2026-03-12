#!/usr/bin/env python3
"""
Nó de visão computacional: seguimento de cor (ex.: alvo vermelho).

Assina um tópico de imagem (ex.: /camera/image_raw), detecta a cor configurada
(HSV) e publica o centroide do maior blob e/ou cmd_vel para seguir o alvo.

Requer: fonte de imagem (câmera simulação waffle_pi ou tópico Image).
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray

try:
    from cv_bridge import CvBridge
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class VisionNode(Node):
    """Detecta cor (HSV) na imagem e publica centroide ou cmd_vel para seguir."""

    def __init__(self):
        super().__init__('vision_node')
        if not HAS_OPENCV:
            self.get_logger().error('cv_bridge ou opencv não disponíveis. Instale: ros-humble-cv-bridge e opencv-python')
            return

        self.declare_parameter('image_topic', 'camera/image_raw')
        self.declare_parameter('cmd_vel_topic', 'cmd_vel')
        self.declare_parameter('publish_cmd_vel', True)
        self.declare_parameter('target_hue_center', 0.0)   # 0 = vermelho (ou 120 = verde)
        self.declare_parameter('target_hue_range', 15.0)   # ± graus em hue
        self.declare_parameter('min_saturation', 80)
        self.declare_parameter('min_value', 80)
        self.declare_parameter('min_area', 500)
        self.declare_parameter('max_linear', 0.2)
        self.declare_parameter('max_angular', 0.8)
        self.declare_parameter('control_period', 0.05)

        self._image_topic = self.get_parameter('image_topic').value
        self._cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self._publish_cmd_vel = self.get_parameter('publish_cmd_vel').value
        self._hue_center = float(self.get_parameter('target_hue_center').value)
        self._hue_range = float(self.get_parameter('target_hue_range').value)
        self._min_sat = self.get_parameter('min_saturation').value
        self._min_val = self.get_parameter('min_value').value
        self._min_area = self.get_parameter('min_area').value
        self._max_linear = self.get_parameter('max_linear').value
        self._max_angular = self.get_parameter('max_angular').value
        period = self.get_parameter('control_period').value

        self._bridge = CvBridge()
        self._center_x: float | None = None  # centroide normalizado -0.5..0.5
        self._center_y: float | None = None
        self._target_visible = False

        self._pub_centroid = self.create_publisher(
            Float32MultiArray, 'vision/centroid', 10
        )
        if self._publish_cmd_vel:
            self._pub_cmd = self.create_publisher(Twist, self._cmd_vel_topic, 10)
        else:
            self._pub_cmd = None

        self._sub_image = self.create_subscription(
            Image, self._image_topic, self._cb_image, 10
        )
        self._timer = self.create_timer(period, self._control_loop)
        self.get_logger().info(
            'Vision node: image=%s, publish_cmd_vel=%s'
            % (self._image_topic, self._publish_cmd_vel)
        )

    def _cb_image(self, msg: Image) -> None:
        if not HAS_OPENCV:
            return
        try:
            cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn('cv_bridge error: %s' % e)
            return
        h, w = cv_image.shape[:2]
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # Máscara para hue (abrir intervalo para vermelho que cruza 0)
        h_center = int(self._hue_center) % 180
        h_range = int(self._hue_range)
        if h_center < h_range or h_center > 180 - h_range:
            lower1 = (0, self._min_sat, self._min_val)
            upper1 = (min(180, h_center + h_range), 255, 255)
            lower2 = (max(0, h_center - h_range), self._min_sat, self._min_val)
            upper2 = (180, 255, 255)
            mask = cv2.bitwise_or(
                cv2.inRange(hsv, lower1, upper1),
                cv2.inRange(hsv, lower2, upper2),
            )
        else:
            lower = (max(0, h_center - h_range), self._min_sat, self._min_val)
            upper = (min(180, h_center + h_range), 255, 255)
            mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        best = None
        best_area = self._min_area
        for c in contours:
            area = cv2.contourArea(c)
            if area >= best_area:
                best_area = area
                best = c
        if best is not None:
            M = cv2.moments(best)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                self._center_x = (cx / w) - 0.5
                self._center_y = -((cy / h) - 0.5)
                self._target_visible = True
                arr = Float32MultiArray()
                arr.data = [float(self._center_x), float(self._center_y)]
                self._pub_centroid.publish(arr)
                return
        self._target_visible = False
        self._center_x = None
        self._center_y = None

    def _control_loop(self) -> None:
        if self._pub_cmd is None or not self._publish_cmd_vel:
            return
        cmd = Twist()
        if not self._target_visible or self._center_x is None:
            self._pub_cmd.publish(cmd)
            return
        # Proportional: virar em direção ao alvo (center_x); avançar se alvo no centro
        k_angular = 2.0
        k_linear = 0.3
        cmd.angular.z = max(
            -self._max_angular,
            min(self._max_angular, -self._center_x * k_angular)
        )
        cmd.linear.x = max(
            0.0,
            min(self._max_linear, self._max_linear - abs(self._center_x) * k_linear)
        )
        self._pub_cmd.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    if not HAS_OPENCV:
        return
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node._pub_cmd is not None:
            node._pub_cmd.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
