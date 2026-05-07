cmake_minimum_required(VERSION 3.0.2)
project(seaclear_pose)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  nav_msgs
  sensor_msgs
  tf
  tf2_ros
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs geometry_msgs nav_msgs sensor_msgs tf tf2_ros
)

include_directories(${catkin_INCLUDE_DIRS})

catkin_install_python(PROGRAMS
  scripts/trajectory_publisher.py
  scripts/usbl_fault_filter.py
  scripts/surface_feedback_publisher.py
  scripts/compute_mse.py
  scripts/plot_results.py
  scripts/record_experiment.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
