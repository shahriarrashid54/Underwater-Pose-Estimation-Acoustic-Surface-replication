#!/usr/bin/env python
"""Drive the UUV around a rectangular trajectory by publishing Twist commands
on /rexrov/cmd_vel.  Reproduces the "manually driven on a rectangular
trajectory once" experiment described in Section IV of Maer et al. (2023).
"""
from __future__ import print_function

import math
import rospy
from geometry_msgs.msg import Twist


class RectangleDriver(object):
    def __init__(self):
        self.pub = rospy.Publisher("/rexrov/cmd_vel", Twist, queue_size=1)
        self.surge = float(rospy.get_param("~surge", 0.3))           # m/s along x_body
        self.yaw_rate = float(rospy.get_param("~yaw_rate", 0.25))    # rad/s
        self.depth_dive_time = float(rospy.get_param("~dive_time", 4.0))
        self.dive_speed = float(rospy.get_param("~dive_speed", 0.25))
        self.leg_time = float(rospy.get_param("~leg_time", 12.0))    # forward leg duration
        self.turn_time = math.pi / 2.0 / self.yaw_rate               # 90 deg
        self.start_delay = float(rospy.get_param("~start_delay", 5.0))
        self.legs = int(rospy.get_param("~legs", 4))                 # 4 legs = closed rectangle

    def publish(self, lin_x=0.0, lin_z=0.0, ang_z=0.0):
        msg = Twist()
        msg.linear.x = lin_x
        msg.linear.z = lin_z
        msg.angular.z = ang_z
        self.pub.publish(msg)

    def hold(self, seconds, lin_x=0.0, lin_z=0.0, ang_z=0.0, rate_hz=20):
        rate = rospy.Rate(rate_hz)
        end = rospy.Time.now() + rospy.Duration.from_sec(seconds)
        while not rospy.is_shutdown() and rospy.Time.now() < end:
            self.publish(lin_x, lin_z, ang_z)
            rate.sleep()

    def run(self):
        rospy.loginfo("Trajectory driver waiting %.1fs for stack to settle",
                      self.start_delay)
        rospy.sleep(self.start_delay)

        rospy.loginfo("Diving for %.1fs", self.depth_dive_time)
        self.hold(self.depth_dive_time, lin_z=-self.dive_speed)
        self.hold(2.0)

        for leg in range(self.legs):
            rospy.loginfo("Leg %d/%d: forward %.1fs", leg + 1, self.legs, self.leg_time)
            self.hold(self.leg_time, lin_x=self.surge)
            self.hold(1.0)
            rospy.loginfo("Turn 90 deg in %.1fs", self.turn_time)
            self.hold(self.turn_time, ang_z=self.yaw_rate)
            self.hold(1.0)

        rospy.loginfo("Trajectory complete; holding zero command")
        self.hold(5.0)


if __name__ == "__main__":
    rospy.init_node("trajectory_publisher")
    RectangleDriver().run()
