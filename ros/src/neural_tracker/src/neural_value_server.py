#!/usr/bin/env python

#Missing Imports
import rospy
import tensorflow as tf
import Utils
import pickle
import numpy as np
import itertools
from neural_policy import NeuralPolicy

#from value_function_srvs.srv import *
import value_function_srvs.srv


# Network files (param) format:
# List of picklefiles

# Picklefile format:
# {"weights":<np.array>,
#  "layers":<[list ints]>,
#  "control_bounds_upper":<[list of doubles]>
#  "control_bounds_lower":<[list of doubles]>
#  "tracking_error_bound":<[list of doubles]>
#  "planner_params":<{
#                     "max_speed":[list doubles],
#                     "max_vel_dist":[list doubles],
#                     "max_acc_dist":[list doubles]}>
# }

class NeuralValueServer(object):
    def __init__(self):
        self._initialized = False

    # Initialization and loading parameters.
    def Initialize(self):
        self._name = rospy.get_name() + "/neural_value_server"

        # Load parameters.
        if not self.LoadParameters():
            rospy.logerr("%s: Error loading parameters.", self._name)
            return False

        # Register callbacks.
        if not self.RegisterCallbacks():
            rospy.logerr("%s: Error registering callbacks.", self._name)
            return False

        sess = tf.Session();
        ids = range(len(self._network_files + self._network_files))

        self.policies = [ NeuralPolicy(f, i, sess=sess, ppick=15, pick_=15) for f, i in
                          zip(self._network_files + self._network_files, ids) ]

        self._initialized = True
        return True

    def LoadParameters(self):
        # Neural Net Related Stuff

        # Get the network filename for Neural Net
        if not rospy.has_param("~network_files"):
            return False
        self._network_files = rospy.get_param("~network_files")

        #----------------------------------

        # Names for various services

        if not rospy.has_param("~srv/optimal_control"):
            return False
        self._optimal_control_name = rospy.get_param("~srv/optimal_control")
        if not rospy.has_param("~srv/tracking_bound"):
            return False
        self._tracking_bound_name = rospy.get_param("~srv/tracking_bound")
        if not rospy.has_param("~srv/switching_tracking_bound"):
            return False
        self._switching_tracking_bound_name = rospy.get_param("~srv/switching_tracking_bound")
        if not rospy.has_param("~srv/guaranteed_switching_time"):
            return False
        self._guaranteed_switching_time_name = rospy.get_param("~srv/guaranteed_switching_time")
        if not rospy.has_param("~srv/guaranteed_switching_distance"):
            return False
        self._guaranteed_switching_distance_name = rospy.get_param("~srv/guaranteed_switching_distance")
        if not rospy.has_param("~srv/priority"):
            return False
        self._priority_name = rospy.get_param("~srv/priority")
        if not rospy.has_param("~srv/max_planner_speed"):
            return False
        self._max_planner_speed_name = rospy.get_param("~srv/max_planner_speed")
        if not rospy.has_param("~srv/best_possible_time"):
            return False
        self._best_possible_time_name = rospy.get_param("~srv/best_possible_time")

        return True

    def RegisterCallbacks(self):
        # Publishers.
        self._optimal_control_srv               = rospy.Service(self._optimal_control_name, value_function_srvs.srv.OptimalControl, self.OptimalControlCallback)
        self._tracking_bound_srv                = rospy.Service(self._tracking_bound_name, value_function_srvs.srv.TrackingBoundBox, self.TrackingBoundCallback)
        self._switching_tracking_bound_srv      = rospy.Service(self._switching_tracking_bound_name, value_function_srvs.srv.SwitchingTrackingBoundBox, self.SwitchingTrackingBoundCallback)
        self._guaranteed_switching_time_srv     = rospy.Service(self._guaranteed_switching_time_name, value_function_srvs.srv.GuaranteedSwitchingTime, self.GuaranteedSwitchingTimeCallback)
        self._guaranteed_switching_distance_srv = rospy.Service(self._guaranteed_switching_distance_name, value_function_srvs.srv.GuaranteedSwitchingDistance, self.GuaranteedSwitchingDistanceCallback)
        self._priority_srv                      = rospy.Service(self._priority_name, value_function_srvs.srv.Priority, self.PriorityCallback)
        self._max_planner_speed_srv             = rospy.Service(self._max_planner_speed_name, value_function_srvs.srv.GeometricPlannerSpeed, self.MaxPlannerSpeedCallback)
        self._best_possible_time_srv            = rospy.Service(self._best_possible_time_name, value_function_srvs.srv.GeometricPlannerTime, self.BestPossibleTimeCallback)

        return True

    def OptimalControlCallback(self,req):
        policy = self.policies[req.id]
        control = policy.OptimalControl(Utils.UnpackState(req.state))
        res = value_function_srvs.srv.OptimalControlResponse()
        res.control = Utils.PackControl(control)
        return  res

    def TrackingBoundCallback(self,req):
        policy = self.policies[req.id]
        tracking_error_bound = policy.tracking_error_bound
        res = value_function_srvs.srv.TrackingBoundBoxResponse()
        res.x = tracking_error_bound[0]
        res.y = tracking_error_bound[1]
        res.z = tracking_error_bound[2]
        return res

    def SwitchingTrackingBoundCallback(self,req):
        # NOTE: we are not really doing switching (for now).
        policy = self.policies[req.to_id]
        tracking_error_bound = policy.tracking_error_bound
        res = value_function_srvs.srv.SwitchingTrackingBoundBoxResponse()
        res.x = tracking_error_bound[0]
        res.y = tracking_error_bound[1]
        res.z = tracking_error_bound[2]
        return res

    def GuaranteedSwitchingTimeCallback(self,req):
#        rospy.logwarn_throttle(1.0, "GuaranteedSwitchingTimeCallback NOT implemented")
#        rospy.logwarn("GuaranteedSwitchingTimeCallback NOT implemented")
        res = value_function_srvs.srv.GuaranteedSwitchingTimeResponse()
        res.x = 0.0
        res.y = 0.0
        res.z = 0.0
        return res

    def GuaranteedSwitchingDistanceCallback(self,req):
#        rospy.logwarn_throttle(1.0, "GuaranteedSwitchingDistanceCallback NOT implemented")
#        rospy.logwarn("GuaranteedSwitchingDistanceCallback NOT implemented")
        res = value_function_srvs.srv.GuaranteedSwitchingDistanceResponse()
        res.x = 0
        res.y = 0
        res.z = 0
        return res

    def PriorityCallback(self,req):
        res = value_function_srvs.srv.PriorityResponse()
#        res.priority = 1.0
        res.priority = 0.99
        return res

    def MaxPlannerSpeedCallback(self,req):
        policy = self.policies[req.id]
        max_speed = policy.max_speed
        res = value_function_srvs.srv.GeometricPlannerSpeedResponse()
        res.x = max_speed[0]
        res.y = max_speed[1]
        res.z = max_speed[2]
        return res

    def BestPossibleTimeCallback(self,req):
        policy = self.policies[req.id]
        max_speed = policy.max_speed
        start = Utils.UnpackPoint(req.start)
        stop  = Utils.UnpackPoint(req.stop)
        diff = stop - start
        t1 = abs(diff[0])/max_speed[0]
        t2 = abs(diff[1])/max_speed[1]
        t3 = abs(diff[2])/max_speed[2]
        res = value_function_srvs.srv.GeometricPlannerTimeResponse()
        res.time = max(t1,t2,t3)
        return res
