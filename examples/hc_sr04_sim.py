# File: hc_sr04_sim.py
# Date: 21-09-2019
# Author: Saruccio Culmone
#
# Description
# Simulation distance reading from an ultrasonic sensor HC-SR04 in a virtual
# plane environment
#
"""
This script simulates a room with a chair and a sensor near them.
To simulate the walls of the room, the 'SeqPolygon' class will be used
since it was designed for such cases.
"""


import os
import sys

# Add the path of the flatland package
sys.path.insert(0, os.path.abspath('../flatland'))


from trace import logger
import copy

from shape import Shape
import shapes
from flatland import FlatLand
import geom_utils as geom
from virtual_sensor import VirtualSensor
import numpy as np


# Compose the simulated environment
# The room
room_sides = [('start', (0, 0)), ('right', 380), ('up', 30), ('left', 50),
              ('up', 40), ('left', 20), ('up', 300), ('right', 20), ('up', 30),
              ('skip', 'yes'), ('up', 80), ('skip', 'off'), ('up', 50),
              ('left', 40), ('skip', 'on'),('left', 80), ('skip', 'off'),
              ('left', 210), ('down', 430) ]
room = shapes.SeqPolygon(room_sides)
logger.info("Room points= {}".format(room.size()))

# The chair composition
def chair_constructor():
    """Footprint of a four legged classic chair"""
    leg_side = 5 # cm
    leg1 = shapes.Circle(leg_side)
    leg1.color("r")
    leg2 = shapes.Circle(leg_side)
    leg2.traslate(30, 0)
    leg2.color("r")
    leg3 = shapes.Circle(leg_side)
    leg3.traslate(30, 40)
    leg3.color("k")
    leg4 = shapes.Circle(leg_side)
    leg4.traslate(0,40)
    leg4.color("r")

    legs = [leg1, leg2, leg3, leg4]
    chair = shapes.CompoundShape(legs, "chair")
    return chair

# Create and pose the chair into the room
chair = chair_constructor()
chair.traslate(200,300)

# Compose flatland environment with all objects in it
sim_env = FlatLand("HC_SR04 test bench")
sim_env.add_objects(room, chair)
logger.info("Bench points= {}".format(sim_env.size()))

# Define an configure two sensors
# S1 - HC-SR04
S1 = VirtualSensor(name="HC-SR04_01", beam=30, range=50, accuracy=2, mnt_pt=(0, 0), mnt_orient=90)
S1.load_env(sim_env.venv)
S1.place((175, 300), 45)

# S2 - HC-SR04
S2 = VirtualSensor(name="HC-SR04_02", beam=45, range=90, accuracy=2, mnt_pt=(0, 0), mnt_orient=90)
S2.set_color("y")

# Supply virtual environment to sensors
# Loaded from S2 the same environment will be available for all other sensors
S2.load_env(sim_env.venv)

# Add sensors to the virtual environment
sim_env.add_sensors(S1, S2)

# For debugging purposes plot S1 at first position with its range of vision
S1.plot()
S1.plot_surroundings()

meas_point1 = S1.read()
logger.info("Dist1= {}".format(meas_point1[0]))

# Transform reading in rectangular coordinates
meas_rect_point1 = geom.pol2cart(meas_point1[0], np.deg2rad(meas_point1[1]))

# Move the measured point into the external coordinate system
S1x, S1y = S1.position
S1alpha = S1.orientation # radiant since its the internal value
S1_sys = (S1x, S1y, S1alpha, True) # Orientation in rad so flag is True
ext_meas_point1 = geom.localpos_to_globalpos(meas_rect_point1, S1_sys)

# Plot the measured point and the nearestpoint that is detected
geom.plot_segment(S1.position, ext_meas_point1)
geom.plot_point(ext_meas_point1)


# Plot the really detected point, taken from internal sensor structure
real_rect_point1 = geom.pol2cart(S1.detected_point[0],
                                 np.deg2rad(S1.detected_point[1]))
ext_real_point1 = geom.localpos_to_globalpos(real_rect_point1, S1_sys)
geom.plot_point(ext_real_point1, pen_trait="+")

# S2 scan the space in front of it
# Position and orientation of the S2 sysref
# Note that orientation is espressed in degree -> flag is False
S2_sys = (220, 400, -90, False)
S2.place((S2_sys[0], S2_sys[1]), S2_sys[2])
S2.plot_surroundings()
scan_points = S2.scan(-90, 90)

# Transform detected points in rectangular coordinates
scan_meas = [geom.pol2cart(ppoint[0], np.deg2rad(ppoint[1])) for ppoint in scan_points]
# Calculate points in the esternal sysref
ext_scan_meas = [geom.localpos_to_globalpos(meas_point, S2_sys) for meas_point in scan_meas]

geom.plot(ext_scan_meas)

# Show overall picture
sim_env.show()



