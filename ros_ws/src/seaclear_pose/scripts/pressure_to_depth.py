#!/usr/bin/env python
"""Convert sensor_msgs/FluidPressure published by uuv_simulator into a
PoseWithCovarianceStamped that carries only the z (depth) component.
Lets robot_localization fuse depth without a custom pressure plugin.

Constants from Table I of the paper:
    standard pressure : 101.325 kPa
    kPa per metre     : 9.80638
    sensor sigma      : 3.0 Pa
"""
from __future__ import print_function

import rospy
from sensor_msgs.msg import FluidPressure
from geometry_msgs.msg import PoseWithCovarianceStamped


STD_PRESSURE_KPA = 101.325
KPA_PER_M = 9.80638
SIGMA_PA = 3.0


class PressureToDepth(object):
    def __init__(self):
        self.frame_id = rospy.get_param("~frame_id", "odom")
        self.pub = rospy.Publisher("/seaclear/depth_pose",
                                   PoseWithCovarianceStamped, queue_size=10)
        self.sub = rospy.Subscriber("/rexrov/pressure", FluidPressure,
                                    self.cb, queue_size=20)

    def cb(self, msg):
        # uuv_simulator's SubseaPressureROSPlugin publishes the value in kPa
        # despite the FluidPressure.msg field nominally being Pa, following
        # the formula  p = standardPressure - z * kPaPerM  (kPa).
        pressure_kpa = msg.fluid_pressure
        depth_m = (pressure_kpa - STD_PRESSURE_KPA) / KPA_PER_M
        # Depth is positive downward; world z is up, so vehicle z = -depth.
        z = -depth_m

        sigma_m = SIGMA_PA / KPA_PER_M

        out = PoseWithCovarianceStamped()
        out.header = msg.header
        out.header.frame_id = self.frame_id
        out.pose.pose.position.z = z
        out.pose.pose.orientation.w = 1.0
        cov = [0.0] * 36
        cov[0] = 1e6
        cov[7] = 1e6
        cov[14] = max(sigma_m * sigma_m, 1e-6)
        cov[21] = 1e6
        cov[28] = 1e6
        cov[35] = 1e6
        out.pose.covariance = cov
        self.pub.publish(out)


if __name__ == "__main__":
    rospy.init_node("pressure_to_depth")
    PressureToDepth()
    rospy.spin()
