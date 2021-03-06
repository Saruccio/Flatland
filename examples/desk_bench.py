# File: desk_bench.py
# Date: 05-10-2019
# Author: Saruccio Culmone
#
# Description
# Confronto in ambiente simulato tra misure reali e misure simulate
#
"""
This script creates a virtual environemt from a real one in order to allow
the comparison among virtual and real measures.
"""


import os
import sys
import time

# Add the path of the flatland package
sys.path.insert(0, os.path.abspath('../flatland'))

print("---------------------------------------------------------------------")
print("\n".join(sys.path))
print("---------------------------------------------------------------------")
print()

from trace import logger
from shapes import Circle, SeqPolygon
from flatland import FlatLand
import geom_utils as geom
from virtual_sensor import VirtualSensor, load_measures
import numpy as np


# This Flatland environment is the virtualization of an empty desk where the
# sensor is positioned at the origin of the reference system and in front
# of the sensor are placed a glass and a pen.
# At the left and right side of the desk there are the walls of the room.
#
# The unit of measurement is 1 cm
#

#
# Define the room sides as a 'SeqPolygon' object that set the boundaries
# of the test bench
room_sides = [('start', (40, -40)), ('up', 200), ('start', (-97, -40)),
              ('up', 200)]
room = SeqPolygon(room_sides)
#logger.info("Room points= {}".format(room.size()))

# Define the footprint of the pen as a small circle and put it just in front
# of the origin (where the sensor wiil be placed)
pen = Circle(0.25)
pen.move(0.0, 32.0)

# Define the footprint of the glass and pose it far at the left of the sensor
glass = Circle(2.0)
glass.move(-27.0, 45.0)

# Populate the Flatlant environment with all objects just defined
desk_bench = FlatLand("Desk bench")
desk_bench.add_objects(room, pen, glass)
logger.info("Bench points= {}".format(desk_bench.size()))

desk_bench.show()

# Define the sensor as a simulation of the ultrasonic sensor HC-SR04 and pose it
# at the origin of the Flatland
# The sensor orientation is horizontal
S1 = VirtualSensor(name="HC_SR04", beam=40, range=60, 
                   mnt_pt=(0.0, 0.0), mnt_orient=90)
S1.set_color("k")
S1.place((0.0, 0.0), 0)

# Make aware the sensor of the external environment
S1.load_env(desk_bench.venv)

# Add sensor to the virtual environment
desk_bench.add_sensors(S1)

# Put the sensor in vertical position and run a range scan
S1.place((0, 0), 90)
scan_points = S1.scan(-90, 90)
logger.info("Num. scan points= {}".format(len(scan_points)))

# Scan points are in polar coordinates in the sensor reference system,
# Get the range measurements related to the Flatland environment.

# Transform point in rectangular coordinates
rect_points = [geom.pol2cart(ppol[0], np.deg2rad(ppol[1])) for ppol in scan_points if ppol[0] != 0.0]
logger.info("Num valid points= {}".format(len(rect_points)))

# Transform the points as seen from the coordinate system external to the sensor,
# given sensor position and orientation in the external coordinate system.
xo, yo = S1.position
alpha = S1.orientation # radiant
sensor_sys = (xo, yo, alpha, True)

meas_points = [geom.localpos_to_globalpos(rpoint, sensor_sys) for rpoint in rect_points]

# The measured points are related to the external coordinate system.

geom.plot(meas_points)

# The range measurement simulated so far can be compared with the results
# obtained during an experiment using a real sensor placed in the
# origin of the reference system on a real desk bench.
# Those measurements have been saved into a CSV file but are related to
# the coordinate system local to the sensor.
data_path = "."
data_file = "sonar_plot_2019-08-25_12.24.32.csv"
filepath = os.path.join(data_path, data_file)

# Since the real range measurements are local to the sensor, the last can
# load and transform them in points related to the external coordinate systems,
# as if they were its own virtual measuremens.
# In order to distiguish them from the simulates ones, a red pen color will
# be used for the plot.
real_measures = load_measures(S1, filepath)
geom.plot(real_measures, pen_color="r")

# Show environment and data
desk_bench.show()

# As you can see, the simulation in the range of the sensor (60 cm) is
# pretty good.
# On the other end, the actual measurements are affected by noise.
# furthermore, due to echo bouncing between the walls, the real sensor
# provides measurements even over 60 cm, even if clearly false measurements.
#
