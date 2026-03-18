"""
odom_to_tf_broadcaster — Converts odometry to TF for TurtleBot3.

Subscribes to /turtlebot3/odom and publishes odom → base_footprint TF.
This replaces the unreliable Ignition TF bridge which produces
non-monotonic timestamps that SLAM and Nav2 reject.

Usage (standalone):
  ros2 run multi_robot_nodes odom_to_tf_broadcaster

Usage (via launch file):
  Included in task3_dual_spawn.launch.py automatically.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomToTfBroadcaster(Node):

    def __init__(self):
        super().__init__('odom_to_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)

        self.subscription = self.create_subscription(
            Odometry,
            'odom',       # Relative — resolved under namespace (/turtlebot3/odom)
            self.odom_callback,
            10,
        )
        self.get_logger().info('odom_to_tf_broadcaster started — listening on odom')

    def odom_callback(self, msg: Odometry):
        t = TransformStamped()

        # Use the odom message timestamp for consistency
        t.header.stamp = msg.header.stamp
        t.header.frame_id = msg.header.frame_id        # "odom"
        t.child_frame_id = msg.child_frame_id           # "base_footprint"

        # If frame IDs are empty (some Ignition bridge versions), set defaults
        if not t.header.frame_id:
            t.header.frame_id = 'odom'
        if not t.child_frame_id:
            t.child_frame_id = 'base_footprint'

        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTfBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
