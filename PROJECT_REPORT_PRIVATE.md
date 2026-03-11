# PRIVATE PROJECT REPORT — Multi-Robot ROS 2 Navigation
**Student:** Abiola Arowolo | GSOU
**Supervisor:** Prof. Doyun Lee
⚠️ PRIVATE — This file is in .gitignore and is NOT pushed to GitHub

---

## Report Log

---

### [2026-03-11] — Session 1: Workspace Setup & SLAM (Tasks 1–2A)

**Time:** Full day session
**Status:** ✅ Tasks 1 and 2A complete

**What was accomplished:**
- Set up ROS 2 Humble workspace `~/ros2_ws` with flat package structure
- Created `multi_robot_bringup` and `multi_robot_nodes` packages
- Implemented basic pub/sub nodes in `my_robot_pkg` (Task 1)
- Built and saved warehouse SLAM map using `slam_toolbox` online_async mode with Ceres solver
- Map saved: `~/ros2_ws/maps/husky_map.pgm` + `husky_map.yaml`
- Fixed `nav_config` reference bug in SLAM launch file

**Key decisions:**
- Used `slam_toolbox` over `gmapping` for loop closure capability
- Ceres solver chosen for better performance in warehouse geometry
- Flat workspace structure to avoid nested package issues with `colcon`

**Blockers encountered:**
- None significant at this stage

---

### [2026-03-11] — Session 2: Task 2B — Nav2 Debugging (~10 hours)

**Time:** ~10 hours continuous debugging
**Status:** ✅ Task 2B complete (goal accepted and navigation working)

**Root cause chain (in order of discovery):**

1. `libnav2_round_robin_bt_node.so` — wrong plugin name in params (actual name is `libnav2_round_robin_node_bt_node.so`). Caused `bt_navigator` crash on first launch.

2. `lifecycle_manager_navigation` aborted after crash, leaving `bt_navigator` in `inactive` state. Manual `cleanup → configure → activate` sequence partially worked but `activate` failed due to broken TF chain.

3. **Core TF problem:** `map` frame did not exist because AMCL was not publishing it. AMCL requires `odom → base_link` to be resolvable before it broadcasts `map → odom`.

4. **TF relay approach was wrong.** Using `topic_tools relay /a200_0000/tf /tf` conflicts with `use_namespace: true` in `nav2_bringup`. When `use_namespace` is set, Nav2 handles TF remapping internally. The manual relay was fighting the internal remapping.

5. **`odom_topic` was set to `odometry/filtered`** — this is the physical robot's EKF topic. In simulation it should be `/a200_0000/odom`.

6. **Missing `autostart: true`** in launch file — lifecycle managers were not automatically transitioning nodes to active.

7. **`set_initial_pose: true`** needed in AMCL params — without it, AMCL waits indefinitely for a pose from RViz.

8. **Missing BT plugin:** `nav2_remove_passed_goals_action_bt_node` — required by `navigate_through_poses_w_replanning_and_recovery.xml` behavior tree.

**Final working configuration:**
- No TF relay — `use_namespace: true` handles it
- `odom_frame_id: "odom"` (plain, not namespaced)
- `odom_topic: "/a200_0000/odom"`
- `autostart: true` in launch file
- `set_initial_pose: true` in AMCL
- All BT plugins including `nav2_remove_passed_goals_action_bt_node`

**What finally fixed it:**
```
Goal accepted with ID: 0a29793ccc2d40e1bfe85943eb90af4d
```

**Personal notes:**
- After PC restart, GPU (GTX 1650) is detected by WSL2 via `nvidia-smi` but Gazebo still uses `llvmpipe` software rendering. Not a blocker but worth fixing for performance.
- `killros` kills Gazebo too — always launch Gazebo first in a dedicated terminal before running `killros` on Nav2 only.

**Hours spent:** ~10 hours
**Frustration level:** High — same symptom (goal rejected) had 4 different root causes stacked on each other.

---

### [2026-03-12] — Session 3: Task 3 Start

**Time:** TBD
**Status:** 🔄 In Progress

**Goal:** Spawn TurtleBot3 and Husky simultaneously in Ignition Gazebo with basic pub/sub hello nodes confirming inter-robot ROS 2 communication.

**Plan:**
- Use `/turtlebot3/` namespace for TurtleBot3
- Verify both robots visible in `ros2 node list` and `ros2 topic list`
- Create hello publisher/subscriber pair across namespaces

**Notes to carry forward:**
- TurtleBot3 model must be set: `export TURTLEBOT3_MODEL=burger`
- Ignition Gazebo 6 only — not Classic

---

## Pending Items

| Item | Priority | Notes |
|------|----------|-------|
| GPU rendering in WSL2 Gazebo | Low | GTX 1650 detected but llvmpipe used |
| Task 3 dual spawn | High | Next session |
| Task 4 leader-follower | Medium | Needs Task 3 + 2B both working |
| Task 5 goal sharing | Medium | Builds on Task 4 |
| RViz Nav2 Goal screenshot for 2B | High | Required deliverable for Prof. Lee |

---

## Architecture Notes (For Future Reference)

**TF frame hierarchy (working):**
```
map (published by AMCL)
 └── odom (published by Gazebo/ros2_control)
      └── base_link (robot chassis)
           ├── front_left_wheel
           ├── front_right_wheel
           ├── rear_left_wheel
           ├── rear_right_wheel
           └── lidar2d_0_laser
```

**Why `use_namespace: true` replaces the TF relay:**
When `use_namespace: true` is passed to `nav2_bringup`, it uses `RewrittenYaml` internally to prepend the namespace to all frame IDs and topic remappings. The relay was re-publishing TF on `/tf` globally which conflicted with Nav2's internal remapping, causing frame ID mismatches.

**AMCL initialization chain:**
1. `map_server` loads `.yaml` + `.pgm` → publishes `/a200_0000/map`
2. `amcl` subscribes to map + `set_initial_pose: true` → initializes particle filter at (0,0,0)
3. AMCL subscribes to `/a200_0000/sensors/lidar2d_0/scan` for particle updates
4. AMCL broadcasts `map → odom` TF transform
5. `bt_navigator` can now activate (requires complete `map → odom → base_link` chain)

---

*This document is private and excluded from git via .gitignore*
*Last updated: 2026-03-12*
