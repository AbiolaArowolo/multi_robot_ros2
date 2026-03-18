import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action._navigate_to_pose import NavigateToPose_FeedbackMessage
from action_msgs.msg import GoalStatusArray, GoalStatus


class GoalSharingNode(Node):
    """
    Watches Husky's navigate_to_pose action.
    Caches the current pose from action feedback.
    When Husky SUCCEEDS, publishes that pose to /shared_goal
    with TRANSIENT_LOCAL QoS so TB3 gets it even if late.
    """

    def __init__(self):
        super().__init__('goal_sharing_node')

        latching_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        self._shared_goal_pub = self.create_publisher(
            PoseStamped, '/shared_goal', latching_qos
        )

        # Cache Husky's pose from action feedback
        self._last_pose: PoseStamped | None = None

        # Subscribe to action feedback to track current pose
        self._feedback_sub = self.create_subscription(
            NavigateToPose_FeedbackMessage,
            '/a200_0000/navigate_to_pose/_action/feedback',
            self._feedback_callback,
            10,
        )

        # Subscribe to goal status to detect SUCCEEDED
        self._status_sub = self.create_subscription(
            GoalStatusArray,
            '/a200_0000/navigate_to_pose/_action/status',
            self._status_callback,
            10,
        )

        self._last_succeeded_id = None
        self.get_logger().info('GoalSharingNode started — watching Husky goals')

    def _feedback_callback(self, msg: NavigateToPose_FeedbackMessage):
        """Cache Husky's current pose from action feedback."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose = msg.feedback.current_pose.pose
        self._last_pose = pose

    def _status_callback(self, msg: GoalStatusArray):
        """When any goal reaches SUCCEEDED, share Husky's pose with TB3."""
        for status in msg.status_list:
            if status.status == GoalStatus.STATUS_SUCCEEDED:
                goal_id = bytes(status.goal_info.goal_id.uuid).hex()
                if goal_id == self._last_succeeded_id:
                    continue  # Already handled this goal
                if self._last_pose is not None:
                    self.get_logger().info(
                        f'Husky reached goal — sharing with TB3: '
                        f'x={self._last_pose.pose.position.x:.2f} '
                        f'y={self._last_pose.pose.position.y:.2f}'
                    )
                    self._shared_goal_pub.publish(self._last_pose)
                    self._last_succeeded_id = goal_id
                break


def main(args=None):
    rclpy.init(args=args)
    node = GoalSharingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
