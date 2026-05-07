FROM osrf/ros:melodic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=melodic

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    python-pip \
    python-catkin-tools \
    python-rosdep \
    python-rosinstall \
    python-rosinstall-generator \
    python-wstool \
    python-numpy \
    python-matplotlib \
    python-scipy \
    python-pandas \
    build-essential \
    ros-melodic-uuv-simulator \
    ros-melodic-uuv-descriptions \
    ros-melodic-uuv-gazebo \
    ros-melodic-uuv-gazebo-worlds \
    ros-melodic-uuv-thruster-manager \
    ros-melodic-uuv-control-cascaded-pid \
    ros-melodic-uuv-trajectory-control \
    ros-melodic-uuv-sensor-ros-plugins \
    ros-melodic-uuv-gazebo-ros-plugins \
    ros-melodic-uuv-teleop \
    ros-melodic-robot-localization \
    ros-melodic-teleop-twist-keyboard \
    ros-melodic-tf2-tools \
    ros-melodic-rosbash \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglu1-mesa \
    libglapi-mesa \
    libegl1-mesa \
    libgles2-mesa \
    mesa-utils \
    xvfb \
    x11-utils \
    x11-xserver-utils \
    x11vnc \
    novnc \
    websockify \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/ros_ws/src
WORKDIR /root/ros_ws

COPY ros_ws/src /root/ros_ws/src

RUN /bin/bash -c "source /opt/ros/melodic/setup.bash && \
    cd /root/ros_ws && \
    catkin_make"

RUN chmod +x /root/ros_ws/src/seaclear_pose/scripts/*.py

COPY run_all_experiments.sh /root/run_all_experiments.sh
RUN chmod +x /root/run_all_experiments.sh

RUN echo "source /opt/ros/melodic/setup.bash" >> /root/.bashrc && \
    echo "source /root/ros_ws/devel/setup.bash" >> /root/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\$GAZEBO_MODEL_PATH:/opt/ros/melodic/share/uuv_descriptions/models" >> /root/.bashrc

WORKDIR /root/ros_ws
CMD ["/bin/bash"]
