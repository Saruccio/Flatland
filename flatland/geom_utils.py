# File: geom_utils.py
# Date: 05-10-2019
# Author: Saruccio Culmone
#
# This module contains all function that perform geometric actions as
# traslation, rotation, etc.
#
"""
Module with utility function for manipulation points in various coordinate system and plot them.
"""

# General imports
from trace import logger
import numpy as np
import matplotlib.pyplot as plt


def cart2pol(x: float, y: float):
    """Coordinate conversion fron cartesian (rectangular)to polar"""
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return (rho, phi)

def pol2cart(rho: float, phi: float):
    """Coordinate conversion from polar to cartesian"""
    x = rho*np.cos(phi)
    y = rho*np.sin(phi)
    return (x, y)

def to_polar(points: list):
    """Convert all points (x, y) contained in a list from cartesian coordinates to polar ones"""
    polar_points = []
    for point in points:
        x, y = point
        polar_points.append(cart2pol(x, y))
    return polar_points

def to_rect(points):
    """Convert all tuple points (rho, phi) contained in a list from polar coordinates into cartesian ones"""
    cart_points = []
    for point in points:
        cart_points.append(pol2cart(*point))
    return cart_points

def rotate(points: list, angle: float, rad: bool = False):
    """Rotates point in alist

    Default angle unit is degree and wiil be converted to radiant
    before calculations

    Rotation algorithm is simple:
    - convert points in polar coordinates
    - add angle to the angle of each point
    - convert new points in rectangular coordinates

    Parameters
    ----------
    points : list
        list of tuples (x, y)
    angle : float
        rotation angle
    rad : bool
        flag indicating if angle is expressed in radiant.
        Defaults to False

    Return
    ------
    A list of tuples (x, y)
    """
    # Polar conversion of the actual (last modification) Shape
    polar_shape = to_polar(points)

    # Perform rotation
    if rad is False:
        alpha = np.deg2rad(angle)
    else:
        alpha = angle

    rotated_shape = []
    for rho, phi in polar_shape:
        rotated_shape.append((rho, phi+alpha))

    # Cartesian conversion
    return to_rect(rotated_shape)


def traslate(points: list, dx: float, dy: float):
    """Traslate each point of a list of dx and dy length.

    It's a differential traslation, not absoluta at point.
    The traslation action will be performed on the actual points of
    the Shape, that is on the last its transformation
    """
    # Perform traslation of the actual (last modification) Shape
    traslated_points = []
    for px, py in points:
        tx = px + dx
        ty = py + dy
        traslated_points.append((tx, ty))

    return traslated_points


def plot_segment(p1: tuple, p2: tuple, pen_color: str = "c"):
    """Draw a segment with adashed line between two points"""
    x1, y1 = p1
    x2, y2 = p2
    x = [x1, x2]
    y = [y1, y2]

    # Set color
    pen = pen_color + "--"
    plt.plot(x, y, pen)


def plot_point(p: tuple, pen_color: str = "b", pen_trait: str = "o"):
    """Draw a point with a big O"""
    x, y = p
    x = [x]
    y = [y]

    # Set color
    pen = pen_color + pen_trait
    plt.plot(x, y, pen)

def annotate_point(p: tuple, text: str):
    """Put a label at point"""
    plt.annotate(text, p)

def plot(points: list, pen_trait: str = ".", pen_color: str = "k"):
    """Plot but does not show a list of points in its coordinate system
    Uses mathplotlib.pyplot module capabilities
    """
    # Produce coordinate lists
    xv = []
    yv = []

    for p in points:
        x, y = p
        xv.append(x)
        yv.append(y)

    # Plot the current shape
    pen = pen_trait + pen_color
    plt.plot(xv, yv, pen, linewidth=.5, markersize=.5)

def live_plot(on: bool):
    if on:
        plt.ion()
    else:
        plt.ioff()

def show(title: str = "No title", label: str = ""):
    """Shows an already composed plot
    Uses mathplotlib.pyplot module capabilities
    """
    plt.title(title)
    xlabel = label + " x"
    plt.xlabel(xlabel)
    ylabel = label + " y"
    plt.ylabel(ylabel)
    #plt.grid()
    plt.axis('equal')
    plt.show()
    plt.pause(0.01)

def close():
    """
    Close current plot window
    """
    plt.close()


# Calculation of point coordinates in a new coordinate system


def globalpos_to_localpos(point: tuple, local_sys: tuple) -> tuple:
    """
    Calculates the new point's coordinates (xp, yp) in the local coordinate
    system which has position local_sys in the global coordinate system.

    The local_sys parameter is a tuple:

    (xo, yo, alpha, rad)

    where:
    xo, yo : are the coordinates of the origin of the local coordinate system
             in the global one
    alpha  : is the rotation of the local coordinate system with respect to
             the global one
    rad    : is a booles flag indicating if alpha angle is expressed in degrees
             or radiants.

    Note that the coordinates and rotation of the local coordinate system
    are always expressed with respect tothe global one
    """
    xp, yp = point
    xo, yo, alpha, rad = local_sys

    if rad is False:
        alpha_rad = np.deg2rad(alpha)
    else:
        alpha_rad = alpha

    xl = np.cos(alpha_rad)*(xp - xo) - np.sin(alpha_rad)*(yp - yo)
    yl = np.sin(alpha_rad)*(xp - xo) + np.cos(alpha_rad)*(yp - yo)

    return (xl, yl)


def localpos_to_globalpos(point: tuple, local_sys: tuple) -> tuple:
    """
    Calculates the new point's coordinates (xl, yl) in the local coordinate
    system of a point in the local coordinate system positioned at local_sys
    with respect to the global one.

    The local_sys parameter is a tuple:

    (xo, yo, alpha, rad)

    where:
    xo, yo : are the coordinates of the origin of the local coordinate system
             in the global one
    alpha  : is the rotation of the local coordinate system with respect to
             the global one
    rad    : is a booles flag indicating if alpha angle is expressed in degrees
             or radiants.

    Note that the coordinates and rotation of the local coordinate system
    are always expressed with respect to the global one
    """
    xl, yl = point
    xo, yo, alpha, rad = local_sys

    if rad is False:
        alpha_rad = np.deg2rad(alpha)
    else:
        alpha_rad = alpha

    xp = xo + xl*np.cos(alpha_rad) - yl*np.sin(alpha_rad)
    yp = yo + xl*np.sin(alpha_rad) + yl*np.cos(alpha_rad)

    return (xp, yp)

def tround(fpt: tuple):
    """
    Returns a pont tuple in which elements are 'rounded' applying round()
    function
    """
    fx, fy = fpt
    return (round(fx), round(fy))

