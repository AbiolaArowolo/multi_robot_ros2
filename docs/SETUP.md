# Setup & Testing Guide

**Multi-Robot Cooperative Navigation — ROS 2 Humble**
**Student:** Abiola Arowolo | **Supervisor:** Prof. Doyun Lee | **Mentor:** Yong Ann Voeurn (PhD)

This document is for contributors or anyone wanting to reproduce and test this project from scratch.

---

## Prerequisites

### 1. Operating System
Ubuntu 22.04 LTS (bare metal or WSL2 on Windows 11).

For WSL2 users — enable GPU support:
```bash
nvidia-smi  # Should show your GPU if drivers are installed
```

### 2. Install ROS 2 Humble

```bash
sudo apt update && sudo apt install curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install ros-humble-desktop
```

### 3. Install Project Dependencies

```bash
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-clearpath-* \
  ros-humble-turtlebot3* \
  ros-humble-topic-tools \
  python3-colcon-common-extensions
```

### 4. Set TurtleBot3 model

```bash
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

---

## Workspace Setup

### Clone the repo

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/AbiolaArowolo/multi_robot_ros2.git .
```

### Build

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

### Source every terminal

```bash
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/ros2_ws/install/setup.bash
```

> Tip: Add these three lines to your `~/.bashrc` so you don't have to run them every time.

---

## Task 1 — Basic Pub/Sub Nodes

**Package:** `my_robot_pkg`

```bash
# Run publisher
ros2 run my_robot_pkg publisher

# Run subscriber (new terminal)
ros2 run my_robot_pkg subscriber
```

Expected: subscriber terminal prints messages published by publisher.

---

## Task 2A — Husky SLAM Mapping

**Package:** `multi_robot_bringup`
**Config:** `src/multi_robot_bringup/config/husky_slam_params.yaml`

```bash
# Terminal 1 — Launch Gazebo warehouse
ros2 launch clearpath_gz simulation.launch.py world:=warehouse
```

Wait for the Husky to fully spawn, then:

```bash
# Terminal 2 — Start SLAM
ros2 launch multi_robot_bringup husky_slam_warehouse.launch.py
```

```bash
# Terminal 3 — Visualize in RViz
ros2 launch clearpath_viz view_robot.launch.py namespace:=a200_0000
```

Drive the robot around the warehouse using the keyboard to build the map:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/a200_0000/cmd_vel
```

When map looks complete, save it:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/husky_map
```

**Expected output:**
- `~/ros2_ws/maps/husky_map.pgm`
- `~/ros2_ws/maps/husky_map.yaml`

---

## Task 2B — Husky Nav2 Autonomous Navigation

**Package:** `multi_robot_bringup`
**Config:** `src/multi_robot_bringup/config/husky_nav2_params.yaml`
**Requires:** Task 2A map saved at `~/ros2_ws/maps/husky_map.yaml`

### Step 1 — Launch Gazebo

```bash
source /opt/ros/humble/setup.bash && source /usr/share/gazebo/setup.sh && source ~/ros2_ws/install/setup.bash
ros2 launch clearpath_gz simulation.launch.py world:=warehouse
```

Wait for Husky to fully spawn before continuing.

### Step 2 — Launch Nav2 stack

```bash
# New terminal
source /opt/ros/humble/setup.bash && source /usr/share/gazebo/setup.sh && source ~/ros2_ws/install/setup.bash
ros2 launch multi_robot_bringup husky_nav2.launch.py
```

Wait until you see **both** of these messages:
```
[lifecycle_manager_localization]: Managed nodes are active
[lifecycle_manager_navigation]: Managed nodes are active
```

> This takes approximately 15-30 seconds. Do not proceed until both appear.

### Step 3 — Send a navigation goal

**Option A — Command line:**
```bash
source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 action send_goal /a200_0000/navigate_to_pose \
  nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
```

**Expected response:**
```
Goal accepted with ID: ...
```

**Option B — RViz (recommended for visual testing):**
```bash
ros2 launch clearpath_viz view_navigation.launch.py namespace:=a200_0000
```

In RViz: click **Nav2 Goal** button in toolbar → click anywhere on the map → robot plans and drives.

### Verify lifecycle states

```bash
ros2 lifecycle list /a200_0000/bt_navigator
ros2 lifecycle list /a200_0000/amcl
ros2 lifecycle list /a200_0000/controller_server
```

All must show `active`.

### Key configuration parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| `use_namespace` | `true` | Internal TF remapping — no relay needed |
| `odom_frame_id` | `odom` | Plain frame within namespace context |
| `scan_topic` | `sensors/lidar2d_0/scan` | Clearpath Husky A200 LiDAR topic |
| `set_initial_pose` | `true` | Auto-initializes AMCL at origin |
| `autostart` | `true` | Lifecycle managers start automatically |
| Controller | `RegulatedPurePursuitController` | Smooth velocity scaling on curves |

---

## Task 3 — Dual Robot Spawn (In Progress)

```bash
# Set TurtleBot3 model first
export TURTLEBOT3_MODEL=burger

# Launch both robots (coming soon)
```

---

## Useful Commands

```bash
# Kill all ROS processes
killros

# Check TF tree is connected
ros2 run tf2_ros tf2_echo map base_link

# List all active topics
ros2 topic list | grep a200_0000

# Validate YAML config
python3 -c "import yaml; yaml.safe_load(open('src/multi_robot_bringup/config/husky_nav2_params.yaml'))" && echo "VALID"

# Full rebuild
cd ~/ros2_ws && colcon build --symlink-install
```

---

## Known Warnings (Safe to Ignore)

| Warning | Reason |
|---------|--------|
| `transient local durability falling back to volatile` | QoS mismatch on TF — harmless |
| `QStandardPaths: runtime directory not owned by UID` | WSL2 display warning |
| `Unable to deserialize sdf::Model` | Clearpath Ignition model warning |
| `husky_hardware.xml has no Root Element` | Hardware plugin warning |

---

## Troubleshooting

**Goal rejected:**
1. Check both lifecycle managers printed `Managed nodes are active`
2. Verify bt_navigator is active: `ros2 lifecycle list /a200_0000/bt_navigator`
3. If inactive: `ros2 lifecycle set /a200_0000/bt_navigator cleanup` then `configure` then `activate`

**map frame does not exist:**
- AMCL has not received initial pose. Check `set_initial_pose: true` is in `husky_nav2_params.yaml`

**TF errors:**
- Do NOT use manual TF relay when `use_namespace: true` is set — they conflict

---

*Academic project — GSOU. Not licensed for commercial use.*
