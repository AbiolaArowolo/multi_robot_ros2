# Multi-Robot Cooperative Navigation — ROS 2 Humble

**Student:** Abiola Arowolo | **Supervisor:** Prof. Doyun Lee | GSOU
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
| Task 3 | TurtleBot3 + Husky dual spawn, pub/sub hello nodes | 🔄 In Progress |
| Task 4 | Leader-follower controller (Husky leads, TurtleBot3 follows) | ⏳ Pending |
| Task 5 | Goal sharing node + role manager node | ⏳ Pending |

---

## Repository Structure

```
~/ros2_ws/
├── src/
│   ├── multi_robot_bringup/          # Main launch & config package
│   │   ├── launch/
│   │   │   ├── husky_slam_warehouse.launch.py   # SLAM mapping launch
│   │   │   └── husky_nav2.launch.py             # Nav2 navigation launch
│   │   ├── config/
│   │   │   ├── husky_slam_params.yaml           # slam_toolbox config
│   │   │   └── husky_nav2_params.yaml           # Full Nav2 params
│   │   └── setup.py
│   ├── multi_robot_nodes/            # Tasks 4 & 5 Python nodes
│   │   └── multi_robot_nodes/
│   │       ├── goal_sharing_node.py
│   │       └── role_manager_node.py
│   └── my_robot_pkg/                 # Task 1 — do not modify
└── maps/
    ├── husky_map.pgm
    ├── husky_map.yaml
    ├── turtlebot3_map.pgm
    └── turtlebot3_map.yaml
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

### Build workspace

```bash
cd ~/ros2_ws && colcon build --symlink-install
```

### Source every terminal

```bash
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/ros2_ws/install/setup.bash
```

---

## Task 2A — Husky SLAM Mapping

Builds a 2D occupancy grid map of the warehouse using `slam_toolbox` in `online_async` mode with the Ceres solver.

```bash
# Terminal 1 — Gazebo
ros2 launch clearpath_gz simulation.launch.py world:=warehouse

# Terminal 2 — SLAM
ros2 launch multi_robot_bringup husky_slam_warehouse.launch.py

# Save map when done
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/husky_map
```

---

## Task 2B — Husky Nav2 Autonomous Navigation

Deploys the full Nav2 stack with AMCL localization on the pre-built warehouse map.

```bash
# Terminal 1 — Gazebo (wait for Husky to spawn)
ros2 launch clearpath_gz simulation.launch.py world:=warehouse

# Terminal 2 — Nav2
ros2 launch multi_robot_bringup husky_nav2.launch.py
```

Wait for both:
```
[lifecycle_manager_localization]: Managed nodes are active
[lifecycle_manager_navigation]: Managed nodes are active
```

```bash
# Terminal 3 — Send goal
ros2 action send_goal /a200_0000/navigate_to_pose \
  nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'

# Or use RViz Nav2 Goal tool
ros2 launch clearpath_viz view_navigation.launch.py namespace:=a200_0000
```

### Nav2 Key Configuration

| Parameter | Value | Reason |
|-----------|-------|--------|
| `use_namespace` | `true` | Internal TF remapping — no relay needed |
| `odom_frame_id` | `odom` | Plain frame within namespace context |
| `scan_topic` | `sensors/lidar2d_0/scan` | Clearpath Husky A200 LiDAR topic |
| `set_initial_pose` | `true` | Auto-initializes AMCL without RViz |
| Controller | `RegulatedPurePursuitController` | Smooth velocity scaling |

---

## Useful Commands

```bash
# Kill all ROS processes
killros

# Check lifecycle states
ros2 lifecycle list /a200_0000/bt_navigator

# Verify TF tree
ros2 run tf2_ros tf2_echo map base_link

# Validate YAML config
python3 -c "import yaml; yaml.safe_load(open('src/multi_robot_bringup/config/husky_nav2_params.yaml'))" && echo "VALID"

# Full build
cd ~/ros2_ws && colcon build --symlink-install
```

---

## Guardrails

- **ROS 2 Humble only** — do not upgrade
- **Ignition Gazebo 6** — not Gazebo Classic 11
- **Workspace:** `~/ros2_ws` — do not move or rename
- **Husky namespace:** `/a200_0000/` | **TurtleBot3 namespace:** `/turtlebot3/`
- **`my_robot_pkg`** — do not touch (Task 1 deliverables)
- **VPN must be OFF** for all apt installs and git push
- All config files go inside packages under `config/` — never in workspace root

---

## Known Warnings (Safe to Ignore)

| Warning | Reason |
|---------|--------|
| `transient local durability falling back to volatile` | QoS mismatch on TF — harmless |
| `QStandardPaths: runtime directory not owned by UID` | WSL2 display warning |
| `Unable to deserialize sdf::Model` | Clearpath Ignition model warning |
| `husky_hardware.xml has no Root Element` | Hardware plugin warning |

---

*Academic project — GSOU. Not licensed for commercial use.*
