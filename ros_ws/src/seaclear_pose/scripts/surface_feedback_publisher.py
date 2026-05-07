#!/usr/bin/env python
"""Surface-based intermittent position fix (Section V).

Models a high-precision sensor that becomes available periodically (e.g. a
waterproofed GPS on the UUV during resurfacing, or a UAV camera fix).
The paper uses a Gaussian noise of sigma = 0.05 m on the corrupted ground
truth.  Period is configurable; experiments reported are 1 s, 5 s, 10 s,
and 30 s.
"""
from __future__ import print_function

import random
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped


SIGMA = 0.05  # m, GPS-grade datasheet accuracy as stated in the paper


class SurfaceFix(object):
    def __init__(self):
        self.period = float(rospy.get_param("~period", 1.0))
        self.frame_id = rospy.get_param("~frame_id", "odom")
        self.seed = int(rospy.get_param("~seed", 0))
        if self.seed:
            random.seed(self.seed)

        self.pub = rospy.Publisher("/seaclear/surface_pose",
                                   PoseWithCovarianceStamped, queue_size=10)
        self.sub = rospy.Subscriber("/rexrov/pose_gt", Odometry,
                                    self.cb, queue_size=10)
        self.last_gt = None

    def cb(self, msg):
        self.last_gt = msg

    def emit(self, _evt):
        if self.last_gt is None:
            return
        gt = self.last_gt
        out = PoseWithCovarianceStamped()
        out.header.stamp = rospy.Time.now()
        out.header.frame_id = self.frame_id
        out.pose.pose.position.x = gt.pose.pose.position.x + random.gauss(0.0, SIGMA)
        out.pose.pose.position.y = gt.pose.pose.position.y + random.gauss(0.0, SIGMA)
        out.pose.pose.position.z = gt.pose.pose.position.z + random.gauss(0.0, SIGMA)
        out.pose.pose.orientation.w = 1.0
        cov = [0.0] * 36
        cov[0] = SIGMA * SIGMA
        cov[7] = SIGMA * SIGMA
        cov[14] = SIGMA * SIGMA
        cov[21] = 1e6
        cov[28] = 1e6
        cov[35] = 1e6
        out.pose.covariance = cov
        self.pub.publish(out)


if __name__ == "__main__":
    rospy.init_node("surface_feedback_publisher")
    node = SurfaceFix()
    rospy.Timer(rospy.Duration.from_sec(node.period), node.emit)
    rospy.spin()
