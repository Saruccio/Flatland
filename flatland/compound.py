# File: compound.py
# Date: 21-09-2019
# Author: Saruccio Culmone
#
"""
A counpound object is a container of shapes managed as a whole.
The coordinate system, for all shapes, is the one of the compound
Each compound can be moved and rotated into its coordinate system
as a normal shape.
"""

from trace import logger
logger.info("Compound")

import geom_utils as geom
import shapes


# Compound Shape definition
class CompoundShape():
    """Container of Shapes

    If a list of Shapes is supplied at creation time, it will be used
    to compose the compound object
    """
    def __init__(self, shapes: list = [], name: str = ""):
        self.name = name
        self.shapes = shapes.copy()

        # Add shapes points
        self.points = []

    def build(self):
        """
        Build the list of points of the compound scannig the list of
        stored shapes
        """
        for shape in self.shapes:
            self.points += shape.get_points()


    def get_points(self):
        """Returns a list of all points of the compound"""
        if self.points == []:
            self.build()
        return self.points

    def plot(self):
        """
        Draws but does not show each shape of the compond object
        """
        for shape in self.shapes:
            shape.plot()

    def show(self):
        """Draw the compound object drawing each shape with its own color
        Uses mathplotlib.pyplot module capabilities
        """
        for shape in self.shapes:
            shape.plot()
        geom.show(self.name)

    def rotate(self, angle: float, rad: bool = False):
        """
        Rotate the compound object rotating each component shape
        """
        for shape in self.shapes:
            shape.rotate(angle, rad)

    def traslate(self, x: float, y: float):
        """
        Traslate the compound object traslating each component shape
        """
        for shape in self.shapes:
            shape.traslate(x, y)

    def move(self, x: float, y: float, angle: float, rad: bool = False):
        """
        Move(that is rotate first and traslate after) each component shape
        """
        for shape in self.shapes:
            shape.move(x, y, angle, rad)

    def add_shape(self, *shape_objs: shapes.Shape):
        """Adds a variabile number of new shapes to an already built
        compound
        """
        if shape_objs == ():
            logger.warning("No new shape to add")
            return
        for shape_obj in shape_objs:
            self.shapes.append(shape_obj)
            self.points += shape_obj.get_points()
        return

    def size(self):
        """
        Returns the numeber of points composing the shape.
        It serves to give an idea of the number of calculations to be made
        """
        if self.points != []:
            return len(self.points)

        # No build has been made till now, so calculate number of
        # compound size at flight
        num_points = 0
        for shape in self.shapes:
            num_points += shape.size()
        return num_points

# Test --------------------------------------------------------------------
def chair_constructor():
    """Footprint of a four legged classic chair"""
    leg_side = 5 # cm
    leg1 = shapes.Square(leg_side)
    leg1.color("r")
    leg2 = shapes.Square(leg_side)
    leg2.traslate(30, 0)
    leg2.color("r")
    leg3 = shapes.Square(leg_side)
    leg3.traslate(30, 40)
    leg3.color("k")
    leg4 = shapes.Square(leg_side)
    leg4.traslate(0, 40)
    leg4.color("r")

    legs = [leg1, leg2, leg3, leg4]
    chair = CompoundShape(legs, "chair")
    chair.rotate(45)
    chair.move(10, 10, 15)
    chair.show()
    return chair

def adding_shapes(compound: CompoundShape):
    """Add shapes to a compound"""
    circ1 = shapes.Circle(20)
    circ1.move(20, 20)
    circ2 = shapes.Circle(10)
    circ2.move(10, 10)
    tri = shapes.IsoscelesTriangle(30, 10)
    tri.move(30, 40)

    compound.add_shape(circ1, circ2, tri)
    compound.show()

def main():
    """
    Main function for test purposes only
    """
    chair = chair_constructor()
    adding_shapes(chair)
    # adding_shapes_by_points(chair)

if __name__ == "__main__":
    main()
