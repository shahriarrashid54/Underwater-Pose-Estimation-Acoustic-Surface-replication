# SeaClear Pose Estimation - Replication

Replicates **"Underwater Robot Pose Estimation Using Acoustic Methods and
Intermittent Position Measurements at the Surface"**, Maer, Tamas, Busoniu
(arXiv:2312.11401, 2023).

The paper uses ROS Noetic-era tooling, `uuv_simulator`, and
`robot_localization` on Linux. This replication runs the same stack inside
Docker (ROS Melodic + Ubuntu 18.04, on which `uuv_simulator` is rock-solid)
and reproduces:

* Section IV - underwater-only EKF performance with four sensor combinations
  (IMU, IMU+DVL, IMU+USBL, IMU+DVL+USBL) -> **Table II**, **Figs 3-6**.
* Section V - intermittent surface position fixes
  ("resurfacing" via GPS / UAV camera) -> **Tables III, IV**, **Figs 7-8**.

The Process noise covariance matrix `Q` (eq. 7), the sensor noise
parameters (Table I), the USBL stuck-fault model (5% probability, 10 s
hold), and the surface-fix sigma (sigma = 0.05 m) all match the paper.

## Substitutions vs paper

| Paper                                    | Replication                              |
|------------------------------------------|------------------------------------------|
| ROS Noetic                               | ROS Melodic (best `uuv_simulator` support) |
| SubseaTech Tortuga URDF (not public)     | `rexrov` (default UUV in `uuv_descriptions`) |
| Manual teleop on rectangle               | Automated `cmd_vel` rectangle driver     |
| `uuv_simulator` USBL plugin              | Synthetic publisher matching paper noise & stuck behavior |

The EKF behavior (`robot_localization` Newtonian 3D rigid-body model) is
identical: same `Q`, same per-sensor `R`, same 15-state vector.

## Layout

```
seaclear_replication/
  Dockerfile                 # ros:melodic-desktop-full + uuv_simulator + robot_localization
  docker-compose.yml         # mounts ./results, sets X server env
  run_all_experiments.sh     # in-container orchestrator
  ros_ws/src/seaclear_pose/
    config/                  # 6 EKF YAMLs (common Q + per-config sensors)
    launch/                  # bringup + 6 experiment launches
    scripts/
      trajectory_publisher.py        # rectangle cmd_vel
      usbl_fault_filter.py           # USBL: sigma=0.5, 5%/10s stuck
      surface_feedback_publisher.py  # sigma=0.05, periodic
      pressure_to_depth.py           # FluidPressure -> z PoseWithCovariance
      record_experiment.py           # CSV logger (gt + estimate)
      compute_mse.py                 # Tables II/III/IV
      plot_results.py                # Figs 3-8
  results/                   # populated by the run script (mounted to host)
```

## Build

Windows (Docker Desktop, WSL2 backend) - **GUI optional**, headless run is
the default:

```powershell
cd "D:\MUN\Workspace\Underwater Pose Estimation\seaclear_replication"
docker compose build
```

Linux:

```bash
docker compose build
```

## Run all experiments (headless)

```powershell
docker compose run --rm seaclear bash /root/ros_ws/src/seaclear_pose/../../run_all_experiments.sh
```

Or, more cleanly, copy the script into the image / bind mount and run:

```powershell
docker compose run --rm -v "${PWD}/run_all_experiments.sh:/root/run.sh" seaclear bash /root/run.sh
```

Total wall time: roughly 25-30 minutes on a modern laptop (each experiment
is 150 s sim time, run sequentially in lock-step with Gazebo).

Results land in `./results/`:

```
results/
  imu_only.csv          fig3_imu_only.png
  imu_dvl.csv           fig4_imu_dvl.png
  imu_usbl.csv          fig5_imu_usbl.png
  imu_dvl_usbl.csv      fig6_imu_dvl_usbl.png
  usbl_surface_*.csv    fig7_x_axis.png
  imu_surface_30s.csv   fig8_x_axis.png
  table_II.txt  table_III.txt  table_IV.txt
```

## Run a single experiment (with Gazebo GUI)

You need an X server on the host:

* **Windows**: install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) or
  [X410](https://x410.dev/), launch it with "Disable access control" / multi-window mode.
* Set `DISPLAY` to your host IP:0.0 before `docker compose run`. Example
  PowerShell:

  ```powershell
  $env:DISPLAY = "host.docker.internal:0.0"
  docker compose run --rm seaclear
  ```

Inside the container:

```bash
roslaunch seaclear_pose experiment_imu_dvl_usbl.launch \
    duration:=150 out_path:=/root/results/imu_dvl_usbl.csv
```

## Reproducing the tables

After `run_all_experiments.sh` finishes:

```bash
cat /root/results/table_II.txt
cat /root/results/table_III.txt
cat /root/results/table_IV.txt
```

`compute_mse.py` can also be invoked manually on any subset of CSVs with
`--labels` to pick the column titles.

## Process / measurement noise

The EKF process noise reproduces equation (7) of the paper exactly:

```
Q = diag( 1e-3 1e-3 1e-3   0.3 0.3 0.3   0.5 0.5 0.1   0.3 0.3 0.3   0.3 0.3 0.3 )
```

Per-sensor `R` is set from each measurement's covariance (Table I values
are baked into `usbl_fault_filter.py`, `pressure_to_depth.py`, and the
uuv_simulator IMU/DVL plugin parameters).

## Notes / known gotchas

* Gazebo physics is non-deterministic; run-to-run MSE numbers vary by a
  few percent. The qualitative ordering matches the paper:
  `IMU < IMU+DVL < IMU+USBL < IMU+DVL+USBL` (lower = better) on the
  position channels under the noisy USBL fault model.
* Each experiment exits cleanly when the recorder finishes (it calls
  `rospy.signal_shutdown` after the duration); the 4 second sleep between
  experiments lets gzserver release the model database.
* Set `usbl_seed`, `surface_seed`, and Gazebo's `--seed` (via the world
  launch arg) for fully deterministic reruns.
