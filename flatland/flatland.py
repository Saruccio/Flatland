# File: flatland.py
# Date: 21-09-2019
# Author: Saruccio Culmone
#
"""
Description
A FlatLand is an ensamble of compond objects, shapes and one or more
sensors that can be used to measure the distance among objects.
Sensors can be moved and rotated into the land acquiring _dynamic_ range
measures that can be used to compose a map or to test a navigation algorithm
"""

from trace import logger
logger.debug("FlatLand")

import geom_utils as geom


class FlatLand():
    """
    A FlatLand is an ensamble of CompoundShape objects, Shapes and
    one or more Sensors that che cam be used to measure the distancea
    among objects.
    All objects are referred to the same _global_ coordinate system: the one
    of the virtulal plane.
    """
    def __init__(self, name: str = ""):
        self.name = name
        self.venv = []  # The virtual environment is a list of compounds
        self.sensors = dict() # Sensor dictionary

    def add_objects(self, *objects):
        """
        Append a shape or a compound to the object list
        """
        for obj in objects:
            self.venv.append(obj)

    def add_sensors(self, *sensors):
        """
        Append a sensor to the sensor list
        """
        for sensor in sensors:
            if sensor.name in self.sensors:
                logger.warning("the sensor '{}' will be replaced".format(sensor.name))
            self.sensors[sensor.name] = sensor

    def plot(self):
        """
        Plot the actual flatland configuration
        """
        # Plot objects
        for obj in self.venv:
            obj.plot()

        # Plot sensors
        for sensor in self.sensors:
            self.sensors[sensor].plot()

    def show(self, live: bool=False):
        """
        Shows the current plot.
        This function must be the last function called in the program flow.
        """
        geom.live_plot(live)
        self.plot()
        geom.show(self.name)

    def size(self):
        """Returns the overall number of points of the environment"""
        num_points = 0
        for obj in self.venv:
            num_points += obj.size()
        return num_points
