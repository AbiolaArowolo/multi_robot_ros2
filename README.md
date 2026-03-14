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
| Task 1 | Basic ROS 2 pub/sub nodes (`my_robot_pkg`) | ✅ Complete | main |
| Task 2A | Husky SLAM — warehouse map built and saved | ✅ Complete | task/2b-husky-slam-nav2 |
| Task 2B | Husky Nav2 — AMCL localization + autonomous goal navigation | ✅ Complete | task/2b-husky-slam-nav2 |
| Task 3 | TurtleBot3 + Husky dual spawn, bridged topics, hello nodes | ✅ Complete | task/3-dual-spawn |
| Task 4 | Leader-follower controller — proportional + breadcrumb trail | ✅ Complete | task/4-leader-follower |
| Task 5 | Goal sharing node + role manager node | 🔄 In Progress | task/5-cooperative-nav |

---

## Repository Structure

```
~/ros2_ws/
├── src/
│   ├── multi_robot_bringup/          # Main launch & config package
│   │   ├── launch/
│   │   │   ├── husky_slam_warehouse.launch.py    # Task 2A — SLAM mapping
│   │   │   ├── husky_nav2.launch.py              # Task 2B — Nav2 navigation
│   │   │   ├── task3_dual_spawn.launch.py         # Task 3 — both robots
│   │   │   └── task4_leader_follower.launch.py    # Task 4 — leader-follower
│   │   ├── config/
│   │   │   ├── husky_slam_params.yaml
│   │   │   └── husky_nav2_params.yaml
│   │   ├── models/
│   │   │   └── turtlebot3_burger/
│   │   │       ├── model.sdf                     # Native Ignition SDF
│   │   │       └── model.config
│   │   └── setup.py
│   ├── multi_robot_nodes/            # All Python nodes
│   │   └── multi_robot_nodes/
│   │       ├── husky_hello_node.py               # Task 3 cross-namespace pub/sub
│   │       ├── tb3_hello_node.py                 # Task 3 cross-namespace pub/sub
│   │       ├── odom_to_tf_broadcaster.py         # Task 3 odom → TF
│   │       ├── leader_pose_publisher.py          # Task 4 — Husky odom → /leader/pose
│   │       ├── follower_controller.py            # Task 4 — proportional follower
│   │       └── breadcrumb_follower.py            # Task 4 — exact footprint tracker
│   └── my_robot_pkg/                 # Task 1 — do not modify
└── maps/
    ├── husky_map.pgm / .yaml         # Husky warehouse map
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
# Single command — launches everything
ros2 launch multi_robot_bringup task3_dual_spawn.launch.py
```

Wait 2–3 minutes on WSL2. Then verify:

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
| DiffDrive subscribes on `/turtlebot3/cmd_vel` | Absolute topic set in model.sdf |
| TB3 odom bridges from Ignition `/odom` | Not `/model/turtlebot3/odometry` |
| TB3 link names prefixed `tb3_` | Prevents cross-model joint binding with Husky |
| Bridge remappings require absolute paths | Leading `/` prevents namespace auto-prefix |

---

## Task 4 — Leader-Follower Control

Husky A200 acts as leader. TurtleBot3 follows using two controller modes.

```bash
# Launch both robots + leader publisher
ros2 launch multi_robot_bringup task4_leader_follower.launch.py
```

### Mode 1 — Proportional Follower
Drives TB3 toward Husky's current position, maintaining 1.2 m gap.

```bash
ros2 run multi_robot_nodes follower_controller
```

### Mode 2 — Breadcrumb Trail Follower (Exact Footprint Tracking)
Husky records waypoints every 0.08 m. TB3 works through the queue in order, tracing Husky's exact path with a ~0.32 m delay gap.

```bash
ros2 run multi_robot_nodes breadcrumb_follower
```

### Drive Husky (separate terminal)

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
          │
          ▼
  leader_pose_publisher ──► /leader/pose
                                  │
              ┌───────────────────┤
              ▼                   ▼
   follower_controller    breadcrumb_follower
              │                   │
              └─────────┬─────────┘
                        ▼
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

## Confirmed Topic Map

| Topic | Source | Notes |
|-------|--------|-------|
| `/a200_0000/platform/odom/filtered` | Husky EKF | Real odom — `/a200_0000/odom` is empty |
| `/a200_0000/cmd_vel` | Drive Husky | |
| `/turtlebot3/cmd_vel` | Drive TB3 | Absolute topic in model.sdf |
| `/turtlebot3/odom` | Bridged from `/odom` | Global Ignition topic |
| `/turtlebot3/scan` | Bridged from `/scan` | Global Ignition topic |
| `/leader/pose` | leader_pose_publisher | System-level coordination channel |

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
| "Requesting list of world names" repeating | Gazebo loading — wait 2–3 min, do not kill |

---

## Guardrails

- **ROS 2 Humble only** — do not upgrade
- **Ignition Gazebo 6 (Fortress)** — not Gazebo Classic
- **Workspace:** `~/ros2_ws` — do not move or rename
- **Husky namespace:** `/a200_0000/` | **TB3 namespace:** `/turtlebot3/`
- **`my_robot_pkg`** — do not touch (Task 1 deliverables)
- **VPN must be OFF** for all apt installs and git push
- **TB3 link names must stay prefixed `tb3_`** — prevents cross-model joint binding
- **Do NOT add `sensors-system` plugin to robot models** — warehouse world loads it
- **No hardcoded paths** — use `get_package_share_directory()` and `model://` URIs

---

*Academic project — Georgia Southern University. Not licensed for commercial use.*
