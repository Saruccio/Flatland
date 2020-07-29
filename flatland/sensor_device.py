# File: sensor_device.py
# Date: 28-07-2020
# Author: Saruccio Culmone

"""
The SensorDevice class takes into account that in a physical world, the
The sensor is positioned on one reference system that moves over another.

In the simplest case, the sensor reference system moves with respect to the one
on which it is mounted.

In more complicated cases, the reference system of the sensor moves with respect
to another reference system which in turn moves with respect of another one
and so on.

Therefore, SensorDevice aims to take into account the movements of stacked
reference systems and places the sensor on the correct absolute
position in the global reference system in order to perform a right simulated
measurement.

The SensorDevice class so extends the Sensor classadding to it physical
information.

Note
----
Angular attributes are always expressed in radian units
Method parameters are always expressed in degrees
"""

# Imports
import numpy as np
from collections import namedtuple

# Project imports
from sensor import Sensor

# Point type
Point = namedtuple("Point", ["x", "y"])

class SensorDevice(Sensor):
    """
    Stores all data related to the sensor mounting on the chassis and the
    sensor itself.

    Angular data unit is radiant for all internal calculation even if,
    when passed as input, degrees are used.
    """
    def __init__(self, name: str, beam: float, range: float, mnt_pt: Point, mnt_orient: float):
        """
        Create a Sensor with chassis positioning information.

        Parameters
        ----------
        name : str
            Mandatory name it should be unique
        beam: float
            sensor beam width in degrees
        range: float
            maximum measurable distance
        mnt_pt : Point
            coordinates of the mount point in the chassis reference system
        mnt_orient : float
            anglular orientation of the sensor with respect to the chassis
            expressed in degrees.
        """

        # Init base class
        super().__init__(name, beam, range)

        # Sensor mount point and orientation relative to vehicle coordinate
        # system
        self.mnt_pt = mnt_pt
        self.mnt_orient = np.deg2rad(mnt_orient)


    def update_orientation(self, rot_angle):
        """
        Update the docked sensor position and orientation.

        When the chassis rotates around its center sensor mounted on it
        rotates around chassis's center.
        This method places the sensor at the new global position.
        """

        rotation_angle = np.deg2rad(rot_angle)

        # Update absolute sensor orientation according with it the
        # orientation of the chassis
        dev_orient = self.mnt_orient + rotation_angle

        # Calculate the rotation of the mount points
        # New position related to the chassis
        new_x, new_y = geom.rotate([self.mnt_pt], rotation_angle, rad=True)[0]

        # New absolute position
        newdev_x = chassis_pos.x + new_x
        newdev_y = chassis_pos.y + new_y

        self.place((newdev_x, newdev_y), dev_orient)

