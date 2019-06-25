#puts above directory into the path
import sys
sys.path.append("..")

import time
from datetime import date
import os
import signal
import numpy as np
import matplotlib.pyplot as plt
import vrep

from utils.motor_setup import Motors

def signal_handler(signal, frame):
	motors.tcp_close()

signal.signal(signal.SIGINT, signal_handler)

script_dir = os.path.dirname(__file__)
results_dir = os.path.join(script_dir, 'Motor_Data/')
if not os.path.isdir(results_dir):
    os.makedirs(results_dir)

#Constants for motor setup
socket_ip = '192.168.1.18'
socket_port = 1122
P = 0
PL = 0
I = 0
IL = 0
D = 0

motors = Motors(P ,PL ,I, IL ,D)
motors.tcp_init(socket_ip, socket_port)
print("Arming motors now...")
motors.arm_motors()
time.sleep(1)


num_limitswitch_bumps = 1
bumps = 0

enc_position = np.zeros(8)
while(num_limitswitch_bumps > bumps):
	enc_position = enc_position + 1000
	motors.command_motors(enc_position)
	limit_switches = motors.limit_switches_data
	print(limit_switches)
	time.sleep(0.01)

print("done")
motors.tcp_close()


# #optitrak setup
# server_ip = "192.168.1.27"
# multicastAddress = "239.255.42.99"
# print_trak_data = False
# optitrack_joint_names = ['base', 'j1', 'j2']
# ids = [0, 1, 2]

# #Tracking class
# print("Starting streaming client now...")
# streamingClient = NatNetClient(server_ip, multicastAddress, verbose = print_trak_data)
# NatNet = NatNetFuncs()
# streamingClient.newFrameListener = NatNet.receiveNewFrame
# streamingClient.rigidBodyListListener = NatNet.receiveRigidBodyFrameList

# prev_frame = 0
# time.sleep(0.5)
# streamingClient.run()
# time.sleep(0.5)
# track_data = data(optitrack_joint_names,ids)
# track_data.parse_data(NatNet.joint_data, NatNet.frame) #updates the frame and data that is being used
# old_frame = track_data.frame

"""
#What i need to do
conversion of motor encoder counts to distance
integrate limit switches
record data
setup tracker info
plot tracker data and encoder data
"""