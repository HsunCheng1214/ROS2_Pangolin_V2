#！usr/bin python3

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from sensor_msgs.msg import Imu
import time
import os, sys, math
import numpy as np

import threading


sys.path.append('/home/ubuntu/pangolin_ws/ros2-pangolin-robot/pangolin_control/driver')
# sys.path.append('/home/puppypi/puppypi_ws/src/puppy_control/driver')
from Pangolin_ControlCmd import PangolinControl
from Pangolin_Config import *


class Pangolin(Node):
    def __init__(self):
        super().__init__('pangolin_control')
        self.control_cmd = PangolinControl()

        self.joy_subscriber_ = self.create_subscription(Joy, 'joy', self.joy_callback, 0)
        self.imu_subscriber_ = self.create_subscription(Imu, 'imu', self.imu_callback, 1)
        self.cmd_vel_subscriber_ = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 1)

        self.is_first_time = True
        self.is_disalbe_motor = False
        self.is_freedom_mode = False
        self.is_stance_mode = False
        self.is_record_mode = False
        self.is_curl = False
        self.last_joy_msgs_buttons = []
        self.time_1 = 0

# destroy ros    
    def destroy(self):
        self.cmd_vel_subscriber_.destroy()
        super().destroy_node()
    

    def joy_callback(self, msg):
        # X:0, A:1, B:2, Y:3
        # LB:4, RB:5, LT:6, RT:7
        # BACK:8, START:9, 
        # L3:10, R3:11  

        if self.is_first_time == True:
            self.last_joy_msgs_buttons = msg.buttons
            self.is_first_time = False

    # Stance control mode
        if msg.buttons[0] != self.last_joy_msgs_buttons[0]:
            self.is_stance_mode = not self.is_stance_mode

        if self.is_stance_mode == True:
            self.get_logger().info(f'Stance control mode')
            if msg.axes[1]>0.5:
                self.control_cmd.x += 1.5
            elif msg.axes[1]<-0.5:
                self.control_cmd.x -= 1.5
            if msg.axes[0]>0.5:
                self.control_cmd.z += 1.5
            elif msg.axes[0]<-0.5:
                self.control_cmd.z -= 1.5

            self.control_cmd.pitch = msg.axes[2]*15
            self.control_cmd.roll = msg.axes[3]*15

            # self.get_logger().info()
            # self.get_logger().info(f'button3: {self.control_cmd.stance_control()}')
        else:
            self.control_cmd.x = 0
            self.control_cmd.z = LEG_HEIGHT
            self.control_cmd.pitch = 0
            self.control_cmd.roll = 0
            

    # Reset mode
        if msg.buttons[1] != self.last_joy_msgs_buttons[1]:
            self.get_logger().info(f'Reset mode')
            self.control_cmd.reset_to_orginal()

    # Curl action mode
        if msg.buttons[2] != self.last_joy_msgs_buttons[2]:
            self.get_logger().info(f'Curl action mode')
            if self.is_curl == False:
                self.control_cmd.run_action_get_down()
                self.is_curl = True
            else:
                self.control_cmd.run_action_stand_up()
                self.is_curl = False

    # Freedom control mode
        if msg.buttons[3] != self.last_joy_msgs_buttons[3]:
            self.is_freedom_mode = not self.is_freedom_mode
            

        if self.is_freedom_mode == True:
            self.control_cmd.control_cmd.leg_motor_position_control(position = {"motor1":int(msg.axes[0]*1000 + self.control_cmd.motor_center_position["motor1"]), 
                                                                                "motor2":int(msg.axes[1]*1000 + self.control_cmd.motor_center_position["motor2"]), 
                                                                                "motor3":0, 
                                                                                "motor4":int(msg.axes[2]*1000 + self.control_cmd.motor_center_position["motor4"]), 
                                                                                "motor5":int(msg.axes[3]*1000 + self.control_cmd.motor_center_position["motor5"])})

    # Record mode
        if msg.buttons[4] != self.last_joy_msgs_buttons[4]:
            self.get_logger().info(f'record mode')
            if self.is_record_mode == False:
                self.control_cmd.start_record_action_points()
                self.is_record_mode = True
            else:
                self.control_cmd.stop_record_action_points()
                self.is_record_mode = False

        if msg.buttons[5] != self.last_joy_msgs_buttons[5]:
            self.get_logger().info(f'replay')    
            self.control_cmd.replay_recorded_data()
  

        if msg.buttons[8] != self.last_joy_msgs_buttons[8]:
            # self.get_logger().info(f'disable motor')
            # if self.is_disalbe_motor == False:
            #     self.control_cmd.disable_all_motor()
            #     self.is_disalbe_motor = True
            # else:
            #     self.control_cmd.enable_all_motor()
            #     self.is_disalbe_motor = False
            pass

        self.last_joy_msgs_buttons = msg.buttons

# Pangolin cmd_vel callback
    def cmd_vel_callback(self, msg):

        # self.get_logger().info(f'linear.x: {msg.linear.x} angular.z: {msg.angular.z}')

        # self.control_cmd.set_servo_rate([msg.linear.x - msg.angular.z, msg.linear.x + msg.angular.z])

        if round(msg.linear.x, 0) != 0:
            
            self.control_cmd.set_servo_rate([msg.linear.x, msg.linear.x])
            if self.control_cmd.is_walking == False:
                self.get_logger().info(f'cmd_vel linear')
                self.control_cmd.set_gait_name('move_linear')
                self.control_cmd.start_gait()

        elif round(msg.angular.z, 0) < 0:
            
            self.control_cmd.set_servo_rate([msg.angular.z, msg.angular.z])
            if self.control_cmd.is_walking == False:
                self.get_logger().info(f'cmd_vel turn_right')
                self.control_cmd.set_gait_name('turn_right')
                self.control_cmd.start_gait()

        elif round(msg.angular.z, 0) > 0:
            
            self.control_cmd.set_servo_rate([-msg.angular.z, -msg.angular.z])
            if self.control_cmd.is_walking == False:
                self.get_logger().info(f'cmd_vel turn_left')
                self.control_cmd.set_gait_name('turn_left')
                self.control_cmd.start_gait()
        
        else:
            
            if self.control_cmd.is_walking == True:
                # self.get_logger().info(f'cmd_vel stop')
                self.control_cmd.stop_gait()

# Pangolin imu callback
    def imu_callback(self, msg):
        
        # Get the imu msgs
        self.q0 = msg.orientation.x
        self.q1 = msg.orientation.y
        self.q2 = msg.orientation.z
        self.q3 = msg.orientation.w

        # Calculate eular angle
        pitch = -math.asin(-2*self.q1*self.q3+2*self.q0*self.q2)*57.3
        roll = math.atan2(2*self.q2*self.q3+2*self.q0*self.q1,-2*self.q1*self.q1-2*self.q2*self.q2+1)*57.3
        yaw = math.atan2(2*(self.q1*self.q2 + self.q0*self.q3),self.q0*self.q0+self.q1*self.q1-self.q2*self.q2-self.q3*self.q3)*57.3

        # self.get_logger().info(f'pitch: {pitch}')
        self.get_logger().info(f'roll: {roll}')
        # self.get_logger().info(f'yaw: {yaw}')
        # Detect wether the robot has fallen over, then stand up.
        # if abs(roll) < 70 :
        #     self.time_1 = time.time()

        # elif abs(roll) >= 70:
        #     self.get_logger().info(f'imu stand up mode')
            
        #     if (time.time() - self.time_1 > 3):
        #         self.control_cmd.run_action_stand_up()
        #         self.is_curl = False

            

def main(args=None):
    rclpy.init(args=args)
    PangolinControl = Pangolin()

    rclpy.spin(PangolinControl)
    
    PangolinControl.destroy()
    rclpy.shutdown()


if __name__ == '__main__':
    main()