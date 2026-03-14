#!/usr/bin/env python3
"""
Task 4 — Breadcrumb Trail Follower
=====================================
Husky records its exact path as a queue of waypoints.
TurtleBot3 works through that queue in order, tracing Husky's
exact footprint with a ~1 m delay gap.

Architecture:
  Husky odom → /leader/pose (via leader_pose_publisher)
      ↓
  breadcrumb_follower
      - Records a new waypoint every time Husky moves > RECORD_DIST m
        OR rotates > RECORD_ANGLE rad
      - TB3 drives to the oldest waypoint in the queue
      - Pops waypoint when within ARRIVE_TOLERANCE m
      - Keeps MIN_QUEUE_SIZE waypoints buffered so TB3 always stays
        ~1 m behind Husky (not right on top of it)
      ↓
  /turtlebot3/cmd_vel

Control law (same proportional as follower_controller but target is
the front of the waypoint queue, not Husky's live position):
  - Angular: face the waypoint first
  - Linear: drive forward once heading error is small enough

Node:    breadcrumb_follower
Sub:     /leader/pose          (geometry_msgs/PoseStamped)
Sub:     /turtlebot3/odom      (nav_msgs/Odometry)
Pub:     /turtlebot3/cmd_vel   (geometry_msgs/Twist)
"""

import math
from collections import deque

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry


class BreadcrumbFollower(Node):

    # ── Waypoint recording thresholds ────────────────────────────────────
    RECORD_DIST   = 0.08   # m   — record new waypoint every this distance
    RECORD_ANGLE  = 0.087  # rad — or every ~5° of rotation

    # ── Queue buffer — keeps TB3 behind Husky ────────────────────────────
    # TB3 only consumes the front waypoint when the queue is longer than
    # this, so TB3 trails by at least MIN_QUEUE_SIZE * RECORD_DIST metres.
    # At 0.15 m spacing, 7 waypoints ≈ 1.05 m gap.
    MIN_QUEUE_SIZE = 4

    # ── Arrival / control ────────────────────────────────────────────────
    ARRIVE_TOLERANCE = 0.08  # m   — pop waypoint when within this radius
    MAX_LINEAR       = 0.22  # m/s
    MAX_ANGULAR      = 1.20  # rad/s
    K_LINEAR         = 0.60
    K_ANGULAR        = 1.40
    HEADING_GATE     = 0.35  # rad — drive forward only when roughly facing wp
    TIMEOUT_S        = 1.50  # s   — stop if /leader/pose goes silent
    CTRL_HZ          = 20.0  # Hz
    # ─────────────────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__('breadcrumb_follower')

        self._waypoints: deque = deque()   # (x, y) tuples, oldest first

        # Last recorded Husky pose for delta calculation
        self._last_recorded_x: float | None = None
        self._last_recorded_y: float | None = None
        self._last_recorded_yaw: float | None = None

        self._follower_pose   = None
        self._last_leader_ts  = None

        # Subscriptions
        self.create_subscription(
            PoseStamped, '/leader/pose', self._leader_callback, 10)
        self.create_subscription(
            Odometry, '/turtlebot3/odom', self._odom_callback, 10)

        # Publisher
        self._pub = self.create_publisher(Twist, '/turtlebot3/cmd_vel', 10)

        # Control loop
        self.create_timer(1.0 / self.CTRL_HZ, self._control_loop)

        self.get_logger().info(
            f'BreadcrumbFollower ready — '
            f'record every {self.RECORD_DIST} m / {math.degrees(self.RECORD_ANGLE):.0f}°, '
            f'min queue={self.MIN_QUEUE_SIZE} waypoints (~'
            f'{self.MIN_QUEUE_SIZE * self.RECORD_DIST:.2f} m gap)'
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _yaw(q) -> float:
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny, cosy)

    @staticmethod
    def _wrap(a: float) -> float:
        while a >  math.pi: a -= 2.0 * math.pi
        while a < -math.pi: a += 2.0 * math.pi
        return a

    def _stop(self):
        self._pub.publish(Twist())

    # ── Callbacks ────────────────────────────────────────────────────────

    def _leader_callback(self, msg: PoseStamped) -> None:
        self._last_leader_ts = self.get_clock().now()

        lx = msg.pose.position.x
        ly = msg.pose.position.y
        lyaw = self._yaw(msg.pose.orientation)

        # First pose — just record it
        if self._last_recorded_x is None:
            self._record(lx, ly)
            self._last_recorded_x   = lx
            self._last_recorded_y   = ly
            self._last_recorded_yaw = lyaw
            return

        dist  = math.hypot(lx - self._last_recorded_x,
                           ly - self._last_recorded_y)
        dangle = abs(self._wrap(lyaw - self._last_recorded_yaw))

        if dist >= self.RECORD_DIST or dangle >= self.RECORD_ANGLE:
            self._record(lx, ly)
            self._last_recorded_x   = lx
            self._last_recorded_y   = ly
            self._last_recorded_yaw = lyaw

    def _record(self, x: float, y: float) -> None:
        self._waypoints.append((x, y))

    def _odom_callback(self, msg: Odometry) -> None:
        self._follower_pose = msg.pose.pose

    # ── Control loop ─────────────────────────────────────────────────────

    def _control_loop(self) -> None:

        # Guard: no data
        if self._last_leader_ts is None or self._follower_pose is None:
            return

        # Guard: leader timeout
        elapsed = (self.get_clock().now() - self._last_leader_ts).nanoseconds * 1e-9
        if elapsed > self.TIMEOUT_S:
            self.get_logger().warn(
                f'Leader silent {elapsed:.1f} s — stopping.',
                throttle_duration_sec=2.0)
            self._stop()
            return

        # Guard: queue too short — wait for more breadcrumbs
        if len(self._waypoints) <= self.MIN_QUEUE_SIZE:
            self._stop()
            return

        # Current follower state
        fx   = self._follower_pose.position.x
        fy   = self._follower_pose.position.y
        fyaw = self._yaw(self._follower_pose.orientation)

        # Target: oldest waypoint in queue
        tx, ty = self._waypoints[0]

        dx       = tx - fx
        dy       = ty - fy
        dist     = math.hypot(dx, dy)
        bearing  = math.atan2(dy, dx)
        heading_err = self._wrap(bearing - fyaw)

        # Arrived at waypoint — pop and move to next
        if dist < self.ARRIVE_TOLERANCE:
            self._waypoints.popleft()
            self.get_logger().debug(
                f'Waypoint reached. Queue: {len(self._waypoints)}')
            return

        # ── Proportional control ────────────────────────────────────────
        cmd = Twist()

        # Angular — always rotate toward waypoint
        cmd.angular.z = max(-self.MAX_ANGULAR,
                            min(self.K_ANGULAR * heading_err, self.MAX_ANGULAR))

        # Linear — only drive forward when roughly facing waypoint
        if abs(heading_err) < self.HEADING_GATE:
            cmd.linear.x = min(self.K_LINEAR * dist, self.MAX_LINEAR)
        else:
            cmd.linear.x = 0.0   # rotate in place first

        self._pub.publish(cmd)

        self.get_logger().debug(
            f'Queue={len(self._waypoints)} dist={dist:.2f}m '
            f'heading_err={math.degrees(heading_err):.1f}°',
            throttle_duration_sec=1.0)

    def destroy_node(self):
        self._stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BreadcrumbFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
