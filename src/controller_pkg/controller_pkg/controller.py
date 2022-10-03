from importlib.util import set_loader
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8

# Idan driver
from autoware_auto_msgs.msg import VehicleControlCommand

# vaya import switch ego speed
from nav_msgs.msg import OccupancyGrid, Odometry

# PID Controller class
from .submodules.controllerPID import PID

# Generic Imports
import enum
import math
import numpy as np
import cv2

class State(enum.Enum):
    ACC = 1
    BRAKE = 2
    LEFT = 3
    RIGHT = 4
    EMERGANCY = 5


class Controller(Node):
    """
        ACC = 0
        BRAKE = 1
        LEFT = 2
        RIGHT = 3
        EMERGANCY = 4
    """

    def __init__(self):
        super().__init__("controller")

        # subscribers
        self.create_subscription(Int8, "switch_cmd", self.switch_cb, 10)
        self.create_subscription(
            VehicleControlCommand, "raw_command_master", self.vel_pid_cb, 10)

        # publishers
        self.idan_pub = self.create_publisher(
            VehicleControlCommand, "raw_command", 10)
        self.timer = self.create_timer(0.1, self.control)

        # ego variables
        self.state = 0  # default ACC
        self.idan_msg: VehicleControlCommand = VehicleControlCommand()
        
        # PID
        self.velocity_PID_SLOW = PID(kp=0.8, ki=0, kd=0.13)
        self.speed = None
        self.desired_speed = 0.0

    def switch_cb(self, msg: Int8):
        # update the current state of the switch
        self.state = msg.data

    def vel_pid_cb(self, msg: VehicleControlCommand):
        # update the idan command
        self.idan_msg = msg
    
    def ego_motion_callback(self, msg: Odometry):
        """
        get ego motion data
        """
        self.speed = np.linalg.norm([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ])

    def velocity_controller(self):
        out = 0.0
        # calc the error from now to the desierd Velocity
        error_from_desired = (self.speed - self.desired_speed) / 35.0
        out = self.velocity_PID_SLOW.output(error_from_desired)
        out = -out
        return out

    def control(self):
        """
            This method decieds the next step of the vehicle based on the given state
            from the switch.
        """
        # TODO Emergancy
        if self.state == State.EMERGANCY.value:
            self.idan_msg.long_accel_mps2 = -0.4
            self.get_logger().info("EBrake")

        # TODO Brake
        elif self.state == State.BRAKE.value:
            # TODO PID control - input - ( desired speed, our speed) - output - (long_aacel_mps2 -  pid low
            # value)
            if self.speed < 1.3:
                self.idan_msg.long_accel_mps2 = -0.2
            else:
                self.idan_msg.long_accel_mps2 = self.velocity_controller()
            self.get_logger().info("Brake and slow")

        # TODO Right
        elif self.state == State.RIGHT.value:
            # TODO change file (from here)
            # TODO and add the raw command from ACC
            self.get_logger().info("Moving to right lane")
            
        # TODO Left
        elif self.state == State.LEFT.value:
            # TODO change file (from here)
            # TODO and add the raw command from ACC
            self.get_logger().info("Moving to left lane")

        self.idan_pub.publish(self.idan_msg)


def main(args=None):
    rclpy.init(args=args)

    control = Controller()

    rclpy.spin(control)

    control.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
