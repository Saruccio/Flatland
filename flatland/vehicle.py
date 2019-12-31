# File: vehicle.py
# Date: 09-11-2019
# Author: Saruccio Culmone
#
"""
Base class that allows implementation a vehicle with one or more sensors on
board.
The movement method allow to simulate realistic movements in a Flatland
environment as if it were a physical object.
"""

# Imports
from trace import logger
import shapes
import numpy as np
from collections import namedtuple
import geom_utils as geom
from sensor import Sensor
from flatland import FlatLand
import matplotlib.pyplot as plt

# Point type
Point = namedtuple("Point", ["x", "y"])

# DataPath: position and orientation of the Vehicle
DataPath = namedtuple("DataPath", ["x", "y", "angle", "seq"]) 


class SensorHook():
    """
    Stores all data related to the sensor mounting on the chassis and the
    sensor itself.
    
    Angular data unit is radiant for all internal calculation even if 
    when passed as input degrees are used.
    """
    def __init__(self, mnt_pt: Point, mnt_orient: float, device: Sensor):
        """
        Associate a sensor mount point (the sensor hook) to asensor device 
        
        Arguments:
        :param mnt_pt: coordinates of the mount point in the chassis reference
                    system
        :type mnt_ot: Point
        :param mnt_orient: anglular orientation of the sensor with respecgt 
                           to the chassis.
        :type mnt_orient: float in degrees
        """
        self.mnt_pt = mnt_pt
        self.mnt_orient = mnt_orient
        self.device = device

    def update_dev_orient(self, chassis_pos: Point, chassis_angle: float):
        """
        Rotate the sensor hook and the connected device.
        Whe the chassis rotates its center does not move but sensor mount
        points rotate around it.

        Arguments:
        :param chassis_angle: angle of the chassis that mounts the device
        :type chassis_angle: float in degreees
        """
        # Update absolute device orientation and according with it the 
        # orientation of the chassis        
        dev_orient = self.mnt_orient + chassis_angle
        
        # Calculate the rotation of the mount points
        # New position related to the chassis
        new_x, new_y = geom.rotate([self.mnt_pt], chassis_angle)[0]
        
        # New absolute position
        newdev_x = chassis_pos.x + new_x
        newdev_y = chassis_pos.y + new_y
        
        self.device.move((newdev_x, newdev_y), dev_orient)
    
class ChassisShape(shapes.Rectangle):
    """
    ChassisShape is a modified Rectangle with a double line on the right
    side in order to mark the front side of the Vehicle.
    """
    def __init__(self, base: float, height: float, gap: float, res: float = 0.1):
        """
        Initialize the base class and draw the second vertical line at
        right rectangle side.

        Arguments:
        :param base: the base of the rectangle along the x axis
        :param height: the height of the rectangle along the y axis
        :param gap: the distance between the right side of the rectangle and
                    the second side drown internally to mark the front of
                    the chassis
        :param res: the distance among points in the sides of the rectangle
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
    A Vehicle is chassis with some sensors onboard.
    Every time the vehicle moves, the positiona and the orientation of each
    sensor must be updated
    """
    def __init__(self, length, width, name = "Vehicle", color = "r"):
        """
        Defines dimensions and graphical aspect of the vehicle
        """
        # Position defaults to the origin of the reference system
        self.position = Point(0, 0)

        # Orientation is taken from the x (horizontal) axis and is stored
        # in degrees but all calculation are performed in radiants
        self.orientation = 0 # deg
        
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

        # Shape. Set the gap between the two front lines to 0.5
        gap = 0.5
        self.shape = ChassisShape(length, width, gap)
        self.shape.color(color)

        # Sensor list as dictionay; this way you can read sensor by name
        self.sensor_hooks = dict()
        
        # Flatland Environment 
        self.flatland = None
        
        # Trecing flag
        self.tracing = False
        
    def __str__(self):
        """
        Returns a string with basic vehicle data: 
        -- name
        -- position 
        -- orientation
        """
        return "{}: {} {} deg".format(self.name, self.position, self.orientation)

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

    def mount_sensor(self, mount_pt: Point, mount_angle: float, sensor: Sensor):
        """
        Mounting a sensor on a chassis means to store the Sensor instance
        along with its mounting positions on the vehicle chassis.
        Mount point coordinates are related to the origin of the coordinate
        system of the chassis.
        These positions must be updated at each vehicle movement.

        :Arguments:
        :param mount_pt: sensor mount point on the chassis
        :type mount_pt: Point
        :param mount_angle: mounting angle of the sensor in degrees
        :param sensor: Sensor instance
        :returns: True if mounting succeded, False il mounting fails
        """
        mount_x, mount_y = mount_pt
        if ((mount_x > self.length/2) or (mount_x < -self.length/2)):
            return False

        if ((mount_y > self.width/2) or (mount_y < -self.width/2)):
            return False

        # Position the sensor
        sensor.move(mount_pt, mount_angle)
        sensor_data = SensorHook(mount_pt, mount_angle, sensor)

        sens_name = sensor.name
        self.sensor_hooks[sens_name] = sensor_data
        msg = "Sensor '{}' mounted onto vehicle '{}'".format(sens_name, self.name)
        logger.info(msg)
        return True

    def _draw_vehicle_shape(self):
        """
        Draws the vehicle shape according with its position and angular
        orientation
        """
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

        :Arguments:
        :param angle: rotation angle (positive to LEFT, negative to RIGHT)
        :type angle: float degrees

        :returns: the new orientation of the vehicle
        """
        # Positive angles perform rotation toward left, negative toward
        # right
        rot_angle = self.orientation + angle
        return rot_angle

    def turn(self, angle: float):
        """
        Turns the vehicle and sensor on it of angle degrees in the desired
        direction

        :Arguments:
        :param dir: turn direction: LEFT or RIGHT
        :type dir: Vehicle.LEFT, Vehicle.RIGHT
        :param angle: rotation angle
        :type angle: float degrees
        :returns: None
        """
        # Update chassis orientation and orient its shape
        self.orientation = self.model_turn(angle)
        self._draw_vehicle_shape()
        
        # Update sensor orientation
        for sensor_id in self.sensor_hooks:
            self.sensor_hooks[sensor_id].update_dev_orient(self.position, self.orientation)

        # Save data path
        self._save_datapath()
        
        # Perform light tracing if required
        if self.tracing is True:
            self.light_plot()

    def model_move(self, distance: float):
        """
        Returns the new position of the vehicle after the requested linear move.
        In this default method an ideal linear move is implemented.
        Positve values for distance are for forward movement, negative for 
        backward.

        Override or overload this method to implement your own linear move 
        model (for example taking into account deterministic or random errors).

        :Arguments:
        :param distance: distance at which the vehicle will stop. Negative values will be transformed in positive.
        :type distance: float in length unit defined for the overall simulation.
        :Return:
        :type: tuple (x, y)
        """
        abs_dist = np.abs(distance)
        
        # Calculate the cartesian absolute coordinates of the destination point
        x_move = abs_dist * np.cos(np.deg2rad(self.orientation))
        y_move = abs_dist * np.sin(np.deg2rad(self.orientation))
        
        # Calculate the actual point
        if distance < 0:
            x_move = -x_move
            y_move = -y_move
        
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
        for slot in self.sensor_hooks:
            self.sensor_hooks[slot].update_dev_orient(self.position, self.orientation)

        # Save data path
        self._save_datapath()

        # Perform light tracing if required
        if self.tracing is True:
            self.light_plot()

    def load_env(self, flatland: FlatLand):
        """
        In order to interact with the virtual environment, the vehicle
        must load a list of shapes or compound objects from a flatland
        environment.
        
        Optimization step:
        Since the vehicle cannot *see* objects that are positioned outside
        of the range of its sensors, the loaded environment will be filtered
        and only surrounding points will be saved.
        """
        # Store flatland environment
        self.flatland = flatland
        
        # Push the environment into the sensors
        for hook_id in self.sensor_hooks:
            self.sensor_hooks[hook_id].device.load_env(self.flatland.venv)


    def scan(self, sensor_name: str, 
                angle_from: float = -90, 
                angle_to: float = 90, 
                angle_step: float = 1):
        """
        Performs a sensor scan of the virtual environment loaded.
        It is possible to scan all sensors or a single sensor specifying its
        name.
        The same scan limits will be applaied to all sensors.
        
        A dictionry of readings is returned with key the name of the sensor
        """
        scan_data = dict()
        
        if sensor_name == "all":
            for s_name in self.sensor_hooks:
                sensor = self.sensor_hooks[s_name].device
                scan_data[s_name] = sensor.scan(angle_from, angle_to, angle_step)
        elif sensor_name in self.sensor_hooks:
            sensor = self.sensor_hooks[sensor_name].device
            scan_data[sensor_name] = sensor.scan(angle_from, angle_to, angle_step)
        else:
            error_msg = "ERROR - Scan failed. Sensor '{}' not found".format(sensor_name)
            logger.error(error_msg)
            
        return scan_data

    def plot(self):
        """
        Add Vehicle shape and sensors to current plot
        """
        self.shape.plot()
        for sensor in self.sensor_hooks:
            self.sensor_hooks[sensor].device.plot()

        # Plot actual vehicle position
        geom.plot_point(self.position)
        xp, yp = self.position
        yn = yp + 0.3
        name_point = Point(xp, yn)
        geom.annotate_point(name_point, self.name)

    def light_plot(self):
        """
        A lighter version of plot method that plots only sensors and actual
        position of vehicle.
        """
        for sensor in self.sensor_hooks:
            self.sensor_hooks[sensor].device.plot()

        # Plot actual vehicle position
        geom.plot_point(self.position)
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
    twv = Vehicle(length, width, "SBOT")
    print(twv)

    # Create a sensor and put it in the middle of the front side of the vehicle
    S1 = Sensor(40, 60, "S_Front")
    twv.mount_sensor((length/2, 0), 0, S1)
    twv.plot()
    
    # Create 2 more sensors and mount them at +/-45 deg into the chassis
    S2 = Sensor(40, 60, "S_Left")
    twv.mount_sensor((5,5), 45, S2)

    S3 = Sensor(40, 60, "S_Right")
    twv.mount_sensor((5, -5), -45, S3)
    
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

