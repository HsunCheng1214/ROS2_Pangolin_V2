#！usr/bin python3

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

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
        self.cmd_vel_subscriber_ = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 1)

        self.is_first_time = True
        self.is_disalbe_motor = True
        self.is_freedom_mode = False
        self.is_stance_mode = False
        self.is_curl = False
        self.last_joy_msgs_buttons = []

# destroy ros    
    def destroy(self):
        self.cmd_vel_subscriber_.destroy()
        super().destroy_node()
    

    def joy_callback(self, msg):
        if self.is_first_time == True:
            self.last_joy_msgs_buttons = msg.buttons
            self.is_first_time = False

        if msg.buttons[0] != self.last_joy_msgs_buttons[0]:
            self.is_stance_mode = not self.is_stance_mode

        if self.is_stance_mode == True:
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
            self.get_logger().info(f'button3: {self.control_cmd.stance_control()}')
        else:
            self.control_cmd.x = 0
            self.control_cmd.z = LEG_HEIGHT
            self.control_cmd.pitch = 0
            self.control_cmd.roll = 0
            


        if msg.buttons[1] != self.last_joy_msgs_buttons[1]:
            self.control_cmd.reset_to_orginal()

        if msg.buttons[2] != self.last_joy_msgs_buttons[2]:
            # self.get_logger().info(f'button3: {self.is_curl}')
            if self.is_curl == False:
                self.control_cmd.run_action_get_down()
                self.is_curl = True
            else:
                self.control_cmd.run_action_stand_up()
                self.is_curl = False


        if msg.buttons[3] != self.last_joy_msgs_buttons[3]:
            self.is_freedom_mode = not self.is_freedom_mode
            

        if self.is_freedom_mode == True:
            self.control_cmd.control_cmd.leg_motor_position_control(position = {"motor1":int(msg.axes[0]*1000 + self.control_cmd.motor_center_position["motor1"]), 
                                                                                "motor2":int(msg.axes[1]*1000 + self.control_cmd.motor_center_position["motor2"]), 
                                                                                "motor3":0, 
                                                                                "motor4":int(msg.axes[2]*1000 + self.control_cmd.motor_center_position["motor4"]), 
                                                                                "motor5":int(msg.axes[3]*1000 + self.control_cmd.motor_center_position["motor5"])})


        if msg.buttons[4] != self.last_joy_msgs_buttons[4]:
            self.control_cmd.controlcmd.start_recording()

        if msg.buttons[5] != self.last_joy_msgs_buttons[5]:
            self.control_cmd.controlcmd.stop_record_action_points()
            self.get_logger().info('last_joy_msgs_buttons: %s' % self.last_joy_msgs_buttons)

        if msg.buttons[8] != self.last_joy_msgs_buttons[8]:
            if self.is_disalbe_motor == True:
                self.control_cmd_old.openPort()
                self.control_cmd_old.enableMotor()
                self.is_disalbe_motor = False
            
            else:
                self.control_cmd_old.disableMotor()
                self.is_disalbe_motor = True

        self.last_joy_msgs_buttons = msg.buttons

# puppy cmd vel callback
    def cmd_vel_callback(self, msg):

        self.get_logger().info(f'linear.x: {msg.linear.x} angular.z: {msg.angular.z}')

        # self.control_cmd.set_servo_rate([msg.linear.x - msg.angular.z, msg.linear.x + msg.angular.z])

        if round(msg.linear.x, 0) != 0:
            self.control_cmd.set_servo_rate([msg.linear.x, msg.linear.x])
            if self.control_cmd.is_walking == False:
                self.control_cmd.set_gait_name('move_linear')
                self.control_cmd.start_gait()

        elif round(msg.angular.z, 0) > 0:
            self.control_cmd.set_servo_rate([-msg.angular.z, -msg.angular.z])
            if self.control_cmd.is_walking == False:
                self.control_cmd.set_gait_name('turn_right')
                self.control_cmd.start_gait()

        elif round(msg.angular.z, 0) < 0:
            self.control_cmd.set_servo_rate([msg.angular.z, msg.angular.z])
            if self.control_cmd.is_walking == False:
                self.control_cmd.set_gait_name('turn_left')
                self.control_cmd.start_gait()
        
        else:
            if self.control_cmd.is_walking == True:
                self.control_cmd.stop_gait()


def main(args=None):
    rclpy.init(args=args)
    PangolinControl = Pangolin()

    rclpy.spin(PangolinControl)
    
    PangolinControl.destroy()
    rclpy.shutdown()


if __name__ == '__main__':
    main()