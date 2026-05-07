#!/usr/bin/env bash
# Inside-container orchestrator: run every experiment headless and assemble
# Tables II, III, IV plus Figs 3-8 into /root/results/.
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /root/ros_ws/devel/setup.bash

mkdir -p /root/results
RES=/root/results

run_exp () {
    local launch=$1
    local out=$2
    shift 2
    echo "==== running $launch -> $out ===="
    xvfb-run -a -s "-screen 0 1280x800x24 +extension GLX +render" \
        roslaunch seaclear_pose "$launch" gui:=false out_path:="$out" "$@" \
        2>&1 | tee "$RES/$(basename "$out" .csv).log"
    echo "==== done $launch ===="
    sleep 4
}

# Section IV
run_exp experiment_imu_only.launch     "$RES/imu_only.csv"     duration:=150
run_exp experiment_imu_dvl.launch      "$RES/imu_dvl.csv"      duration:=150
run_exp experiment_imu_usbl.launch     "$RES/imu_usbl.csv"     duration:=150 usbl_seed:=42
run_exp experiment_imu_dvl_usbl.launch "$RES/imu_dvl_usbl.csv" duration:=150 usbl_seed:=42

# Section V (Table III): IMU+USBL with surface feedback at varying periods
run_exp experiment_usbl_surface.launch "$RES/usbl_surface_nofb.csv" \
    duration:=150 surface_period:=1000000 usbl_seed:=42
run_exp experiment_usbl_surface.launch "$RES/usbl_surface_1s.csv" \
    duration:=150 surface_period:=1.0   usbl_seed:=42 surface_seed:=11
run_exp experiment_usbl_surface.launch "$RES/usbl_surface_5s.csv" \
    duration:=150 surface_period:=5.0   usbl_seed:=42 surface_seed:=12
run_exp experiment_usbl_surface.launch "$RES/usbl_surface_10s.csv" \
    duration:=150 surface_period:=10.0  usbl_seed:=42 surface_seed:=13

# Section V (Table IV): IMU only with 30 s surface fixes
run_exp experiment_imu_surface.launch  "$RES/imu_surface_30s.csv" \
    duration:=150 surface_period:=30.0 surface_seed:=21

# Tables
rosrun seaclear_pose compute_mse.py \
    "$RES/imu_only.csv" "$RES/imu_dvl.csv" \
    "$RES/imu_usbl.csv" "$RES/imu_dvl_usbl.csv" \
    --labels "IMU,IMU+DVL,IMU+USBL,IMU+DVL+USBL" \
    --out "$RES/table_II.txt"

rosrun seaclear_pose compute_mse.py \
    "$RES/usbl_surface_nofb.csv" \
    "$RES/usbl_surface_1s.csv" \
    "$RES/usbl_surface_5s.csv" \
    "$RES/usbl_surface_10s.csv" \
    --labels "no feedback,1 sec,5 sec,10 sec" \
    --out "$RES/table_III.txt"

rosrun seaclear_pose compute_mse.py \
    "$RES/imu_only.csv" "$RES/imu_surface_30s.csv" \
    --labels "IMU only,30 sec" \
    --out "$RES/table_IV.txt"

# Figs
rosrun seaclear_pose plot_results.py --mode six \
    --csv "$RES/imu_only.csv" --title "Fig. 3: IMU only" \
    --out "$RES/fig3_imu_only.png"
rosrun seaclear_pose plot_results.py --mode six \
    --csv "$RES/imu_dvl.csv" --title "Fig. 4: IMU + DVL" \
    --out "$RES/fig4_imu_dvl.png"
rosrun seaclear_pose plot_results.py --mode six \
    --csv "$RES/imu_usbl.csv" --title "Fig. 5: IMU + USBL" \
    --out "$RES/fig5_imu_usbl.png"
rosrun seaclear_pose plot_results.py --mode six \
    --csv "$RES/imu_dvl_usbl.csv" --title "Fig. 6: IMU + DVL + USBL" \
    --out "$RES/fig6_imu_dvl_usbl.png"

rosrun seaclear_pose plot_results.py --mode compare \
    --csv "$RES/usbl_surface_1s.csv" \
    --baseline "$RES/usbl_surface_nofb.csv" \
    --axis x --title "Fig. 7: USBL+IMU, 1 s surface feedback vs none" \
    --out "$RES/fig7_x_axis.png"

rosrun seaclear_pose plot_results.py --mode compare \
    --csv "$RES/imu_surface_30s.csv" \
    --baseline "$RES/imu_only.csv" \
    --axis x --title "Fig. 8: IMU only with 30 s surface fixes" \
    --out "$RES/fig8_x_axis.png"

echo "All artefacts in $RES"
ls -la "$RES"
