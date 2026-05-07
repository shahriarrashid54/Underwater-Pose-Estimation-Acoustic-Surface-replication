#!/usr/bin/env python
"""Synthesize the USBL measurement stream described in Section II of the
paper:

  - Gaussian noise on the ground-truth position with sigma = 0.5 m.
  - Each new sample has a 5%% chance of being "stuck" (sensor returns the
    last value for the next 10 seconds, simulating the lockup behavior
    observed in the real device).

The publisher consumes the simulator's ground-truth odometry topic
(/rexrov/pose_gt) and emits a PoseWithCovarianceStamped on
/seaclear/usbl_pose, ready to be ingested by robot_localization.
"""
from __future__ import print_function

import random
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped


SIGMA = 0.5            # m, per paper, "standard deviation sigma = 0.5"
STUCK_PROB = 0.05      # 5%% chance of stuck per measurement
STUCK_DURATION = 10.0  # seconds


class UsblFault(object):
    def __init__(self):
        self.rate_hz = float(rospy.get_param("~rate", 1.0))   # USBL ~1 Hz typical
        self.frame_id = rospy.get_param("~frame_id", "odom")
        self.seed = int(rospy.get_param("~seed", 0))
        if self.seed:
            random.seed(self.seed)

        self.pub = rospy.Publisher("/seaclear/usbl_pose",
                                   PoseWithCovarianceStamped, queue_size=10)
        self.sub = rospy.Subscriber("/rexrov/pose_gt", Odometry,
                                    self.cb, queue_size=10)
        self.last_gt = None
        self.stuck_until = rospy.Time(0)
        self.stuck_msg = None

    def cb(self, msg):
        self.last_gt = msg

    def make_measurement(self, gt):
        out = PoseWithCovarianceStamped()
        out.header.stamp = rospy.Time.now()
        out.header.frame_id = self.frame_id
        out.pose.pose.position.x = gt.pose.pose.position.x + random.gauss(0.0, SIGMA)
        out.pose.pose.position.y = gt.pose.pose.position.y + random.gauss(0.0, SIGMA)
        out.pose.pose.position.z = 0.0
        out.pose.pose.orientation.w = 1.0
        cov = [0.0] * 36
        cov[0] = SIGMA * SIGMA   # x
        cov[7] = SIGMA * SIGMA   # y
        cov[14] = 1e6            # z (effectively unused for USBL)
        cov[21] = 1e6
        cov[28] = 1e6
        cov[35] = 1e6
        out.pose.covariance = cov
        return out

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            if self.last_gt is None:
                rate.sleep()
                continue
            now = rospy.Time.now()
            if now < self.stuck_until and self.stuck_msg is not None:
                msg = PoseWithCovarianceStamped()
                msg.header.stamp = now
                msg.header.frame_id = self.frame_id
                msg.pose = self.stuck_msg.pose
                self.pub.publish(msg)
            else:
                meas = self.make_measurement(self.last_gt)
                if random.random() < STUCK_PROB:
                    rospy.logwarn("USBL stuck for %.1fs", STUCK_DURATION)
                    self.stuck_until = now + rospy.Duration.from_sec(STUCK_DURATION)
                    self.stuck_msg = meas
                self.pub.publish(meas)
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("usbl_fault_filter")
    UsblFault().spin()
