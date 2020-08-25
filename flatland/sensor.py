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

# Out of range value
OUT_OF_RANGE = 255 # length units


class Sensor():
    """
    Sensor base class.
    At creation time position into the plane and its rotation must be
    supplied.
    """

    def __init__(self, name: str, beam: float, range: float, accuracy: float, rho_phi_type: bool = True):
        """
        Set physical sensor parametrs

        Parameters
        ----------
        name : str
            Mandatory name it must be unique
            
        beam: float
            sensor beam width in degrees
            
        range: float
            maximum measurable distance
            
        rho_phi_type : bool
            if True, the 'read' method return a tuple of the format (rho, phi),
            otherwise a (phi, rho) tuple is returned
            
        Into the class, angles are stored always in radiant
        """
        # Set sensor properties
        self.name = name
        self.color = "g"

        # Sensor position and orientation in the global reference system
        self.position = (0, 0)
        self.orientation = 0  # radiant

        # Now create the sensor shape at default position
        self.shape = self.sensor_shape()
        self.shape.color(self.color)

        # Sensor physical ratings
        self.beam = np.deg2rad(beam)
        self.range = range
        self.out_of_range = OUT_OF_RANGE
        self.rho_phi_type = rho_phi_type

        # Last measured point
        self.measured_point = ()


    def __str__(self):
        """Format all relevant sensor parameter in a string"""
        str_pos = geom.str_point(self.position)
        return "'{}': {}, {:.1f}°".format(self.name, str_pos, np.rad2deg(self.orientation))

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


    def traslate(self, position: tuple, spov: bool = True):
        """
        Traslate the sensor at point (x, y) 
        
        Move the sensor shape according with its new position.
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
        """
        raise NotImplementedError()


    def ping(self, angle: float):
        """
        Wrapper of 'read' method to perform a sensor reading in a direction.
        
        Paramters
        ---------
            same of the read method
        
        Return
        ------
        According with the 'rho_phi_type' flag the reading is always returned
        in the rho, phi) format
        """
        if self.rho_phi_type:
            rho, phi = self.read(angle)
        else:
            phi, rho = self.read(angle)
        
        return (rho, phi)
        

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
            if self.rho_phi_type:
                rho, phi = self.read(angle)
            else:
                phi, rho = self.read(angle)
            
            measures.append((rho, phi))

        # Now restore sensor orientation
        self.orientation = sensor_orientation

        return measures



