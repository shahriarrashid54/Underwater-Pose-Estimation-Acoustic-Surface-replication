#!/usr/bin/env python
"""Synchronously log /rexrov/pose_gt (ground truth) and /odometry/filtered
(EKF estimate) to a CSV file for offline MSE/plot analysis.

Stops automatically after a configurable duration so a launch file can
finish cleanly when the trajectory ends.
"""
from __future__ import print_function

import csv
import os
import math
import rospy
from nav_msgs.msg import Odometry


def quat_to_euler(q):
    # ZYX (yaw, pitch, roll) Tait-Bryan
    sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2.0 * (q.w * q.y - q.z * q.x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


class Recorder(object):
    def __init__(self):
        self.duration = float(rospy.get_param("~duration", 150.0))
        self.out_path = rospy.get_param(
            "~out_path",
            os.path.join("/root/results", "experiment.csv"))
        self.gt_topic = rospy.get_param("~gt_topic", "/rexrov/pose_gt")
        self.est_topic = rospy.get_param("~est_topic", "/odometry/filtered")

        out_dir = os.path.dirname(self.out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        self.gt = None
        self.est = None
        self.t0 = None

        self.fp = open(self.out_path, "w")
        self.writer = csv.writer(self.fp)
        self.writer.writerow([
            "t",
            "gt_x", "gt_y", "gt_z", "gt_roll", "gt_pitch", "gt_yaw",
            "est_x", "est_y", "est_z", "est_roll", "est_pitch", "est_yaw",
        ])

        rospy.Subscriber(self.gt_topic, Odometry, self.cb_gt, queue_size=20)
        rospy.Subscriber(self.est_topic, Odometry, self.cb_est, queue_size=20)

        self.timer = rospy.Timer(rospy.Duration(0.05), self.tick)
        self.shutdown_at = rospy.Time.now() + rospy.Duration.from_sec(self.duration)

    def cb_gt(self, msg):
        self.gt = msg

    def cb_est(self, msg):
        self.est = msg

    def tick(self, _evt):
        if self.gt is None or self.est is None:
            return
        if self.t0 is None:
            self.t0 = rospy.Time.now()
        t = (rospy.Time.now() - self.t0).to_sec()

        gp = self.gt.pose.pose
        ep = self.est.pose.pose
        gr, gpi, gy = quat_to_euler(gp.orientation)
        er, epi, ey = quat_to_euler(ep.orientation)

        self.writer.writerow([
            "%.4f" % t,
            "%.6f" % gp.position.x, "%.6f" % gp.position.y, "%.6f" % gp.position.z,
            "%.6f" % gr, "%.6f" % gpi, "%.6f" % gy,
            "%.6f" % ep.position.x, "%.6f" % ep.position.y, "%.6f" % ep.position.z,
            "%.6f" % er, "%.6f" % epi, "%.6f" % ey,
        ])

        if rospy.Time.now() >= self.shutdown_at:
            rospy.loginfo("Recording finished -> %s", self.out_path)
            self.fp.flush()
            self.fp.close()
            rospy.signal_shutdown("recording duration reached")


if __name__ == "__main__":
    rospy.init_node("record_experiment")
    Recorder()
    rospy.spin()
