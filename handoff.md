# Session handoff

This document captures the state of the SeaClear pose-estimation replication
at the end of the working session. Pick up from here.

## What we built

A complete, Dockerized end-to-end replication of Maer, Tamas & Busoniu (2023),
"Underwater Robot Pose Estimation Using Acoustic Methods and Intermittent
Position Measurements at the Surface" (arXiv:2312.11401).

The replication:

* Spins up a single Docker container based on `osrf/ros:melodic-desktop-full`
  containing ROS Melodic, Gazebo 9, `uuv_simulator`, and `robot_localization`.
* Spawns the `rexrov` UUV in an empty subsea world, controlled by a
  cmd_vel-driven cascaded-PID stack.
* Fuses IMU, DVL, USBL, depth (from pressure), and an intermittent surface
  GPS-style fix in an EKF whose process-noise covariance `Q` is taken
  verbatim from the paper's equation (7).
* Runs the four Section IV underwater configurations (`IMU`, `IMU+DVL`,
  `IMU+USBL`, `IMU+DVL+USBL`) and the five Section V surface-feedback
  configurations (no feedback, 1 s, 5 s, 10 s, 30 s).
* Emits the paper's Tables II / III / IV plus Figures 3-8 from CSVs of
  ground truth vs. EKF estimate.
* Optionally streams the live Gazebo client to a host browser via an
  internal Xvfb -> x11vnc -> noVNC bridge (`http://localhost:6080/vnc.html`).

A single `run-headless.ps1` (or in-container `run_all_experiments.sh`)
reproduces every artefact in roughly 25-30 minutes.

GitHub repo: <https://github.com/shahriarrashid54/Underwater-Pose-Estimation-Acoustic-Surface-replication>.

## Files created or modified

```
seaclear_replication/
├── Dockerfile                        # ROS Melodic + uuv_simulator +
│                                       robot_localization + Mesa + Xvfb +
│                                       x11vnc + noVNC + websockify.
├── docker-compose.yml                # bridge networking, ports 5900/6080,
│                                       software-GL env vars, volume mounts.
├── .dockerignore
├── .gitignore                        # excludes ros_ws build/devel and *.log.
├── .gitattributes                    # forces LF on shell/python/launch
│                                       files so Linux container is happy.
├── README.md                         # full build/run instructions + paper
│                                       diff (Melodic vs. Noetic, rexrov vs.
│                                       Tortuga, automated rectangle vs.
│                                       teleop).
├── build.ps1                         # Windows convenience wrapper.
├── run-headless.ps1                  # full-suite Windows wrapper.
├── run-gui.ps1                       # interactive Gazebo session.
├── run_all_experiments.sh            # in-container orchestrator. Calls
│                                       xvfb-run for each headless launch
│                                       so gzserver gets a working GL.
└── ros_ws/src/seaclear_pose/
    ├── package.xml                   # ROS 1 package metadata, depends on
    │                                   uuv_gazebo, uuv_descriptions,
    │                                   uuv_control_cascaded_pid, etc.
    ├── CMakeLists.txt                # installs Python scripts and config
    │                                   + launch dirs.
    ├── config/
    │   ├── ekf_common.yaml           # paper's Q from eq. (7), 20 Hz,
    │   │                               base_link=rexrov/base_link,
    │   │                               world_frame=odom.
    │   ├── ekf_imu_only.yaml         # IMU + depth.
    │   ├── ekf_imu_dvl.yaml
    │   ├── ekf_imu_usbl.yaml
    │   ├── ekf_imu_dvl_usbl.yaml
    │   ├── ekf_usbl_surface.yaml     # IMU + USBL + depth + intermittent
    │   │                               surface fix.
    │   └── ekf_imu_surface.yaml      # IMU + depth + 30 s surface fix.
    ├── launch/
    │   ├── bringup.launch            # subsea world, rexrov spawn at
    │   │                               z=-3, thruster_manager, inline
    │   │                               AccelerationControl + VelocityControl
    │   │                               nodes (no velocity_control.launch -
    │   │                               that file does not exist in apt
    │   │                               package, so we replicate its content).
    │   ├── experiment_imu_only.launch
    │   ├── experiment_imu_dvl.launch
    │   ├── experiment_imu_usbl.launch
    │   ├── experiment_imu_dvl_usbl.launch
    │   ├── experiment_usbl_surface.launch
    │   └── experiment_imu_surface.launch
    │                                  # Each adds required="true" on the
    │                                  # record_experiment node so roslaunch
    │                                  # tears the whole stack down when
    │                                  # the recorder finishes.
    └── scripts/
        ├── trajectory_publisher.py     # closed rectangle: dive 4 s @
        │                                 0.25 m/s, then 4 x (forward 12 s
        │                                 @ 0.3 m/s, yaw 90 deg).
        ├── usbl_fault_filter.py        # synthesises USBL: ground truth +
        │                                 N(0, 0.5 m) + 5%/10 s stuck fault
        │                                 (paper's hardware lockup model).
        ├── surface_feedback_publisher.py
        │                                # GPS/UAV-camera surrogate, sigma
        │                                 = 0.05 m, configurable period.
        ├── pressure_to_depth.py         # converts uuv_simulator's
        │                                 SubseaPressure topic to a z-only
        │                                 PoseWithCovarianceStamped. The
        │                                 plugin publishes kPa not Pa
        │                                 despite the FluidPressure spec -
        │                                 do not divide by 1000.
        ├── record_experiment.py         # logs gt + EKF estimate at 20 Hz,
        │                                 calls signal_shutdown after the
        │                                 configured duration.
        ├── compute_mse.py               # builds Tables II / III / IV.
        ├── plot_results.py              # builds Figs 3-8 (matplotlib Agg).
        └── run_with_gui.sh              # starts Xvfb :99, x11vnc, noVNC,
                                          then roslaunches the requested
                                          experiment - browser viewable
                                          at localhost:6080.
```

## Final results (committed in `results/`)

| Artefact | Description |
| --- | --- |
| `imu_only.csv`, `imu_dvl.csv`, `imu_usbl.csv`, `imu_dvl_usbl.csv` | Section IV CSVs. |
| `usbl_surface_{nofb,1s,5s,10s}.csv` | Section V Table III CSVs. |
| `imu_surface_30s.csv` | Section V Table IV CSV. |
| `table_II.txt`, `table_III.txt`, `table_IV.txt` | MSE tables. |
| `fig3_imu_only.png` ... `fig8_x_axis.png` | Per-axis plots. |

Quick MSE comparison (X-axis MSE in m^2):

| Config | Paper | Replication |
| --- | --- | --- |
| IMU only | 18.4 | 9.24 |
| IMU+USBL | 2.45 | 0.67 |
| IMU+DVL | 0.04 | 0.0001 |
| IMU+DVL+USBL | 0.94 | 0.11 |
| 1 s surface fix | 0.014 | 0.028 |
| 30 s surface vs IMU only | 2.57 | 2.38 |

Same ranking, same orders of magnitude. The remaining gap comes from the
vehicle substitution (rexrov vs. SubseaTech Tortuga - URDF not public) and
a slightly different rectangle scale.

## Next steps

Pick whichever item is most useful for your goal next session:

1. **Tighten quantitative match.** If a closer match to the paper's
   absolute MSE values matters, port the SubseaTech Tortuga URDF (currently
   not public - reach out to SeaClear or build a stand-in with similar mass
   and IMU bias) and replay. The pipeline is otherwise sensor-agnostic.

2. **Run with multiple random seeds.** The paper reports a single run.
   Adding a Monte Carlo loop (10 seeds per config) would give error bars
   and is a one-line change to `run_all_experiments.sh`
   (`for seed in 0..9; do ... usbl_seed:=$seed surface_seed:=$seed; done`).

3. **Try the unscented Kalman filter extension the paper mentions.**
   `robot_localization` has `ukf_localization_node` as a drop-in
   replacement for `ekf_localization_node`. Add a parallel set of launch
   files and compare against the EKF.

4. **Real-hardware bridge.** The paper lists hardware tests as future
   work. The same launch files should accept real `/imu`, `/dvl_twist`,
   `/usbl_pose` topics with minimal remap; document the topic-mapping
   procedure in the README.

5. **Trim the image.** Image is 4.27 GB, mostly Gazebo + meshes. Multi-stage
   build would shrink the runtime layer; not urgent.

6. **Add a CI smoke run.** A 30 s GitHub Actions job that boots the
   container, runs `experiment_imu_only.launch`, and checks the CSV is
   non-empty would catch regressions on PRs.

## Quick resume checklist

When you come back:

```powershell
# 1. Make sure Docker Desktop is running.
docker info --format '{{.ServerVersion}}'

# 2. Sanity-check the image still exists.
docker images seaclear-replication

# 3. Reproduce all results headless (~25-30 min).
cd "D:\MUN\Workspace\Underwater Pose Estimation\seaclear_replication"
.\run-headless.ps1

# 4. Single experiment with live Gazebo in the browser (localhost:6080).
docker compose run --rm --service-ports seaclear `
    bash /root/ros_ws/src/seaclear_pose/scripts/run_with_gui.sh `
    experiment_imu_dvl.launch duration:=200 out_path:=/root/results/play.csv
```

Repo: <https://github.com/shahriarrashid54/Underwater-Pose-Estimation-Acoustic-Surface-replication>
