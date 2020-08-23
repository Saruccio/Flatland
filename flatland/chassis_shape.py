# File: chassis_shape.py
# Date: 23-08-2020
# Author: Saruccio Culmone
#
"""
Vehicle spatial information
"""

# Imports
from trace import logger
logger.add("vehicle.log", mode="w")

import shapes
import numpy as np

# Project imports
import geom_utils as geom

    
class ChassisShape(shapes.Rectangle):
    """
    Default ChassisShape is a modified Rectangle with a double line on the right
    side in order to mark the front side of the Vehicle.
    """
    
    def __init__(self, base: float, height: float, gap: float = 2, res: float = 0.1):
        """
        Initialize the base class and draw the second vertical line at
        right rectangle side.

        Parameters
        ----------
        base : float
            the base of the rectangle along the x axis
        height : float
            the height of the rectangle along the y axis
        gap : float
            the distance between the right side of the rectangle and the second 
            side drown internally to mark the front of the chassis
        res : float
            the distance among points in the sides of the rectangle.
            Defaults to 0.1 unit
        """
        
        # Init base class
        super().__init__(base, height, res)
        
        # Save rectangle's sides dimensions
        self.base = base
        self.height = height

        # Add second side
        xside = base - gap
        yords = np.arange(0.0, height, res)
        for y in yords:
            self.points.append((xside, y))

        # Traslate rectangle in order to be centered to the origin
        self.traslate(-base/2, -height/2)
        
        # Traslate in order to position the track axle
        self.traslate(-base/4, 0)
        self.save()   # Save actual point configuration as
        self.reset()
        
        # Calculate shape's x_min and x_max
        self.x_min = -base/2 -base/4
        self.x_max = base/4
        
        # Calculate shape's y_min and y_max 
        self.y_min = -height/2
        self.y_max = height/2
        
        # Calculate the radius of the circumference circumscribed to the vehicle
        shape_polar_pts = geom.to_polar(self.shape_points)
        rhos = [rho for rho, phi in shape_polar_pts]
        self.safe_radius = np.max(rhos)

    def safe_radius(self):
        """Return the radius of the circumference circumscribed to the vehicle"""
        return self.safe_radius


    def length_width(self):
        """Return orizontal maximum width and vertical length"""
        return self.base, self.height


    def x_min_max(self):
        """Return x_min and x_max of the chasiss shape"""
        return self.x_min, self.x_max


    def y_min_max(self):
        """Return y_min and y_max of the chasiss shape"""
        return self.y_min, self.y_max
