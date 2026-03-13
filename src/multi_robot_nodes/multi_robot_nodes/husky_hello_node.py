"""
husky_hello_node — Husky side of cross-namespace communication.

Publishes:  /shared_comms  (String) — "Husky: Hello from a200_0000 [seq]"
Subscribes: /shared_comms  (String) — Listens for TurtleBot3 messages

Demonstrates bidirectional inter-robot ROS 2 communication
across namespaces in the same workspace.

Usage:
  ros2 run multi_robot_nodes husky_hello_node --ros-args -r __ns:=/a200_0000
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class HuskyHelloNode(Node):

    def __init__(self):
        super().__init__('husky_hello_node')
        self.seq = 0

        # Publish on global /shared_comms (absolute topic — no namespace prefix)
        self.publisher = self.create_publisher(String, '/shared_comms', 10)

        # Subscribe to the same global topic
        self.subscription = self.create_subscription(
            String,
            '/shared_comms',
            self.listener_callback,
            10,
        )

        # Publish at 1 Hz
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info('Husky hello node started — publishing and listening on /shared_comms')

    def timer_callback(self):
        msg = String()
        msg.data = f'Husky: Hello from a200_0000 [{self.seq}]'
        self.publisher.publish(msg)
        self.seq += 1

    def listener_callback(self, msg: String):
        # Only log messages from the OTHER robot
        if msg.data.startswith('TB3:'):
            self.get_logger().info(f'Husky received: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = HuskyHelloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
