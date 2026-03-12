# Multi-Robot Cooperative Navigation — ROS 2 Humble

**Student:** Abiola Arowolo
**Supervisor:** Prof. Doyun Lee | **Mentor:** Yong Ann Voeurn (PhD)
**Institution:** GSOU
**ROS Distribution:** ROS 2 Humble | **Simulator:** Ignition Gazebo 6 (Fortress)

---

## Project Overview

This project implements a cooperative multi-robot navigation system using a **Clearpath Husky A200** and a **TurtleBot3** in a simulated warehouse environment.

The system progressively builds toward a fully autonomous multi-robot architecture featuring:
- 2D SLAM-based warehouse mapping
- AMCL probabilistic localization
- Nav2 autonomous goal navigation
- Inter-robot goal sharing
- Dynamic leader-follower role switching

---

## System Requirements

| Component | Version |
|-----------|---------|
| ROS 2 | Humble Hawksbill |
| Simulator | Ignition Gazebo 6 (Fortress) |
| OS | Ubuntu 22.04 (or WSL2) |
| Python | 3.10+ |

---

## Task Progress

| Task | Description | Status |
|------|-------------|--------|
| Task 1 | Basic ROS 2 pub/sub nodes |  Complete |
| Task 2A | Husky SLAM — warehouse map built and saved |  Complete |
| Task 2B | Husky Nav2 — AMCL localization + autonomous navigation |  Complete |
| Task 3 | TurtleBot3 + Husky dual spawn, pub/sub communication |  In Progress |
| Task 4 | Leader-follower controller (Husky leads, TurtleBot3 follows) | ⏳ Pending |
| Task 5 | Goal sharing node + role manager node | ⏳ Pending |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    ROS 2 Humble Stack                     │
├─────────────────────┬────────────────────────────────────┤
│   Husky A200        │   TurtleBot3                        │
│   /a200_0000/       │   /turtlebot3/                      │
├─────────────────────┴────────────────────────────────────┤
│   Shared map frame (SLAM → AMCL → Nav2)                  │
│   Inter-robot goal sharing via /shared_goal              │
│   Dynamic leader-follower role switching                 │
└──────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
~/ros2_ws/
├── README.md                         ← You are here
├── docs/
│   ├── SETUP.md                      ← Full setup & testing guide
│   └── media/                        ← Screenshots, diagrams, demo GIFs
├── maps/
│   ├── husky_map.pgm
│   ├── husky_map.yaml
│   ├── turtlebot3_map.pgm
│   └── turtlebot3_map.yaml
└── src/
    ├── multi_robot_bringup/
    │   ├── launch/
    │   │   ├── husky_slam_warehouse.launch.py
    │   │   └── husky_nav2.launch.py
    │   ├── config/
    │   │   ├── husky_slam_params.yaml
    │   │   └── husky_nav2_params.yaml
    │   └── setup.py
    ├── multi_robot_nodes/
    │   └── multi_robot_nodes/
    │       ├── goal_sharing_node.py
    │       └── role_manager_node.py
    └── my_robot_pkg/                 ← Task 1 (do not modify)
```

---

## Quick Start

Full setup and testing instructions → **[docs/SETUP.md](docs/SETUP.md)**

```bash
# Clone and build
git clone https://github.com/AbiolaArowolo/multi_robot_ros2.git
cd multi_robot_ros2 && colcon build --symlink-install

# Source
source /opt/ros/humble/setup.bash && source install/setup.bash

# Launch Nav2 demo
ros2 launch multi_robot_bringup husky_nav2.launch.py
```

---


---

*Academic project — GSOU. Not licensed for commercial use.*
