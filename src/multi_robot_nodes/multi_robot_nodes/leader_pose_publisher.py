#!/usr/bin/env python3
"""
Task 4 — Leader Pose Publisher
=================================
Subscribes to Husky A200 odometry (/a200_0000/odom) and republishes as
geometry_msgs/PoseStamped on /leader/pose.

This decouples the leader identity from the follower: the follower only
ever knows about /leader/pose, so swapping leaders later (Task 5) only
requires changing which node publishes there.

Node: leader_pose_publisher
Sub: /a200_0000/odom  (nav_msgs/Odometry)
Pub: /leader/pose     (geometry_msgs/PoseStamped)
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped


class LeaderPosePublisher(Node):

    def __init__(self):
        super().__init__('leader_pose_publisher')

        self._sub = self.create_subscription(
            Odometry,
            '/a200_0000/platform/odom/filtered',
            self._odom_callback,
            10,
        )
        self._pub = self.create_publisher(PoseStamped, '/leader/pose', 10)

        self.get_logger().info(
            'LeaderPosePublisher ready — '
            'subscribing to /a200_0000/odom, publishing /leader/pose'
        )

    def _odom_callback(self, msg: Odometry) -> None:
        ps = PoseStamped()
        ps.header = msg.header
        ps.header.frame_id = 'odom'   # Husky lives in its odom frame
        ps.pose = msg.pose.pose
        self._pub.publish(ps)


def main(args=None):
    rclpy.init(args=args)
    node = LeaderPosePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
