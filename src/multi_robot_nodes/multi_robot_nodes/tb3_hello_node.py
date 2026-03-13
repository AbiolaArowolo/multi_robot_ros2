"""
tb3_hello_node — TurtleBot3 side of cross-namespace communication.

Publishes:  /shared_comms  (String) — "TB3: Hello from turtlebot3 [seq]"
Subscribes: /shared_comms  (String) — Listens for Husky messages

Demonstrates bidirectional inter-robot ROS 2 communication
across namespaces in the same workspace.

Usage:
  ros2 run multi_robot_nodes tb3_hello_node --ros-args -r __ns:=/turtlebot3
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Tb3HelloNode(Node):

    def __init__(self):
        super().__init__('tb3_hello_node')
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
        self.get_logger().info('TB3 hello node started — publishing and listening on /shared_comms')

    def timer_callback(self):
        msg = String()
        msg.data = f'TB3: Hello from turtlebot3 [{self.seq}]'
        self.publisher.publish(msg)
        self.seq += 1

    def listener_callback(self, msg: String):
        # Only log messages from the OTHER robot
        if msg.data.startswith('Husky:'):
            self.get_logger().info(f'TB3 received: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = Tb3HelloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
