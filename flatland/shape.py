# File: shapes.py
# Date: 08-09-2019
# Author: Saruccio Culmone
#
# Description
# This file contains all definitions of classes corresponding to geometric
# shapes as rectangle, square, circle that will be used to compose the
# virtual environment.
#
"""
In the environment a geometric shape is represented by the list of its points.

A point is represented by a tuple of float.
The meaning of a tuple point depends on the coordinate system referenced:
(x, y) in rectangular coordinats
(r, theta) in polar coordinates

At creation time, each point of a geometric shape is a tuple of float
numbers in rectangular coordinates and represents the shape in its
coordinate system.
The list of all points of a shape will remain untouched during all the
life of the geometric shape.

To position a geometric  shape into the virtual space, all the points
of a shape will be trasated/rotated with respect with the outer
coordinate system shared among all different shapes that popuplate the
same space.
"""

# General imports
from trace import logger
import numpy as np
import geom_utils as geom


# Abstract Shape class
class Shape():
    """
    Base class for all other specific shapes.
    This class supplies all methods needed for shape manipulation and
    composition.
    Derived classes (basically) need only to overload __init__ method
    because each specific shape has its own algorithm to generate shape's
    points.
    """

    def __init__(self, res: float = 0.1):
        """
        Init the structures of the base Shape and its override composes
        the list points of the particular shape
        """
        # List of points composing the shape into its coordinate system
        # This list will be filled by points at creation time
        self.shape_points = []

        # List of shape's points after geometrig traslation and/or rotation
        # This list must be used to graph the geometric shape positioned in
        # the outer coordinate system
        self.points = []

        # Resolution for Shapes points
        self.res = np.abs(res)

        # Traslation/rotation parameters with respect with the external
        # coordinate system in which the shape will be positioned
        self.pos = (0.0, 0.0)  # (x, y) rect
        self.angle = 0 # radiants

        # Color and trait of the pen default values
        self.pen_trait = "."
        self.pen_color = "b"

    def color(self, pen_color: str = "b"):
        """
        Set the shape's color for future show
        """
        self.pen_color = pen_color

    def trait(self, pen_trait="."):
        """
        Set the shape's trait for future show
        """
        self.pen_trait = pen_trait

    def save(self):
        """
        Saves the current shape as default, so at .reset() will be restored
        """
        self.shape_points = self.points.copy()

    def reset(self):
        """Cancel every previous repositioning of the geometric shape.

        The current position becomes the same of the shape in its own
        coordinate system
        """
        self.points = self.shape_points.copy()

    def _set_rotation_angle(self, angle: float, rad: bool = True):
        """Helper method to convert and save rotation angle of the Shape
        """
        if rad is False:
            self.angle = np.deg2rad(angle)
        else:
            self.angle = angle

    def rotate(self, angle: float, rad: bool = False):
        """Rotate all Shapes's points"""
        self._set_rotation_angle(angle, rad)
        self.points = geom.rotate(self.points, angle, rad)

    def traslate(self, x: float, y: float):
        """Traslate Shape's points"""
        self.points = geom.traslate(self.points, x, y)

    def move(self, x: float, y: float, angle: float = 0, rad: bool = False):
        """Rotate first and traslate after the Shape"""
        self._set_rotation_angle(angle, rad)
        moved_points = geom.rotate(self.points, self.angle, rad)
        self.pos = (x, y)
        self.points = geom.traslate(moved_points, x, y)

    def get_points(self, shape_points: bool = False):
        """Returns the actual shape of the geometric figure.
        If flag shape_points is True the original shape's points are returned
        """
        if shape_points is True:
            return self.shape_points

        return self.points

    def size(self):
        """
        Returns the numeber of points composing the shape.

        It serves to give an idea of the number of calculations to be made
        """
        return len(self.points)

    def plot(self, shape_points: bool = False):
        """
        Plots but does not show shape's points
        """
        if shape_points is True:
            show_points = self.shape_points
        else:
            show_points = self.points

        geom.plot(show_points, self.pen_trait, self.pen_color)


    def show(self, shape_points: bool = False):
        """Draw the Shape into its own coordinate system for debugging
        purposes
        Uses mathplotlib.pyplot module capabilities
        """
        self.plot(shape_points)
        obj_name = self.__class__.__name__
        geom.show(obj_name, obj_name)
