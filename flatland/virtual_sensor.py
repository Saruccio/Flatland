# File: sensor_device.py
# Date: 28-07-2020
# Author: Saruccio Culmone

"""
The VirtualDevice class takes into account that in a physical world, the
The sensor is positioned on one reference system that moves over another.

In the simplest case, the sensor reference system moves with respect to the one
on which it is mounted.

In more complicated cases, the reference system of the sensor moves with respect
to another reference system which in turn moves with respect of another one
and so on.

Therefore, VirtualDevice aims to take into account the movements of stacked
reference systems and places the sensor on the correct absolute
position in the global reference system in order to perform a right simulated
measurement.

The VirtualDevice class so extends the Sensor classadding to it physical
information.

Note
----
Angular attributes are always expressed in radian units
Method parameters are always expressed in degrees
"""

# Imports
import os
import sys
import csv

import numpy as np
from collections import namedtuple

# Project imports
import geom_utils as geom
from sensor import Sensor

# Point type
Point = namedtuple("Point", ["x", "y"])

class VirtualSensor(Sensor):
    """
    Stores all data related to the sensor mounting on the chassis and the
    sensor itself.

    Angular data unit is radiant for all internal calculation even if,
    when passed as input, degrees are used.
    """
    def __init__(self, name: str, beam: float, range: float, accuracy: float, mnt_pt: Point, mnt_orient: float):
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
        super().__init__(name, beam, range, accuracy)

        # List of points in the range of the sensor.
        # The local points of the sensor can be calculated using only
        # these boints because the other cannot be detected by the sensor.
        # Using these points only allows a speed improvement
        self.surroundings = []

        # Surrounding boundaries
        self.xwest = 0.0
        self.xeast = 0.0
        self.ynorth = 0.0
        self.ysouth = 0.0

        # List of environment points; this way the list of a static
        # environment can be calculate only once and shared with all other
        # sensors of the same type in the same environment until it changes
        self.env_points = []

        # This list represents the environment in the point of view of
        # the sensor, in the sense that it is facing its own axis (x axis)
        # This list of points chages at each time the sensor moves on at
        # diffrent position.
        # Each instance of a sensor have its own point of view
        self.local_polar_points = []

        # For debugging purposes, store the measured point and real point
        # of the last read.
        # Point are in polar coordinate with anglein deg
        self.detected_point = ()

        # Sensor mount point and orientation relative to vehicle coordinate
        # system
        self.mnt_pt = mnt_pt
        self.mnt_orient = np.deg2rad(mnt_orient)


    def __str__(self):
        """Add to Sensor parameters SensorDevice mounting data"""
        str_pos = geom.str_point(self.mnt_pt)
        return "Dev [{}] {}, {:.1f}°".format(super().__str__(), str_pos, np.rad2deg(self.mnt_orient))


    def load_env(self, venv: list):
        """
        Load virtual space environment as a list of compound objetcs
        and shapes.
        This ensable of points will be used for all readings.

        Pay attention
        Every time this method is called previous loaded points are lost.
        The reason for this behaviour is because you can update the
        environment when it changes.

        At the end of loading the 'point of view' of the sensor will
        be rebuilt
        """
        # Load evnvironment points
        if self.env_points == []:
            for obj in venv:
                self.env_points += obj.get_points()

        # Build sensor point of view at its actual position and orientation
        self._sensor_point_of_view()

        return len(self.env_points)


    def _surroundings(self):
        """
        This function filter the list of points environment reaining
        only those that are in a square areadefining the sensor
        surroundings.

        Surroundings must be recalculated at each traslation of the sensor,
        not at rotation
        """
        # Starting from the position of the sensor, calculate surroundings
        # boundaries
        xpos, ypos = self.position
        self.xwest = xpos - self.range
        self.xeast = xpos + self.range
        self.ynorth = ypos + self.range
        self.ysouth = ypos - self.range

        self.surroundings = []
        for xp, yp in self.env_points:
            if ((xp >= self.xwest) and (xp <= self.xeast)) and \
               ((yp <= self.ynorth) and (yp >= self.ysouth)):
                self.surroundings.append((xp, yp))
        return len(self.surroundings)


    def _sensor_point_of_view(self):
        """
        This method builds the sensor point of view when a movement
        (rotation and/or traslation) occurs.
        This processing is expensive in terms of computation time and
        must be performed using only surroundings points.
        """
        # Before to calculate the point of view of the sensor
        # you must reduce the set of points calculating
        # the sensor surroundings
        self._surroundings()

        # Environment points are available; they refer to the GLOBAL
        # coordinate system
        # Move points ito the LOCAL coordinate system that depends on
        # the position of the sensor into the GLOBAL coord sys
        # Prepare local infos
        xo, yo = self.position

        # Note that the rotation of the local coordinate system (the one
        # of the sensor) is opposite to the sensor orientation
        alpha = -self.orientation  # radiant
        local_sys = (xo, yo, alpha, True)

        local_points = []
        for point in self.surroundings:
            # Calculate and save local point
            local_point = geom.globalpos_to_localpos(point, local_sys)
            local_points.append(local_point)

        # Transform to polar
        self.local_polar_points = geom.to_polar(local_points)

    def plot_surroundings(self):
        """
        Plot the edges of the area surrounding the sensor
        """
        geom.plot_segment((self.xwest, self.ysouth), (self.xeast, self.ysouth))
        geom.plot_segment((self.xeast, self.ysouth), (self.xeast, self.ynorth))
        geom.plot_segment((self.xeast, self.ynorth), (self.xwest, self.ynorth))
        geom.plot_segment((self.xwest, self.ynorth), (self.xwest, self.ysouth))
        geom.plot(self.surroundings, pen_color="y")


    def update_placement(self, chassis_pos: Point, chassis_rot: float):
        """
        Update position and orientation of the sensor in the global frame

        This operation is necessary every time the vehicle moves and/or rotate.
        In particular, when the chassis rotates around its center the mount
        point of each sensor mounted on it rotates around chassis's center.
        So at each chassis rotation we have to update not only the orientation
        but also the position of each sensor.

        This method places the sensor at the new global position needed by the
        sensor to produce simulated rangemeasurements.

        Parameters
        ----------
        chassis_pos : Point
            chassis position after a traslation or rotation movement
        chassis_rot: float
            chassis orientation in radian units after a traslation or
            rotation movement
        """

        # Update absolute sensor orientation according with it the
        # orientation of the chassis
        dev_orient = self.mnt_orient + chassis_rot

        # Calculate the new position of the mount point of the sensor as
        # effect of the chassis rotation
        new_mnt_x, new_mnt_y = geom.rotate([self.mnt_pt], chassis_rot, rad=True)[0]

        # New absolute position
        newdev_x = chassis_pos.x + new_mnt_x
        newdev_y = chassis_pos.y + new_mnt_y

        self.place(Point(newdev_x, newdev_y), dev_orient, True)


    def sys_ref(self):
        """
        Return the position and orientation of the sensor mounting the chassis
        reference system.

        Parameters
        ----------
        None

        Return
        ------
        (mount_point.x, mount_point.y, mount_orient, True)
            The last element is always True because the mount orientation
            is kept from value stored in the class in radian
        """

        return (self.mnt_pt.x, self.mnt_pt.y, self.mnt_orient, True)


    def read(self, at_angle: float = 0.0) -> (float, float):
        """
        Simulates a range reading of the sensor.

        Calculates the simulated reading as the distance between the sensor
        origin and the nearest object il the simulated environment loaded.

        Simplest algoritm:
        - get all points of all objects in the simulated enviroment
        - move these points in the coordinate system LOCAL to the sensor
        - transform all points into polar coordinates
        - filter all points in two steps:
          1. get all points with angle into the beam of the sensor
          2. get the point with the minimum of the module:
             ___this module is the reading of the sensor___

        Parameters
        ----------
        at_angle :
            float direction of the beam in degrees measured from the
            x axis (0 degrees) of the sensor. This parameter will be used
            in scan operation
            In single measurement defaults to zero

        Return
        ------
        the tuple (measure, at_angle_dir) in polar coordinate at
        the orientation angle.
        Angle is expressed in degrees
        """
        # Filter taking only points into the beam
        # TODO - Make this filtering sorting points by angle and using list comprehensions
        at_angle_dir = np.deg2rad(at_angle)
        into_beam_points = []
        for r, phi in self.local_polar_points:
            if (phi >= (at_angle_dir - self.beam/2)) and (phi <= (at_angle_dir + self.beam/2)):
                into_beam_points.append((r, phi))

        if into_beam_points == []:
            # If any, all points are too far for the sensor
            return (0.0, at_angle)

        # Get the point of minimum module
        detected_point = min(into_beam_points)
        self.detected_point = (detected_point[0], np.rad2deg(detected_point[1]))

        # Get the distance only, discarding the detected point angle
        measure, theta = self.detected_point

        # Control if the distance measured is in the range of the sensor
        if measure > self.range:
            measure = 0.0

        # Compose the measured point
        if self.rho_phi_type:
            self.measured_point = (measure, at_angle)
        else:
            self.measured_point = (at_angle, measure)
        return self.measured_point


    def traslate(self, position: tuple, spov: bool = True):
        """
        Traslate the sensor and updates the sensor point of view in order
        to make virtual readings
        """
        super().traslate(position, spov)

        # As the sensor has moved, reconstruct its point of view
        if spov is True:
            self._sensor_point_of_view()

    def rotate(self, alpha: float, rad: bool = False, spov: bool = True):
        """
        Rotate the sensor around _its_ origin that is around _its_ last
        position.
        So the rotation of the sensor shape it's a movement compoed
        by rotation and traslation.

        The new orientation is saved
        """
        super().rotate(alpha, rad, spov)

        # As sensor has rotated, recostruct its point of view
        # TODO - Rotation is particular movement, optimization is possible
        if spov is True:
            self._sensor_point_of_view()

# TEST -------------------------------------------------------------
def load_measures(sensor: VirtualSensor, fname: str):
    """
    Read a set of measures in polar coordinates from a .csv file
    and return a list of measure compatible with 'scan' method.

    Measures in the file must be related to the actual position and
    orientation of the sensor.
    """
    if os.path.exists(fname) is False:
        logger.warning("Measure file '{}' not found.".format(fname))
        return []

    # File exists, try to load its content

    # Setup parameters to pass to global reference system
    xo, yo = sensor.position
    alpha = sensor.orientation # radiant
    local_sys = (xo, yo, alpha, True)

    local_measures = []
    with open(fname, newline='') as csvfile:
        data_points = csv.reader(csvfile, delimiter=';')
        data_points.__next__()
        offset = np.pi/2.0
        for phi, r in data_points:
            # Polar meas
            rho = float(r)
            theta = float(phi) - offset

            # Transform point in rectangular coordinates
            rect_point = geom.pol2cart(rho, theta)

            # Return the point into the GLOBAL coordinate system
            meas_point = geom.localpos_to_globalpos(rect_point, local_sys)

            # Add to measures list
            local_measures.append(meas_point)

    return local_measures


def main():
    """
    Main function for test purposes only
    """
    # Sensor mounting point
    mount_point = Point(0, 0)
    mount_orientation = 45 # deg
    sensor = VirtualSensor(range=70, beam=30, name="Sensor1", accuracy=2,
                           mnt_pt=mount_point, mnt_orient=mount_orientation)
    sensor.traslate((100, 200))

    sensor.show()


if __name__ == "__main__":
    main()
