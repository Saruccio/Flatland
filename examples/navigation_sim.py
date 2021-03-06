# File: hc_sr04_sim.py
# Date: 16-11-2019
# Author: Saruccio Culmone
#
"""
This script simulates a room with a chair and other objects.
To simulate the walls of the room, the 'SeqPolygon' class will be used
since it was designed for such cases.

A Vehicle navigates into the room scanning the environment at every step.
All collected points are plotted in the virtual environment.
"""


import os
import sys
import time

# Add the path of the flatland package
sys.path.insert(0, os.path.abspath('../flatland'))


from trace import logger
logger.add("navigation_sim.log", mode="w")

import copy

import shapes
from flatland import FlatLand
from chassis_shape import ChassisShape
from virtual_vehicle import VirtualVehicle
import geom_utils as geom
from geom_utils import Point

# Compose the simulated environment
# The room
room_sides = [('start', (0, 0)), ('right', 380), ('up', 30), ('left', 50),
              ('up', 40), ('left', 20), ('up', 300), ('right', 20), ('up', 30),
              ('skip', 'yes'), ('up', 80), ('skip', 'off'), ('up', 50),
              ('left', 40), ('skip', 'on'),('left', 80), ('skip', 'off'),
              ('left', 210), ('down', 430) ]
room = shapes.SeqPolygon(room_sides)
room.traslate(0, -50)
logger.info("Room points= {}".format(room.size()))

#  Some boxes
pillar = shapes.Square(50)
pillar.traslate(100, 100)

# The chair composition
def chair_constructor(side, leg_side, name):
    """Footprint of a four legged classic chair"""
    leg1 = shapes.Circle(leg_side)
    leg1.color("r")
    leg2 = shapes.Circle(leg_side)
    leg2.traslate(side, 0)
    leg2.color("r")
    leg3 = shapes.Circle(leg_side)
    leg3.traslate(side, side)
    leg3.color("k")
    leg4 = shapes.Circle(leg_side)
    leg4.traslate(0,side)
    leg4.color("r")

    legs = [leg1, leg2, leg3, leg4]
    chair = shapes.CompoundShape(legs, name)
    return chair

# Create and pose the chair into the room
chair1 = chair_constructor(40, 2.5, "chair1")
chair1.traslate(200, 300)

chair2 = chair_constructor(40, 2.5, "chair2")
chair2.rotate(30)
chair2.traslate(250, 50)

# A table
def table_constructor(side1, side2, leg_side, name):
    """Footprint of a table"""
    leg1 = shapes.Square(leg_side)
    leg1.color("r")
    leg2 = shapes.Square(leg_side)
    leg2.traslate(side1, 0)
    leg2.color("r")
    leg3 = shapes.Square(leg_side)
    leg3.traslate(side1, side2)
    leg3.color("k")
    leg4 = shapes.Square(leg_side)
    leg4.traslate(0, side2)
    leg4.color("r")

    legs = [leg1, leg2, leg3, leg4]
    table = shapes.CompoundShape(legs, name)
    return table


def simulator():
    """Simulate vehicle movement with sensor readings and displays all on a map"""

    table = table_constructor(70, 120, 6, "table")
    table.traslate(50,250)

    # Compose flatland environment with all objects in it
    sim_env = FlatLand("Vehicle indoor navigation")
    sim_env.add_objects(room, pillar, chair1, chair2, table)
    logger.info("Bench points= {}".format(sim_env.size()))

    sim_env.show(live=True)
    #time.sleep(1)

    # Vehicle sizes (all dimensione in cm)
    length = 8
    width = 15
    color = "k"

    # Create a vehicle and mount on it one sensor
    twv = VirtualVehicle("SBOT", ChassisShape(length, width))
    print(twv)

    # Create a sensor and put it in the middle of the front side of the vehicle
    twv.mount_sensor(name="S_Front", beam=40, range=60, accuracy=2,
                      mnt_pt=Point(length/4, 0), mnt_orient=0)

    # Put it into the room
    twv.plot()
    twv.show()
    twv.trace(False)

    # Load the environment
    twv.load_env(sim_env)

    # Prepare a list of movements
    actions = [
                ("mv", 50), ("trn", 90), ("scan", 1),
                ("mv", 30), ("scan", 1),
                ("mv", 30), ("scan", 1),
                ("mv", 50), ("scan", 1),
                ("mv", 50), ("scan", 1),
                ("trn", -45), ("scan", 1),
                ("mv", 40), ("scan", 1),
                ("trn", 45), ("scan", 1),
                ("mv", 10), ("scan", 1),
                ("trn", 90), ("scan", 1),
                ("trn", -180), ("scan", 1),
                ("trn", 90), ("mv", 10), ("trn", 90), ("scan", 1),
                ("trn", -180), ("scan", 1),
                ("trn", 90), ("mv", 10), ("trn", 120), ("scan", 1),
                ("trn", -180), ("mv", 20),
                ]
    for action in actions:
        act, val = action
        if act == "mv":
            twv.move(val)
        elif act == "trn":
            twv.turn(val)
        elif act == "scan":
            scan_data = twv.scan("all", angle_step=val)
            map_data = twv.scan_to_map(scan_data)
            # Plot scan of each sensor
            for sensor_id in map_data:
                #logger.debug("Map data {}: {}".format(sensor_id, map_data[sensor_id]))
                geom.plot(map_data[sensor_id])
        else:
            print("Unknown move {}".format(act))

        # Trace the last position on the vehicle
        twv.plot_path()
        #twv.light_plot()

        # Show overall picture
        sim_env.show(True)

    twv.light_plot()
    sim_env.show()
    return


if __name__ == "__main__":
    simulator()
