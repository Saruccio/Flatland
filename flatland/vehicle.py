# File: vehicle.py
# Date: 09-11-2019
# Author: Saruccio Culmone
#
"""
Base class that allows implementation a vehicle with one or more sensors on
board.
The movement method allow to simulate realistic movements in a Flatland
environment as if it were a physical vehicle in a physical environment.

The default vehile implemented is a two-wheels vehicle.

Note
----
Angular attributes are always expressed in radian units
Method parameters are always expressed in degrees
"""

# Imports
from trace import logger
import shapes
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple

# Project imports
import geom_utils as geom
from sensor_device import SensorDevice
from flatland import FlatLand


# Point type
Point = namedtuple("Point", ["x", "y"])

# DataPath: position and orientation of the Vehicle
DataPath = namedtuple("DataPath", ["x", "y", "angle", "seq"]) 



    
class ChassisShape(shapes.Rectangle):
    """
    ChassisShape is a modified Rectangle with a double line on the right
    side in order to mark the front side of the Vehicle.
    """
    
    def __init__(self, base: float, height: float, gap: float, res: float = 0.1):
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

        # Add second side
        xside = base - gap
        yords = np.arange(0.0, height, res)
        for y in yords:
            self.points.append((xside, y))

        # Traslate rectangle in order to be centered to the origin
        self.traslate(-base/2, -height/2)
        self.save()   # Save actual point configuration as
        self.reset()


class Vehicle():
    """
    A Vehicle is a chassis with some sensors onboard.
    
    Every time the vehicle moves, the positiona and the orientation of each
    sensor will be updated
    """
    def __init__(self, name: str, length: float, width: float, color = "r"):
        """
        Defines dimensions and graphical aspect of the vehicle
        
        Parameters
        ----------
        name : str
            name of the vehicle
        length : float
            vehicle orizontal dimension in its own reference system
        width : float
            vehicle vertical dimension in its own reference system
        color : str
            color string as allowed by matplotlib's plot method
        """
        # Position defaults to the origin of the reference system
        self.position = Point(0, 0)

        # Orientation is taken from the x (horizontal) axis and is stored
        # in radian
        self.orientation = 0 # rad
        
        # Vehicle path.
        # List of vehicle position and orientation after every movement
        self.path = []
        self.seq_counter = 0

        # Dimensions
        self.length = length
        self.width = width
        self.color = color

        # Vehicle name will be shown at vehicle position
        self.name = name

        # Vehicle Shape. 
        # Set the gap between the two front lines to 0.5
        gap = 0.5
        self.shape = ChassisShape(length, width, gap)
        self.shape.color(color)

        # Sensor list as dictionay; this way you can read sensor by name
        self.sensors = dict()
        
        # Flatland Environment 
        self.flatland = None
        
        # Tracing flag
        self.tracing = False
        
        # Compose format string to print the pose of the vehicle with
        # the precision desired
        self.pprec = 1 # one decimal digit, enough for dimensions in cm and degrees
        self.prec_str = "{:." + str(self.pprec) + "f}"
        self.format_str = "{}: " + "(" + self.prec_str + ", " + self.prec_str + ") " + self.prec_str + "°"
        # The expected string will have the format:
        # <STRNG>: (xxx.x, yyy.y) dddd.d°


    def __str__(self):
        """
        Returns a string with basic vehicle data: 
        -- name
        -- position 
        -- orientation
        """
        xpos, ypos = self.position
        return self.format_str.format(self.name, xpos, ypos, self.orientation)


    def trace(self, onoff: bool = False):
        """
        Set or unset the tracing functionality of vehicle.
        
        If tracing is enable the light_plot method will be called at the
        end of each move or rotation.
        """
        if onoff is True:
            self.tracing = True
        else:
            self.tracing = False


    def mount_sensor(self, name: str, beam: float, range: float, mnt_pt: Point, mnt_orient: float):
        """
        Pose a Sensor on the system reference of the vehicle.
        
        Mounting a sensor on a chassis means to store the Sensor instance
        along with its mounting positions on the vehicle chassis.
        Mount point coordinates are related to the origin of the coordinate
        system of the chassis.
        These positions must be updated at each vehicle movement.

        Parameters
        ----------
        same paramters od SensorDevice class
        
        Return
        ------
        True if mounting succeded
        False if mount point is outside the chassis.
        """

        if ((mnt_pt.x > self.length/2) or (mnt_pt.x < -self.length/2)):
            return False

        if ((mnt_pt.y > self.width/2) or (mnt_pt.y < -self.width/2)):
            return False

        self.sensors[name] = SensorDevice(name, beam, range, mnt_pt, mnt_orient)
        self.sensors[name].update_placement(self.position, self.orientation)
        return True

    def _draw_vehicle_shape(self):
        """Draws the vehicle shape according with its position and angular orientation"""
        self.shape.reset()
        self.shape.rotate(self.orientation)
        posx, posy = self.position
        self.shape.traslate(posx, posy)
        
    def _save_datapath(self):
        """
        Logs movements during the vehicle path.
        
        The movement type (turn or move) allows to maintain a sequence into
        stored data for a better graphical representation
        """
        self.seq_counter += 1
        pace = DataPath(self.position.x, self.position.y, self.orientation, self.seq_counter)
        self.path.append(pace)

    def model_turn(self, angle: float):
        """
        Returns the vehicle new orientation after the requested turn.
        
        In this default method an ideal turn (without any kind of
        errors) is implemented.
        Override or overload this method to implement you own turn model.

        Parameters
        ----------
        angle : float
            rotation angle (positive to LEFT, negative to RIGHT)

        Return
        ------
        the new orientation of the vehicle
        """
        # Positive angles perform rotation toward left, negative toward
        # right
        rot_angle = self.orientation + angle
        return rot_angle

    def turn(self, angle: float):
        """
        Turn the vehicle.
        
        After turn all sensors mounted on the vehicle will have their position
        and orientation updated accordingly with the new vehicle orientation.

        Parameters
        ----------
        angle : float
            If angle > 0 turn direction LEFT
            Otherwise turn direction RIGHT

        Return
        ------
        None
        """
        # Update chassis orientation and orient its shape
        self.orientation = self.model_turn(angle)
        self._draw_vehicle_shape()
        
        # Update sensor orientation
        for sensor_id in self.sensors:
            self.sensors[sensor_id].update_placement(self.position,
                                                     self.orientation)

        # Save data path
        self._save_datapath()
        
        # Perform light tracing if required
        if self.tracing is True:
            self.light_plot()

        # Trace vehicle pose and orientation
        logger.debug(self.__str__())
            
    def linear_move(self, distance: float):
        """
        Implements an ideal move forward of backward along the orientation
        of the vehicle.
        
        Parameters
        ----------
        distance : float
            If distance > 0 move forward
            Otherwise move backward
            
        Return
        ------
        None
        """
        abs_dist = np.abs(distance)
        
        # Calculate the cartesian absolute coordinates of the destination point
        x_move = abs_dist * np.cos(np.deg2rad(self.orientation))
        y_move = abs_dist * np.sin(np.deg2rad(self.orientation))
        
        # Calculate the actual point
        if distance < 0:
            x_move = -x_move
            y_move = -y_move
            
        return (x_move, y_move)


    def model_move(self, distance: float):
        """
        Implement linear movement.
        
        Returns the new position of the vehicle after the requested linear move.
        In this default method an ideal linear move is implemented.
        Positve values for distance are for forward movement, negative for 
        backward.

        Override or extend this method to implement your own linear move 
        model (for example taking into account deterministic or random errors).

        Parameters
        ----------
        distance : float
            distance at which the vehicle will stop. 
            Negative values will be transformed in positive.
        
        Return
        ------
        tuple (x, y)
        """
        x_move, y_move = self.linear_move(distance)
        move_pt = Point(x_move, y_move)
        
        # Now traslate vehicle at that point
        x_dest = self.position.x + move_pt.x
        y_dest = self.position.y + move_pt.y
        
        return (x_dest, y_dest)        


    def move(self, distance: float):
        """
        Place the vehicle at the end of the segment of length 'distance'
        along the direction defined by its orientation.

        :Arguments:
        :param dir: direction of the desired movement. Could take only two values forward and backward
        :type dir: Vehicle constants FORWARD, FWD, BACKWARD, BACK
        :param distance: distance at which the vehicle will stop. Negative values will be transformed in positive.
        :type distance: float in length unit defined for the overall simulation.
         
        """
        x_dest, y_dest = self.model_move(distance)
        self.position = Point(x_dest, y_dest)
        self._draw_vehicle_shape()
        
        # Now reposition all onboard sensors
        for sensor_id in self.sensors:
            self.sensors[sensor_id].update_placement(self.position,
                                                     self.orientation)
        # Save data path
        self._save_datapath()

        # Perform light tracing if required
        if self.tracing is True:
            self.light_plot()

        # Trace vehicle pose and orientation
        logger.debug(self.__str__())


    def load_env(self, flatland: FlatLand):
        """
        In order to interact with the virtual environment, the vehicle
        must load a list of shapes or compound objects from a flatland
        environment.
        
        Optimization step:
        Since the vehicle cannot *see* objects that are positioned outside
        of the range of its sensors, the loaded environment will be filtered
        and only surrounding points will be loaded.
        """
        # Store flatland environment
        self.flatland = flatland
        
        # Push the environment into the sensors
        for sensor_id in self.sensors:
            self.sensors[sensor_id].load_env(self.flatland.venv)




    def scan(self, sensor_name: str, 
                angle_from: float = -90, 
                angle_to: float = 90, 
                angle_step: float = 1):
        """
        Perform a sensor scan of the virtual environment loaded.
        
        It is possible to scan all sensors or a single sensor by name.
        The same angle ranges will be applaied to all sensors.
        A dictionry of readings is returned with key the name of the sensor
        
        Parameters
        ----------
        sensor_name: str
            Name of the sensoe to read
        angle_from, angle_to, angle_step : float
            See description of Sensor.scan() method
            
        Return
        ------
        {} empty dict in error case
        {"sensor1": [(rho1, phi1), (rho2, phi2), ...], ...}
        """
        scan_data = dict()
        
        if sensor_name == "all":
            logger.debug("Scanning 'all' sensors")
            for s_name in self.sensors:
                logger.debug("Scan sensor '{}'".format(sname))
                scan_data[s_name] = self.sensors[s_name].scan(angle_from, angle_to, angle_step)
        elif sensor_name in self.sensors:
            logger.debug("Scan sensor '{}'".format(sensor_name))
            scan_data[sensor_name] = self.sensors[sensor_name].scan(angle_from, angle_to, angle_step)
        else:
            error_msg = "ERROR - Scan failed. Sensor '{}' not found".format(sensor_name)
            logger.error(error_msg)
            
        return scan_data

    def plot(self):
        """
        Add Vehicle shape and sensors to current plot
        """
        self.shape.plot()
        for sensor in self.sensors:
            self.sensors[sensor].plot()

        # Plot actual vehicle position
        geom.plot_point(self.position)
        xp, yp = self.position
        yn = yp + 0.3
        name_point = Point(xp, yn)
        geom.annotate_point(name_point, self.name)

    def light_plot(self, show_name: bool=False):
        """
        A lighter version of plot method that plots only sensors and actual
        position of vehicle.
        """
        for sensor_id in self.sensors:
            self.sensors[sensor_id].plot()

        # Plot actual vehicle position
        geom.plot_point(self.position)
        if show_name:
            xp, yp = self.position
            yn = yp + 0.3
            name_point = Point(xp, yn)
            geom.annotate_point(name_point, self.name)

    def plot_path(self, pen_color: str = "c"):
        """
        Plots the overall sequence of points collected after each movement.
        """
        xs = []
        ys = []
        for data_pt in self.path:
            xs.append(data_pt.x)
            ys.append(data_pt.y)
            
        pen = pen_color + "--"
        plt.plot(xs, ys, pen)
        

    def show(self):
        """
        Shows the overall picture at this point.
        This function is ususlly usefull for debuggin purposes, because is
        in charge of the Flatland object to show the environment.
        """
        geom.show()

# Test sction ---------------------------------------------------------------
def main():
    # Vehicle sizes (all dimensione in cm)
    length = 20
    width = 15
    color = "k"

    # Create a vehicle
    twv = Vehicle("TWV", length, width)
    print(twv)

    # Create a sensor and put it in the middle of the front side of the vehicle
    twv.mount_sensor(name="S_Front", beam=40, range=60, 
                      mnt_pt=Point(length/2, 0), mnt_orient=0)
    
    # Create 2 more sensors and mount them at +/-45 deg into the chassis
    # Left sensor
    twv.mount_sensor("S_Left", 40, 60, Point(5, 7.5), 45)
    
    # Right sensor
    twv.mount_sensor("S_Right", 40, 60, Point(5, -7.5), -45)
    
    twv.plot()
    twv.show()
    
    # Now turn vehicle left and right a few times
    twv.turn(45)
    print(twv)
    twv.plot()
    
    twv.move(50)
    print(twv)
    twv.plot()
    
    twv.turn(-20)
    print(twv)    
    twv.plot()
    
    twv.move(50)
    print(twv)
    twv.plot()
    
    twv.turn(-30)
    print(twv)   
    twv.plot()
    
    twv.move(50)
    print(twv)
    twv.plot()
    
    twv.turn(-40)
    print(twv)   
    twv.plot()
    
    twv.move(70)
    print(twv)
    twv.plot()
    
    twv.turn(45)
    print(twv)   
    twv.plot()
    
    twv.move(-60)

    # Plot it
    twv.plot()
    twv.show()



if __name__ == "__main__":
    main()

