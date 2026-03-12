# Multi-Robot Cooperative Navigation — ROS 2 Humble

**Student:** Abiola Arowolo 

**ROS Distribution:** ROS 2 Humble | **Simulator:** Ignition Gazebo 6 (Fortress)

---

## Project Overview

This project implements a cooperative multi-robot navigation system using a **Clearpath Husky A200** and a **TurtleBot3** in a simulated warehouse environment. The system integrates SLAM-based mapping, AMCL localization, Nav2 autonomous navigation, inter-robot goal sharing, and dynamic leader-follower role switching.

---

## Task Progress

| Task | Description | Status |
|------|-------------|--------|
| Task 1 | Basic ROS 2 pub/sub nodes (`my_robot_pkg`) | Complete |
| Task 2A | Husky SLAM — warehouse map built and saved |  Complete |
| Task 2B | Husky Nav2 — AMCL localization + autonomous navigation | Complete |
| Task 3 | TurtleBot3 + Husky dual spawn, pub/sub hello nodes |  In Progress |
| Task 4 | Leader-follower controller (Husky leads, TurtleBot3 follows) | ⏳ Pending |
| Task 5 | Goal sharing node + role manager node | ⏳ Pending |

---

## Repository Structure
```
~/ros2_ws/
├── src/
│   ├── multi_robot_bringup/          # Main launch & config package
│   │   ├── launch/
│   │   │   ├── husky_slam_warehouse.launch.py
│   │   │   └── husky_nav2.launch.py
│   │   ├── config/
│   │   │   ├── husky_slam_params.yaml
│   │   │   └── husky_nav2_params.yaml
│   ├── multi_robot_nodes/            # Tasks 4 & 5 Python nodes
│   └── my_robot_pkg/                 # Task 1 — do not modify
└── maps/
    ├── husky_map.pgm + husky_map.yaml
    └── turtlebot3_map.pgm + turtlebot3_map.yaml
```

---

## Task 2A — Husky SLAM Mapping
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
```bash
# Terminal 1 — Gazebo
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

# RViz visualization
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

## Environment Setup
```bash
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/ros2_ws/install/setup.bash
cd ~/ros2_ws && colcon build --symlink-install
```

---


---

## Known Warnings (Safe to Ignore)

| Warning | Reason |
|---------|--------|
| `transient local durability falling back to volatile` | QoS mismatch — harmless |
| `QStandardPaths: runtime directory not owned by UID` | WSL2 display warning |
| `Unable to deserialize sdf::Model` | Clearpath Ignition model warning |

---

*Academic project — GSOU. Not licensed for commercial use.*
