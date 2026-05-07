#!/usr/bin/env bash
# Launch a roslaunch experiment inside the container with a self-contained
# Xvfb -> x11vnc -> noVNC stack, so the Gazebo client renders to an
# off-screen X server and the user can watch it from their host browser
# at http://localhost:6080/vnc.html
set -euo pipefail

LAUNCH="${1:-experiment_imu_dvl.launch}"
shift || true

export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export GALLIUM_DRIVER=llvmpipe

mkdir -p /tmp/runtime
chmod 700 /tmp/runtime
export XDG_RUNTIME_DIR=/tmp/runtime

echo "[gui] starting Xvfb on $DISPLAY (1280x800x24)"
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!

# Wait for Xvfb to come up.
for i in $(seq 1 30); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then break; fi
    sleep 0.3
done
xdpyinfo -display :99 >/dev/null 2>&1 || { echo "[gui] Xvfb failed"; exit 1; }
echo "[gui] Xvfb up"

echo "[gui] starting x11vnc on port 5900"
x11vnc -display :99 -forever -shared -nopw -quiet -rfbport 5900 -bg -o /tmp/x11vnc.log
sleep 1

echo "[gui] starting noVNC on port 6080 (open http://localhost:6080/vnc.html)"
websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
WS_PID=$!

cleanup () {
    echo "[gui] shutting down GUI bridge"
    kill $WS_PID  2>/dev/null || true
    pkill -f x11vnc 2>/dev/null || true
    kill $XVFB_PID 2>/dev/null || true
}
trap cleanup EXIT

source /opt/ros/melodic/setup.bash
source /root/ros_ws/devel/setup.bash
export GAZEBO_MODEL_PATH="${GAZEBO_MODEL_PATH:-}:/opt/ros/melodic/share/uuv_descriptions/models"

echo "[gui] roslaunch seaclear_pose $LAUNCH $*"
roslaunch seaclear_pose "$LAUNCH" gui:=true "$@"
