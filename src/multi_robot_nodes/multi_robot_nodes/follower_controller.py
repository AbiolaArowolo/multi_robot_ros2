#!/usr/bin/env python3
"""
Task 4 — Follower Controller Node
=====================================
Subscribes to /leader/pose and /turtlebot3/odom. Computes a proportional
control law to keep TurtleBot3 at a fixed following distance behind the
Husky leader.

Control law (20 Hz loop):
  1. Compute Euclidean distance and bearing from follower to leader.
  2. Linear velocity ∝ (distance − desired_distance), clamped to MAX_LINEAR.
  3. Angular velocity ∝ heading_error (angle from follower heading to
     bearing-to-leader), clamped to MAX_ANGULAR.
  4. Safety stop if /leader/pose has not been received for TIMEOUT_S seconds.
  5. Slow back-off if follower is too close to the leader.

Coordinate assumption:
  Both robots start at the same Gazebo world origin, so their respective
  odom frames coincide at t=0.  Pose comparisons are therefore valid for
  short demonstrations. Long-run drift between the two odom frames is a
  documented limitation (see technical note).

Node:    follower_controller
Sub:     /leader/pose          (geometry_msgs/PoseStamped)
Sub:     /turtlebot3/odom      (nav_msgs/Odometry)
Pub:     /turtlebot3/cmd_vel   (geometry_msgs/Twist)
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry


class FollowerController(Node):

    # ── Tunable parameters ──────────────────────────────────────────────
    DESIRED_DIST  = 1.2    # m   — target following distance
    DEADBAND      = 0.15   # m   — tolerance band around desired distance
    MAX_LINEAR    = 0.18   # m/s — maximum forward speed
    BACK_OFF_MAX  = 0.10   # m/s — maximum reverse speed (safety)
    MAX_ANGULAR   = 1.00   # rad/s — maximum rotation speed
    K_LINEAR      = 0.35   # proportional gain — linear
    K_ANGULAR     = 1.20   # proportional gain — angular
    TIMEOUT_S     = 1.50   # s   — stop follower if leader goes silent
    CTRL_HZ       = 20.0   # Hz  — control loop rate
    # ────────────────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__('follower_controller')

        self._leader_pose     = None
        self._follower_pose   = None
        self._last_leader_ts  = None   # rclpy.time.Time

        # Subscriptions
        self._sub_leader = self.create_subscription(
            PoseStamped,
            '/leader/pose',
            self._leader_callback,
            10,
        )
        self._sub_odom = self.create_subscription(
            Odometry,
            '/turtlebot3/odom',
            self._odom_callback,
            10,
        )

        # Publisher
        self._pub_cmd = self.create_publisher(Twist, '/turtlebot3/cmd_vel', 10)

        # Control loop timer
        self._timer = self.create_timer(1.0 / self.CTRL_HZ, self._control_loop)

        self.get_logger().info(
            f'FollowerController ready — '
            f'desired dist={self.DESIRED_DIST} m, '
            f'deadband=±{self.DEADBAND} m, '
            f'timeout={self.TIMEOUT_S} s'
        )

    # ── Callbacks ────────────────────────────────────────────────────────

    def _leader_callback(self, msg: PoseStamped) -> None:
        self._leader_pose    = msg.pose
        self._last_leader_ts = self.get_clock().now()

    def _odom_callback(self, msg: Odometry) -> None:
        self._follower_pose = msg.pose.pose

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _yaw_from_quaternion(q) -> float:
        """Extract yaw (rad) from a geometry_msgs/Quaternion."""
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny, cosy)

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Wrap angle to (−π, π]."""
        while angle >  math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def _publish_stop(self) -> None:
        self._pub_cmd.publish(Twist())

    # ── Control loop ─────────────────────────────────────────────────────

    def _control_loop(self) -> None:

        # Guard: no data yet
        if self._last_leader_ts is None or self._follower_pose is None:
            return

        # Guard: leader timeout → safety stop
        elapsed_s = (
            self.get_clock().now() - self._last_leader_ts
        ).nanoseconds * 1e-9

        if elapsed_s > self.TIMEOUT_S:
            self.get_logger().warn(
                f'Leader silent for {elapsed_s:.1f} s — stopping follower.',
                throttle_duration_sec=2.0,
            )
            self._publish_stop()
            return

        # ── Geometry ────────────────────────────────────────────────────
        lx = self._leader_pose.position.x
        ly = self._leader_pose.position.y
        fx = self._follower_pose.position.x
        fy = self._follower_pose.position.y

        dx       = lx - fx
        dy       = ly - fy
        distance = math.hypot(dx, dy)

        follower_yaw    = self._yaw_from_quaternion(self._follower_pose.orientation)
        angle_to_leader = math.atan2(dy, dx)
        heading_error   = self._normalize_angle(angle_to_leader - follower_yaw)

        # ── Proportional control ────────────────────────────────────────
        cmd = Twist()

        dist_error = distance - self.DESIRED_DIST

        if dist_error > self.DEADBAND:
            # Too far — drive toward leader
            cmd.linear.x = min(self.K_LINEAR * dist_error, self.MAX_LINEAR)
        elif dist_error < -self.DEADBAND:
            # Too close — back off slowly
            cmd.linear.x = max(self.K_LINEAR * dist_error, -self.BACK_OFF_MAX)
        else:
            cmd.linear.x = 0.0   # within deadband — no linear motion

        # Always rotate to face the leader
        cmd.angular.z = max(
            -self.MAX_ANGULAR,
            min(self.K_ANGULAR * heading_error, self.MAX_ANGULAR),
        )

        self._pub_cmd.publish(cmd)

    # ── Cleanup ──────────────────────────────────────────────────────────

    def destroy_node(self):
        self._publish_stop()   # ensure robot stops on shutdown
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FollowerController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
