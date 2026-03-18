# Multi-Robot Cooperative Navigation — ROS 2 Humble

**Student:** Ayodele Abiola Arowolo (Incoming Masters)
**Direct Mentor:** Yong Ann Voeurn (PhD Candidate)
**Supervisor:** Prof. Doyun Lee — Georgia Southern University
**ROS Distribution:** ROS 2 Humble | **Simulator:** Ignition Gazebo 6 (Fortress)

---

## Project Overview

This project implements a cooperative multi-robot navigation system using a **Clearpath Husky A200** and a **TurtleBot3 Burger** in a simulated warehouse environment. The system integrates SLAM-based mapping, AMCL localization, Nav2 autonomous navigation, leader-follower control with exact footprint tracking, inter-robot goal sharing, and dynamic role switching.

---

## Task Progress

| Task | Description | Status | Branch |
|------|-------------|--------|--------|
| Task 1 | Basic ROS 2 pub/sub nodes (`my_robot_pkg`) | Complete | main |
| Task 2A | Husky SLAM — warehouse map built and saved | Complete | task/2b-husky-slam-nav2 |
| Task 2B | Husky Nav2 — AMCL localization + autonomous goal navigation | Complete | task/2b-husky-slam-nav2 |
| Task 3 | TurtleBot3 + Husky dual spawn, bridged topics, hello nodes | Complete | task/3-dual-spawn |
| Task 4 | Leader-follower controller — proportional + breadcrumb trail | Complete | task/4-leader-follower |
| Task 5 | TB3 Nav2 + goal sharing node + role manager node | Complete | task/5-cooperative-nav |

---

## Repository Structure
```
~/ros2_ws/
├── src/
│   ├── multi_robot_bringup/          # Main launch & config package
│   │   ├── launch/
│   │   │   ├── husky_slam_warehouse.launch.py      # Task 2A — SLAM mapping
│   │   │   ├── husky_nav2.launch.py                # Task 2B — Nav2 navigation
│   │   │   ├── task3_dual_spawn.launch.py           # Task 3 — both robots
│   │   │   ├── task4_leader_follower.launch.py      # Task 4 — leader-follower
│   │   │   ├── tb3_nav2.launch.py                  # Task 5 — TB3 Nav2 stack
│   │   │   └── task5_cooperative_nav.launch.py     # Task 5 — unified launch
│   │   ├── config/
│   │   │   ├── husky_slam_params.yaml
│   │   │   ├── husky_nav2_params.yaml
│   │   │   └── tb3_nav2_params.yaml                # Task 5 — TB3 Nav2 config
│   │   ├── models/
│   │   │   └── turtlebot3_burger/
│   │   │       ├── model.sdf                       # Native Ignition SDF
│   │   │       └── model.config
│   │   └── setup.py
│   ├── multi_robot_nodes/            # All Python nodes
│   │   └── multi_robot_nodes/
│   │       ├── husky_hello_node.py                 # Task 3 cross-namespace pub/sub
│   │       ├── tb3_hello_node.py                   # Task 3 cross-namespace pub/sub
│   │       ├── odom_to_tf_broadcaster.py           # Task 3 odom to TF
│   │       ├── leader_pose_publisher.py            # Task 4 — Husky odom to /leader/pose
│   │       ├── follower_controller.py              # Task 4 — proportional follower
│   │       ├── breadcrumb_follower.py              # Task 4 — exact footprint tracker
│   │       ├── goal_sharing_node.py                # Task 5 — goal sharing
│   │       └── role_manager_node.py                # Task 5 — role switching
│   └── my_robot_pkg/                 # Task 1 — do not modify
└── maps/
    ├── husky_map.pgm / .yaml         # Full warehouse map (used by both robots)
    └── turtlebot3_map.pgm / .yaml
```

---

## Environment Setup

### Prerequisites
```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
sudo apt install ros-humble-slam-toolbox
sudo apt install ros-humble-clearpath-*
sudo apt install ros-humble-turtlebot3*
```

### Build
```bash
cd ~/ros2_ws && colcon build --symlink-install
```

### Source (every terminal)
```bash
source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
```

---

## Task 2A — Husky SLAM Mapping

Builds a 2D occupancy grid map of the warehouse using `slam_toolbox` in `online_async` mode with the Ceres solver.
```bash
# Terminal 1 — Gazebo
ros2 launch clearpath_gz simulation.launch.py world:=warehouse

# Terminal 2 — SLAM
ros2 launch multi_robot_bringup husky_slam_warehouse.launch.py

# Save map
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/husky_map
```

---

## Task 2B — Husky Nav2 Autonomous Navigation

Deploys Nav2 with AMCL localization on the pre-built warehouse map.
```bash
# Terminal 1 — Gazebo
ros2 launch clearpath_gz simulation.launch.py world:=warehouse

# Terminal 2 — Nav2
ros2 launch multi_robot_bringup husky_nav2.launch.py
```

Wait for:
```
[lifecycle_manager_localization]: Managed nodes are active
[lifecycle_manager_navigation]: Managed nodes are active
```
```bash
# Send navigation goal
ros2 action send_goal /a200_0000/navigate_to_pose \
  nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
```

---

## Task 3 — Dual Robot Spawn + Communication

Spawns Husky A200 and TurtleBot3 simultaneously in the Ignition warehouse. All TB3 topics bridged under `/turtlebot3/`. Cross-namespace hello nodes confirm bidirectional communication.
```bash
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch multi_robot_bringup task3_dual_spawn.launch.py
```

Wait 2-3 minutes on WSL2. Then verify:
```bash
ros2 topic list | grep turtlebot3
# Expected: /turtlebot3/cmd_vel, /turtlebot3/odom, /turtlebot3/scan,
#           /turtlebot3/joint_states, /turtlebot3/robot_description

# Test TB3 movement
ros2 topic pub /turtlebot3/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}' --rate 10
```

### Task 3 Key Findings

| Finding | Detail |
|---------|--------|
| DiffDrive subscribes on `/turtlebot3/cmd_vel` | Absolute topic set in `model.sdf` |
| TB3 odom bridges from Ignition `/odom` | Not `/model/turtlebot3/odometry` |
| TB3 link names prefixed `tb3_` | Prevents cross-model joint binding with Husky |
| Bridge remappings require absolute paths | Leading `/` prevents namespace auto-prefix |

---

## Task 4 — Leader-Follower Control

Husky A200 acts as leader. TurtleBot3 follows using two controller modes.
```bash
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch multi_robot_bringup task4_leader_follower.launch.py
```

**Mode 1 — Proportional Follower**

Drives TB3 toward Husky's current position, maintaining 1.2 m gap.
```bash
ros2 run multi_robot_nodes follower_controller
```

**Mode 2 — Breadcrumb Trail Follower (Exact Footprint Tracking)**

Husky records waypoints every 0.08 m. TB3 works through the queue in order, tracing Husky's exact path with a ~0.32 m delay gap.
```bash
ros2 run multi_robot_nodes breadcrumb_follower
```

**Drive Husky**
```bash
# Forward
ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.15}}' --rate 10

# Turn
ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.15}, angular: {z: 0.4}}' --rate 10

# Stop
ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist '{}' --once
```

### Task 4 Architecture
```
/a200_0000/platform/odom/filtered
          |
          v
  leader_pose_publisher --> /leader/pose
                                 |
             +-------------------+
             v                   v
  follower_controller    breadcrumb_follower
             |                   |
             +--------+----------+
                      v
          /turtlebot3/cmd_vel
```

### Task 4 Key Parameters

| Parameter | Value | Node |
|-----------|-------|------|
| Following distance | 1.2 m | follower_controller |
| Max linear speed | 0.22 m/s | breadcrumb_follower |
| Waypoint spacing | 0.08 m | breadcrumb_follower |
| Queue buffer | 4 waypoints (~0.32 m gap) | breadcrumb_follower |
| Leader timeout | 1.5 s | both nodes |

---

## Task 5 — Cooperative Navigation

Deploys Nav2 on both robots, shares Husky's reached goals with TB3, and supports dynamic role switching at runtime.
```bash
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch multi_robot_bringup task5_cooperative_nav.launch.py
```

Wait for both lifecycle managers to report `Managed nodes are active`, then:
```bash
# Send Husky a navigation goal
ros2 action send_goal /a200_0000/navigate_to_pose \
  nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 0.5, y: 1.0, z: 0.0}, orientation: {w: 1.0}}}}'

# Watch for TB3 receiving the shared goal after Husky succeeds
ros2 topic echo /shared_goal geometry_msgs/msg/PoseStamped \
  --qos-durability transient_local --qos-reliability reliable

# Switch roles at runtime
ros2 topic pub --once /role_switch std_msgs/msg/String '{data: "turtlebot3"}'

# Verify role switched
ros2 topic echo /current_leader std_msgs/msg/String \
  --qos-durability transient_local --qos-reliability reliable --once
```

### Task 5 Architecture
```
[Husky Nav2] --> action feedback/status --> [goal_sharing_node] --> /shared_goal --> [TB3 Nav2]
[role_manager_node] <-- /role_switch --> safety stop both robots --> /current_leader
```

### Task 5 Key Technical Notes

| Finding | Detail |
|---------|--------|
| TB3 uses Husky map | TB3 map too small — both robots share `husky_map.yaml` |
| TB3 base frame | `tb3_base_footprint` — prefixed to avoid Husky link collision |
| Static TF required | `robot_state_publisher` URDF uses stock names — static transforms bridge to `tb3_` prefixed names |
| Goal sharing QoS | TRANSIENT_LOCAL + KEEP_LAST — late subscribers receive last goal |
| Role switch safety | Zero velocity published to both robots before role change |
| Goal capture method | Action feedback used — not `/goal_pose` which only fires from RViz |

---

## Confirmed Topic Map

| Topic | Source | Notes |
|-------|--------|-------|
| `/a200_0000/platform/odom/filtered` | Husky EKF | Real odom — `/a200_0000/odom` is empty |
| `/a200_0000/cmd_vel` | Drive Husky | |
| `/turtlebot3/cmd_vel` | Drive TB3 | Absolute topic in `model.sdf` |
| `/turtlebot3/odom` | Bridged from `/odom` | Global Ignition topic |
| `/turtlebot3/scan` | Bridged from `/scan` | Global Ignition topic |
| `/leader/pose` | `leader_pose_publisher` | System-level coordination channel |
| `/shared_goal` | `goal_sharing_node` | TRANSIENT_LOCAL — Husky's reached pose |
| `/current_leader` | `role_manager_node` | TRANSIENT_LOCAL — active leader identity |
| `/role_switch` | External command | Accepts "husky" or "turtlebot3" |

---

## Useful Commands
```bash
# Kill all ROS processes
killros

# Build specific packages
cd ~/ros2_ws && colcon build --symlink-install \
  --packages-select multi_robot_bringup multi_robot_nodes

# Check Ignition topics
ign topic -l | grep -v "__" | grep -v "world" | grep -v "gui" | grep -v "stats"

# Check lifecycle states
ros2 lifecycle list /a200_0000/bt_navigator
ros2 lifecycle list /turtlebot3/bt_navigator

# Emergency stop both robots
ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist '{}' --once
ros2 topic pub /turtlebot3/cmd_vel geometry_msgs/msg/Twist '{}' --once
```

---

## Known Warnings (Safe to Ignore)

| Warning | Reason |
|---------|--------|
| `transient local durability falling back to volatile` | QoS mismatch on TF — harmless |
| `QStandardPaths: runtime directory not owned by UID` | WSL2 display warning |
| `Unable to deserialize sdf::Model` | Clearpath Ignition model warning |
| `Attribute value string not set` | URDF parser cosmetic |
| `Anti-aliasing level '8' not supported` | WSL2 GPU limitation |
| TB3 scan rate ~1.3 Hz (nominal 5 Hz) | WSL2 software rendering throttle |
| "Requesting list of world names" repeating | Gazebo loading — wait 2-3 min, do not kill |
| `Robot is out of bounds of the costmap` | Transient during Nav2 startup — clears once AMCL localizes |

---

*Academic project — Georgia Southern University. Not licensed for commercial use.*
