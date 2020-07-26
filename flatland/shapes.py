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
This file contains all definitions of classes corresponding to geometric
shapes as rectangle, square, circle that will be used to compose the
virtual environment.
"""

# General imports
from trace import logger
import numpy as np
import geom_utils as geom
from shape import Shape

class Rectangle(Shape):
    """
    Rectangular shape class
    """
    def  __init__(self, base: float, height: float, res: float = 0.1):
        """
        Create a rectangle.
        Resolution in points calculation defaults at 0.1 units
        """
        super().__init__(res)
        self.base = base
        self.height = height

        # Build all points of the geometric figure
        # Add the four vertex
        self.shape_points.append((0.0, 0.0))
        self.shape_points.append((0.0, height))
        self.shape_points.append((base, height))
        self.shape_points.append((base, 0.0))

        # Horizontal sides
        for x in np.arange(0.0, base, self.res):
            self.shape_points.append((x, 0.0))
            self.shape_points.append((x, height))

        # Vertical sides
        for y in np.arange(0.0, height, self.res):
            self.shape_points.append((0.0, y))
            self.shape_points.append((base, y))

        # Call reset in order to populate actual point list for
        # calculation and display
        self.reset()


class Square(Rectangle):
    """
    Square is a simplified rectagle
    """
    def __init__(self, side: float, res: float = 0.1):
        super().__init__(side, side, res)


class Circle(Shape):
    """
    Create a circle.
    The res parameter is converted into a angle_res variable before points
    calculation
    """
    def __init__(self, radius: float, res: float = 0.1):
        super().__init__(res)
        self.angle_res = res / radius  # In radiants
        self.radius = radius
        self.center = (0.0, 0.0)

        # Save center as the first point of the shape point list
        self.shape_points.append(self.center)

        # Calculate circle points
        for alpha in np.arange(0.0, np.pi*2, self.angle_res):
            x = radius * np.cos(alpha)
            y = radius * np.sin(alpha)
            self.shape_points.append((x, y))

        # Call reset in order to populate actual point list for
        # calculation and display
        self.reset()


class ArrowBase(Shape):
    """
    The Arrow basic shape is an isosceles triangle without its base.
    Construction of the arrow is made exploiting its symmetry.
    Ony the left semi-triangle is calculated; the right side is symmetric
    with respect to its height

    Angle reference, as for a triangle is the angle of the base with
    the x axis
    """
    def __init__(self, base: float, height: float, res: float = 0.1):
        super().__init__(res)

        # Triangle's vertex
        self.A = (0.0, 0.0)
        self.B = (base, 0.0)
        semi_base = base/2
        self.C = (semi_base, height)
        self.H = (semi_base, 0.0)

        # Save vertex into the point list
        self.shape_points.append(self.A)
        self.shape_points.append(self.B)
        self.shape_points.append(self.C)
        self.shape_points.append(self.H)

        # Calculate side points
        # Move on polar coordinates, this ensure corect spacing
        side, alpha = geom.cart2pol(semi_base, height)
        side_points = []
        for r in np.arange(0.0, side, self.res):
            side_points.append((r, alpha))

        # Now return in rctangular coordinates
        rside_points = geom.to_rect(side_points)

        self.shape_points += rside_points

        # Add right side by symmetry
        right_side = []
        for p in self.shape_points:
            x, y = p
            d = semi_base - x
            x_right_side = semi_base + d
            right_side.append((x_right_side, y))

        self.shape_points += right_side

        # Call reset in order to populate actual point list for
        # calculation and display
        self.reset()


class IsoscelesTriangle(ArrowBase):
    """
    Isosceles triangle is an Arrow with the base drawn
    """
    def __init__(self, base: float, height: float, res: float = 0.1):
        super().__init__(base, height, res)

        # Add the points of th base
        base_points = []
        for x in np.arange(0.0, base, self.res):
            base_points.append((x, 0.0))

        self.shape_points += base_points

        # Call reset in order to populate actual point list for
        # calculation and display
        self.reset()


class SeqPolygon(Shape):
    """A Seq(uenced)Polygon is a plolygon composed only by segments that
    can be orizontal or vertical positioned.
    Its construction is a sequece of command (start, up, down, left, right,
     skip) and
    the length of the segment starting at the end point of the previous
    segment specified.
    The 'start' command set the first point from which to move.

    Each commend is a tuple (cmd, parameter) and the parameter type
    depends on the command

    For example, to draw a square without the base side, the list of
    command will be:

    [('start', (10,0)), ('up', 10), ('left', 10), ('down', 10)]

    The flag skip allows to move the refernce points to the end of the
    segment but without storing the segment points.
    This shape is useful to trace the borders of common environments like rooms
    """
    def __init__(self, cmd_list: list, res: float = 0.1):
        super().__init__(res)
        self.ref_point = (0.0, 0.0)  # At start is the origin
        self.skip = False # Skip flag false by default

        for cmd_t in cmd_list:
            self._cmd_parser(cmd_t)

        # Call reset in order to populate actual point list for
        # calculation and display
        self.reset()

    def _cmd_parser(self, cmd_t: tuple):
        command, param = cmd_t

        cmd = command.lower()
        if cmd == 'start':
            self._start(param)
        elif (cmd == 'up') or (cmd == 'down'):
            self._up_or_down(param, cmd)
        elif (cmd == 'left') or (cmd == 'right'):
            self._left_or_right(param, cmd)
        elif cmd == 'skip':
            self._skip(param)
        else:
            # Unknown command, issue a warning message and continue
            warn_msg = "Command '{}' unknown, no points will be added".format(cmd)
            logger.warning(warn_msg)

    def _start(self, point: tuple):
        """Saves the start position for next side tracing"""
        self.ref_point = point

    def _up_or_down(self, length: float, direction: str):
        """Calculates and stores points upward from start point"""
        x0, y0 = self.ref_point

        # End point calculation
        x1 = x0
        direct = direction.lower()
        if direct == 'up':
            y1 = y0 + length
        else:
            y1 = y0 - length

        if self.skip is False:
            # Set set direction
            if y1 >= y0:
                step = self.res
            else:
                step = -self.res

            for y in np.arange(y0, y1, step):
                self.shape_points.append((x1, y))

        # Save end point used as start for next side
        self.ref_point = (x1, y1)

    def _left_or_right(self, length, direction):
        """Calculates and stores points upward from start point"""
        x0, y0 = self.ref_point

        # End point calculation
        y1 = y0
        direct = direction.lower()
        if direct == 'right':
            x1 = x0 + length
        else:
            x1 = x0 - length

        if self.skip is False:
            # Set set direction
            if x1 >= x0:
                step = self.res
            else:
                step = -self.res

            for x in np.arange(x0, x1, step):
                self.shape_points.append((x, y1))

        # Save end point used as start for next side
        self.ref_point = (x1, y1)


    def _skip(self, param: str):
        """Set the flag 'skip' to True or False depending on the
        parameter string.
        The parsing is case insensitive.

        Allowed strings are:
        'yes', 'true', 'on' -> set .skip as True
        'no', 'false', 'off' -> set .skip as False

        When set to True, no points are added to the shape and only end
        point is stored.
        """
        flag = param.lower()

        if (flag == 'true') or (flag == 'yes') or (flag == 'on'):
            self.skip = True
        elif (flag == 'false') or (flag == 'no') or (flag == 'off'):
            self.skip = False
        else:
            # Unknown flag issue a warning message and continue
            warn_msg = "Flag '{}' unknown, no points will be added".format(flag)
            logger.warning(warn_msg)


class CompoundShape(Shape):
    """Container of Shapes

    If a list of Shapes is supplied at creation time, it will be used
    to compose the compound object.
    """

    def __init__(self, shapes: list, name: str = ""):
        """Get points fron each single Shape in list"""
        super().__init__()
        for shape in shapes:
            self.shape_points += shape.get_points()
        self.points = self.shape_points.copy()

# Test section --------------------------------------------------------------
def test1():
    """
    Basic shapes
    """
    # Box Test
    logger.info("Rectangle")
    box = Rectangle(10, 5)
    box.show(shape_points=True)
    box.show()
    box.rotate(-45)
    box.traslate(1, 2)
    box.color("r")
    box.show()

    # Circle test
    logger.info("Circle")
    circ = Circle(7)
    circ.show(shape_points=True)
    circ.traslate(1, 2)
    circ.show()

    # Square test
    logger.info("Square")
    sq = Square(3)
    sq.show(shape_points=True)
    sq.move(1, 2, 45)
    sq.show()

    # Arrow Base test
    logger.info("ArrowBase")
    ar = ArrowBase(5, 15)
    ar.show(shape_points=True)
    ar.move(-2.5, 0, 75)
    ar.color("r")
    ar.show()

    # Triangle Test
    logger.info("IsoscelesTriangle")
    tri = IsoscelesTriangle(12, 3)
    tri.move(5, 5, 25)
    tri.show()

def test2():
    """Polygon test"""

    logger.info("Polygon test")
    # Polygon
    poly_sides = [('start', (10, 0)), ('up', 10), ('left', 10), ('down', 10)]
    #poly_sides = [('start', (10,0)), ('ZOT', 10), ('left', 10), ('down', 10)]
    poly = SeqPolygon(poly_sides)
    poly.show(shape_points=True)
    poly.rotate(-30)
    poly.show()

def test3():
    """Test more complex sequence polygon"""

    logger.info("Sequence polygon test")
    room_sides = [('start', (0, 0)), ('right', 380), ('up', 30), ('left', 50), ('up', 40), ('left', 20), ('up', 300), ('right', 20), ('up', 30), ('skip', 'yes'), ('up', 80), ('skip', 'off'), ('up', 50), ('left', 40), ('skip', 'on'),('left', 80), ('skip', 'off'), ('left', 210), ('down', 430) ]
    room = SeqPolygon(room_sides)
    logger.info("Num points= {}".format(room.size()))
    room.show()
    room.traslate(0, -50)
    room.show()

# Compound shape test
def chair_constructor():
    """Footprint of a four legged classic chair"""
    leg_side = 5 # cm
    leg1 = Square(leg_side)
    leg1.color("r")
    leg2 = Square(leg_side)
    leg2.traslate(30, 0)
    leg2.color("r")
    leg3 = Square(leg_side)
    leg3.traslate(30, 40)
    leg3.color("k")
    leg4 = Square(leg_side)
    leg4.traslate(0, 40)
    leg4.color("r")

    legs = [leg1, leg2, leg3, leg4]
    chair = CompoundShape(legs, "chair")
    return chair


def test4():
    """
    Main function for test purposes only
    """
    chair = chair_constructor()
    chair.rotate(45)
    chair.move(10, 10, 15)
    chair.show()

def main_test():
    """
    Main function, for tests purposes only
    """
    test1()
    test2()
    test3()
    test4()

if __name__ == "__main__":
    main_test()
