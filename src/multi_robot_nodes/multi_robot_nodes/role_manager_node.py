import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseStamped


class RoleManagerNode(Node):
    """
    Manages leader/follower role switching between Husky and TB3.

    Listens on /role_switch for a string: "husky" or "turtlebot3"
    On switch:
      1. Publishes zero velocity to both robots (safety stop)
      2. Updates internal role state
      3. Publishes new role assignment on /current_leader (TRANSIENT_LOCAL)

    /current_leader subscribers (e.g. leader_pose_publisher) read this
    to know whose odom to forward onto /leader/pose.
    """

    VALID_ROLES = ('husky', 'turtlebot3')

    def __init__(self):
        super().__init__('role_manager_node')

        self._current_leader = 'husky'  # Default: Husky leads

        # TRANSIENT_LOCAL so late-joining nodes get current role immediately
        latching_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        # Publisher: broadcast current leader to all nodes that care
        self._leader_pub = self.create_publisher(
            String, '/current_leader', latching_qos
        )

        # Publishers: zero-velocity stops on switch
        self._husky_cmd_pub = self.create_publisher(
            Twist, '/a200_0000/cmd_vel', 10
        )
        self._tb3_cmd_pub = self.create_publisher(
            Twist, '/turtlebot3/cmd_vel', 10
        )

        # Subscriber: receive role switch commands
        self._switch_sub = self.create_subscription(
            String, '/role_switch', self._switch_callback, 10
        )

        # Publish initial role on startup so all nodes start in sync
        self._publish_current_role()
        self.get_logger().info(
            f'RoleManagerNode started — current leader: {self._current_leader}'
        )

    def _switch_callback(self, msg: String):
        requested = msg.data.strip().lower()

        if requested not in self.VALID_ROLES:
            self.get_logger().warn(
                f'Invalid role switch request: "{requested}" '
                f'— valid values: {self.VALID_ROLES}'
            )
            return

        if requested == self._current_leader:
            self.get_logger().info(
                f'Role switch ignored — "{requested}" is already leader'
            )
            return

        self.get_logger().info(
            f'Role switch: {self._current_leader} → {requested}'
        )

        # Step 1: Safety stop both robots
        self._stop_all()

        # Step 2: Update role
        self._current_leader = requested

        # Step 3: Broadcast new role
        self._publish_current_role()

        self.get_logger().info(
            f'Role switch complete — new leader: {self._current_leader}'
        )

    def _stop_all(self):
        """Publish zero velocity to both robots."""
        stop = Twist()
        self._husky_cmd_pub.publish(stop)
        self._tb3_cmd_pub.publish(stop)
        self.get_logger().debug('Safety stop published to both robots')

    def _publish_current_role(self):
        msg = String()
        msg.data = self._current_leader
        self._leader_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RoleManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
