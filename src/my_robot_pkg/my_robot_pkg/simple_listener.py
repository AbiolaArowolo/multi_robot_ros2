import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SimpleListener(Node):
    def __init__(self):
        super().__init__('simple_listener')
        self.subscription = self.create_subscription(
            String, '/intern_chatter', self.listener_callback, 10)

    def listener_callback(self, msg):
        self.get_logger().info(f'Heard: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = SimpleListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
