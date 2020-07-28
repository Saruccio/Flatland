# File: sensor.py
# Date: 21-09-2019
# Author: Saruccio Culmone

"""
This module contains the base class definition for a generic Time of Flight
(ToF) sensor.

This sensor returns the distance measured from his actual position and nearest
point in its range of vision.

"""

# General imports
from trace import logger
import csv
import os
import numpy as np
import geom_utils as geom
import shapes

# Sensor shape (Arrow) parameters
ARROW_BASE = 2
ARROW_HEIGHT = 3

# The middle of the arrow base shall be at the origin, so an x axis
# traslation is needed before any rotation
ARROW_BASE_X_TRASLATION = -ARROW_BASE/2

# Default orientation is toward x axis (0 deg)
ARROW_ORIENTATION = -90 # deg


class Sensor():
    """
    Sensor base class.
    At creation time position into the plane and its rotation must be
    supplied.
    """


    def __init__(self, beam: float, range: float, name: str = "Sensor"):
        """
        Parameters
        name : Mandatory name it must be unique
        position: tuple (x, y)
        alpha: float, angle rotation in degrees
        beam: sensor beam in degrees
        range: maximum measurable distance

        Into the class, angles are stored always in radiant
        """
        # Set sensor properties
        self.name = name
        self.color = "g"
        self.position = (0, 0)
        self.orientation = 0  # radiant

        # Now create the sensor shape at default position
        self.shape = self.sensor_shape()
        self.shape.color(self.color)

        # Sensor physical ratings
        self.beam = np.deg2rad(beam)
        self.range = range

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
        self.measured_point = ()
        self.detected_point = ()

    def sensor_shape(self):
        """
        Returns an instance of the default sensor shape, an arrow in this case.
        Default parameters are global in order to simplify adjustements of
        default sensor aspect.

        Override this method to create new shape
        """
        # Create the arrow
        arrow = shapes.ArrowBase(ARROW_BASE, ARROW_HEIGHT)
        arrow.traslate(ARROW_BASE_X_TRASLATION, 0)
        arrow.rotate(ARROW_ORIENTATION)

        # Save current Shape as default
        arrow.save()
        return arrow

    def set_color(self, color: str = "g"):
        """
        Allows to change the default color sensor
        """
        self.color = color

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

    def traslate(self, position: tuple, spov: bool = True):
        """
        Traslate the sensor at point (x, y) passed as parameter and
        move the sensor shape according with it
        The new position is saved
        """
        # Get the actual position
        sxpos, sypos = self.position

        # Save the final position
        self.position = position

        # Calculate the delta movement
        xpos, ypos = position

        # Deltapos
        dxpos = xpos - sxpos
        dypos = ypos - sypos

        # Move sensor's shape
        self.shape.traslate(dxpos, dypos)

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
        # Save new desired orientation
        if rad is False:
            self.orientation = np.deg2rad(alpha)
        else:
            self.orientation = alpha

        # Rotate sensor's shape
        self.shape.reset()
        self.shape.rotate(alpha, rad)
        xp, yp = self.position
        self.shape.traslate(xp, yp)
        self.traslate(self.position)

        # As sensor has rotated, recostruct its point of view
        # TODO - Rotation is particular movement, optimization is possible
        if spov is True:
            self._sensor_point_of_view()

    def place(self, position: tuple, angle: float, rad: bool = False):
        """Place the sensor at given position and orientation

        Rotate the sensor first and traslate after
        """
        # Now move the sensor shape accordingly
        self.rotate(angle, rad, spov=False)
        self.traslate(position)

    def plot(self):
        """
        Add sensor shape to the global plot and annotate its name.

        The position for the label is tailored on the Arrow shape.
        If you change the sensor's shape, probably you will have to override
        this method to calculate a new good position for the label.
        """
        self.shape.plot()
        xs, ys = self.position
        xl = xs + np.amax([ARROW_BASE, ARROW_HEIGHT])
        geom.annotate_point((xl, ys), self.name)

    def plot_surroundings(self):
        """
        Plot the edges of the area surrounding the sensor
        """
        geom.plot_segment((self.xwest, self.ysouth), (self.xeast, self.ysouth))
        geom.plot_segment((self.xeast, self.ysouth), (self.xeast, self.ynorth))
        geom.plot_segment((self.xeast, self.ynorth), (self.xwest, self.ynorth))
        geom.plot_segment((self.xwest, self.ynorth), (self.xwest, self.ysouth))
        geom.plot(self.surroundings, pen_color="y")

    def show(self):
        """
        Debugging function that shows the plot at the current state of
        its composition.
        This function will affect the overall plot
        """
        self.plot()
        self.shape.show()

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
        self.measured_point = (measure, at_angle)
        return self.measured_point


    def scan(self, angle_from: float, angle_to: float, step: float = 1.0) -> list:
        """
        Simulate mulitple sensor readings in an angle range.

        Scanner function run sensor 'read' method getting a sequence of
        reagings at different angles.
        Angles from and to are related to the current orientation of the sensor,
        that is are related to its reference system.

        To make the scan, angle are calculeted as follow:
        - Start angle is sensor.orientation + angle_from
        - End angle is sensor.orientation + angle_to
        Minimum step is 1 deg.
        Mimimum angle_from is -180 deg
        Maximum angle_to is +180 deg
        Constraint is that angle_from < angle_to

        Angles are all in degreees.
        At the end of the scanning angle, the original sensor position is restored.

        Parameters
        ----------
        angle_from : float
        angle_to : float
        step : float
            defaults to 1 deg.

        Return
        ------
        A list of measured points as returned by 'read()' method
        """

        # Save current sensor orientation
        sensor_orientation = self.orientation

        # Set scan step
        scan_step = 1.0
        if step < 1.0:
            logger.warning("Actual step is less than 1 deg: forced to 1 deg.")
            scan_step = 1.0
        else:
            scan_step = step

        # Scan_angles
        scan_angles = np.arange(angle_from, angle_to, scan_step)

        # Run scanning
        measures = []
        for angle in scan_angles:
            meas = self.read(angle)
            if meas is not ():
                measures.append(meas)

        # Now restore sensor orientation
        self.orientation = sensor_orientation

        return measures


    def load_measures(self, fname: str):
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
        xo, yo = self.position
        alpha = self.orientation # radiant
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


# TEST -------------------------------------------------------------
def main():
    """
    Main function for test purposes only
    """
    # Base Sensor Shape
    # Pos = 0, 0
    # Rot = 0 deg
    sensor = Sensor(range=70, beam=30, name="Sensor1")
    sensor.traslate((100, 200))
    sensor.show()


if __name__ == "__main__":
    main()
