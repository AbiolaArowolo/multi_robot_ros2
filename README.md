# Multi-Robot Cooperative Navigation — ROS 2 Humble

**Student:** Ayodele Abiola Arowolo (Incoming Masters)
**Direct Mentor:** Yong Ann Voeurn (PhD Candidate)
**Supervisor:** Prof. Doyun Lee — Georgia Southern University
**ROS Distribution:** ROS 2 Humble | **Simulator:** Ignition Gazebo 6 (Fortress)

---

## Project Overview

This project implements a cooperative multi-robot navigation system using a **Clearpath Husky A200** and a **TurtleBot3** in a simulated warehouse environment. The system integrates SLAM-based mapping, AMCL localization, Nav2 autonomous navigation, inter-robot goal sharing, and dynamic leader-follower role switching.

---

## Task Progress

| Task | Description | Status |
|------|-------------|--------|
| Task 1 | Basic ROS 2 pub/sub nodes (`my_robot_pkg`) | ✅ Complete |
| Task 2A | Husky SLAM — warehouse map built and saved | ✅ Complete |
| Task 2B | Husky Nav2 — AMCL localization + autonomous goal navigation | ✅ Complete |
| Task 3 | TurtleBot3 + Husky dual spawn, bridged topics, hello nodes | ✅ Complete |
| Task 4 | Leader-follower controller (Husky leads, TurtleBot3 follows) | ⏳ Pending |
| Task 5 | Goal sharing node + role manager node | ⏳ Pending |

---

## Repository Structure

\`\`\`
~/ros2_ws/
├── src/
│   ├── multi_robot_bringup/
│   │   ├── launch/
│   │   │   ├── husky_slam_warehouse.launch.py
│   │   │   ├── husky_nav2.launch.py
│   │   │   └── task3_dual_spawn.launch.py
│   │   ├── config/
│   │   │   ├── husky_slam_params.yaml
│   │   │   └── husky_nav2_params.yaml
│   │   ├── models/
│   │   │   └── turtlebot3_burger/
│   │   │       ├── model.sdf
│   │   │       └── model.config
│   │   └── setup.py
│   ├── multi_robot_nodes/
│   │   └── multi_robot_nodes/
│   │       ├── husky_hello_node.py
│   │       ├── tb3_hello_node.py
│   │       └── odom_to_tf_broadcaster.py
│   └── my_robot_pkg/
└── maps/
    ├── husky_map.pgm / .yaml
    └── turtlebot3_map.pgm / .yaml
\`\`\`

---

## Environment Setup

\`\`\`bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install ros-humble-slam-toolbox
sudo apt install ros-humble-clearpath-*
sudo apt install ros-humble-turtlebot3*

cd ~/ros2_ws && colcon build --symlink-install

source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/ros2_ws/install/setup.bash
\`\`\`

---

## Task 2A — Husky SLAM Mapping

\`\`\`bash
ros2 launch clearpath_gz simulation.launch.py world:=warehouse
ros2 launch multi_robot_bringup husky_slam_warehouse.launch.py
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/husky_map
\`\`\`

---

## Task 2B — Husky Nav2 Autonomous Navigation

\`\`\`bash
ros2 launch clearpath_gz simulation.launch.py world:=warehouse
ros2 launch multi_robot_bringup husky_nav2.launch.py
ros2 action send_goal /a200_0000/navigate_to_pose nav2_msgs/action/NavigateToPose '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
\`\`\`

---

## Task 3 — Dual Robot Spawn + Communication

\`\`\`bash
ros2 launch multi_robot_bringup task3_dual_spawn.launch.py
ros2 topic list | grep turtlebot3
ros2 topic pub /turtlebot3/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}' --rate 10
\`\`\`

---

## Useful Commands

\`\`\`bash
killros
ros2 lifecycle list /a200_0000/bt_navigator
ign topic -l | grep -v "__" | grep -v "world" | grep -v "gui" | grep -v "stats"
cd ~/ros2_ws && colcon build --symlink-install
\`\`\`

---

## Known Warnings (Safe to Ignore)

| Warning | Reason |
|---------|--------|
| \`transient local durability falling back to volatile\` | QoS mismatch on TF — harmless |
| \`QStandardPaths: runtime directory not owned by UID\` | WSL2 display warning |
| \`Unable to deserialize sdf::Model\` | Clearpath Ignition model warning |
| TB3 scan rate ~1.3 Hz (nominal 5 Hz) | WSL2 software rendering throttle |

---

*Academic project — Georgia Southern University. Not licensed for commercial use.*
