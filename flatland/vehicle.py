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
logger.add("vehicle.log", mode="w")

import shape
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
    def __init__(self, name: str):
        """
        Defines dimensions and graphical aspect of the vehicle
        
        Parameters
        ----------
        name : str
            name of the vehicle

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
        self.length = 0.0
        self.width = 0.0
        self.color = "r"

        # Vehicle name will be shown at vehicle position
        self.name = name

        # Vehicle Shape. 
        self.shape = None

        # Sensor list as dictionay; this way you can read sensor by name
        self.sensors = dict()
        
        # Flatland Environment 
        self.flatland = None
        
        # Tracing flag
        self.tracing = False
        

    def __str__(self):
        """Returns a string with all vehicle data"""
        pos_str = geom.str_point(self.position)
        out_str = "Vehicle '{}': {}, {:.1f}°".format(self.name, pos_str,
                                                np.rad2deg(self.orientation))
        out_str += "\n"
        for sensor_id in self.sensors:
            out_str += self.sensors[sensor_id].__str__() + "\n"
        out_str += "\n"
        return out_str


    def _draw_vehicle_shape(self):
        """Draws the vehicle shape according with its position and angular orientation"""
        self.shape.reset()
        self.shape.rotate(self.orientation, True)
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


    def sys_ref(self):
        """
        Return the position and orientation of the vehicle with respect to the
        external system reference

        Parameters
        ----------
        None

        Return
        ------
        (vehicle_position.x, vehicle_position.y, vehicle_orientation, True)
            The last element is always True because the mount orientation
            is kept from value stored in the class in radian
        """

        return (self.position.x, self.position.y, self.orientation, True)


    def hw_params(self, length: float, width: float):
        """
        Set hardware parameters as physical dimensions etc.
        
        When modeling real hardware this method can be overwritten to retrieve
        parameters values directly from the real vehicle.
        The current implementation is for simulation purposes.
        
        Parameters
        ----------
        length : float
            vehicle orizontal dimension in its own reference system
        width : float
            vehicle vertical dimension in its own reference system
        """
        
        self.length = length
        self.width = width


    def set_shape(self, shape: shape.Shape = None, color: str = "r"):
        """
        Set the shape of the vehicle for graphical representation.
        
        This method must be called after 'hw_params' method in order to
        use length and width vehicle dimensions.
        
        Parameters
        ----------
        shape : Shape
            The shape used for the graphical representation of the vehicle.
            If None, the default 'ChassisShape' will be assigned
        
        color : str
            Color of the graphical representation of the vehicle.
            Defautls to red ('r')
        """

        if shape is None:
            # Set default chassis shape
            # Set the gap between the two front lines to 0.5
            gap = 0.5
            self.shape = ChassisShape(self.length, self.width, gap)
            self.shape.color(color)
        else:
            self.shape = shape
            self.shape.color(color)

        self._draw_vehicle_shape()


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


    def turn(self, angle: float):
        """
        Turn the vehicle.
        
        After turn all sensors mounted on the vehicle will have their position
        and orientation updated accordingly with the new vehicle orientation.

        Parameters
        ----------
        angle : float
            Rotation angle in degrees units.
            If angle > 0 turn direction LEFT
            Otherwise turn direction RIGHT

        Return
        ------
        None
        """
        
        # logger.debug("before_turn: {}".format(self.__str__()))
        logger.debug("turn: {}°".format(angle)) 
        
        # Update chassis orientation and orient its shape
        self.orientation = self.orientation + np.deg2rad(angle)
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
        logger.debug("after turn: {}".format(self.__str__()))




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
        
        # logger.debug("before move: {}".format(self.__str__()))
        logger.debug("move: {}".format(distance))
        
        # Calculate the cartesian absolute coordinates of the destination point
        abs_dist = np.abs(distance)
        
        x_move = abs_dist * np.cos(self.orientation)
        y_move = abs_dist * np.sin(self.orientation)
        
        # Calculate the actual point
        if distance < 0:
            x_move = -x_move
            y_move = -y_move
        
        # Now traslate vehicle at that point
        x_dest = self.position.x + x_move
        y_dest = self.position.y + y_move
        
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

        logger.debug("after move: {}".format(self.__str__()))


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


    def ping(self, sensor_name: str, angle: float):
        """Return single sensor reading in a given direction"""

        if sensor_name not in self.sensors:
            error_msg = "ERROR - Ping failed. Sensor '{}' not found".format(sensor_name)
            logger.error(error_msg)
            return None
            
        logger.debug("Ping sensor '{}' at angle {}°".format(sensor_name, angle))
        return self.sensors[sensor_name].ping(angle)


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
                logger.debug("---Scanning sensor '{}'".format(s_name))
                scan_data[s_name] = self.sensors[s_name].scan(angle_from, angle_to, angle_step)
        elif sensor_name in self.sensors:
            logger.debug("Scan sensor '{}'".format(sensor_name))
            scan_data[sensor_name] = self.sensors[sensor_name].scan(angle_from, angle_to, angle_step)
        else:
            error_msg = "ERROR - Scan failed. Sensor '{}' not found".format(sensor_name)
            logger.error(error_msg)
            
        return scan_data


    def stop(self):
        """In real vehicle send command to stops currect action"""
        raise NotImplementedError()


    def reset(self):
        """In real vechile send command to reset vehicle firmware"""
        raise NotImplementedError()


    def scan_to_map(self, scan_data: dict, invert_rho_phi: bool = False):
        """
        Point transformation from sensor's local reference into the 'map' 
        (global) reference system.
        
        Readings obtaiened from each SensorDevice are in polar coordinates and
        are related to its local system reference.
        This method implements these transformation reference:
            - from polar to rectangular
            - from sensor local reference to vehicle reference
            - from vehicle reference to global (i.e. external) reference
        The global, vehicle-external reference is the system reference of the
        map built by the vehicle during its exploration.
        The origin of the global reference system coincide with the position
        of the vehicle at exploration start.
        
        Parameters
        ----------
        scan_data : dict
            dictionary of range measurements as returned by 'scan' method
        invert_rho_phi : bool
            Real sensor can return polar readings in tutle (phi, rho) instead
            of (rho, phi).
            If True, the readings are transformed from (phi, rho) to (rho, phi).
            Defaults to False
        """
        
        map_scan = dict()
        for sensor_id, readings in scan_data.items():
            # Convert polar readings in radian
            if invert_rho_phi:
                rad_polar_readings = [(rho, np.deg2rad(deg_phi)) 
                                    for deg_phi, rho in readings]
            else:
                rad_polar_readings = [(rho, np.deg2rad(deg_phi)) 
                                    for rho, deg_phi in readings]
                                    
            rect_readings = geom.to_rect(rad_polar_readings)
            
            # Transform sensor reading in the vehicle reference system
            sensor_ref = self.sensors[sensor_id].sys_ref()
            vehicle_ref_readings = geom.to_globalpos(rect_readings, sensor_ref)
            
            # Transform vehicle readings into the map (external) reference
            vehicle_ref = self.sys_ref()
            map_readings = geom.to_globalpos(rect_readings, vehicle_ref)
            map_scan[sensor_id] = map_readings
            
        return map_scan


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
        

    def show(self, title: str = "No title", label: str = ""):
        """
        Shows the overall picture at this point.
        This function is ususlly usefull for debuggin purposes, because is
        in charge of the Flatland object to show the environment.
        """
        geom.show(title, label)

# Test sction ---------------------------------------------------------------
def main():
    # Vehicle sizes (all dimensione in cm)
    length = 20
    width = 15
    color = "k"

    # Compose a vehicle
    twv = Vehicle("TWV")
    twv.hw_params(length, width)
    twv.set_shape()
    print("Vehicle print test: ", twv)

    # Create a sensor and put it in the middle of the front side of the vehicle
    twv.mount_sensor(name="S_Front", beam=40, range=60, 
                      mnt_pt=Point(length/2, 0), mnt_orient=0)
    
    # Create 2 more sensors and mount them at +/-45 deg into the chassis
    # Left sensor
    twv.mount_sensor("S_Left", 40, 60, Point(5, 7.5), 45)
    
    # Right sensor
    twv.mount_sensor("S_Right", 40, 60, Point(5, -7.5), -45)
    
    twv.plot()
    twv.show("At origin")
    
    # Now turn vehicle left and right a few times
    twv.turn(45)
    twv.plot()
    # twv.show("Turn 45°")
    
    twv.move(50)
    twv.plot()
    # twv.show("Move 50")
    
    twv.turn(-20)
    twv.plot()
    # twv.show("Turn -20°")
        
    twv.move(50)
    twv.plot()
    # twv.show("Move 50")
        
    twv.turn(-30)
    twv.plot()
    # twv.show("Turn -30°")
            
    twv.move(50)
    twv.plot()
    # twv.show("Move 50")
        
    twv.turn(-40)
    twv.plot()
    # twv.show("Turn -40°")
        
    twv.move(70)
    twv.plot()
    # twv.show("Move 70")
        
    twv.turn(45)
    twv.plot()
    # twv.show("Turn 45°")
        
    twv.move(-60)
    twv.plot()
    twv.show("Move -60")
    
    # Assign custom shape
    custom_shape = ChassisShape(5.0, 15.0, 1)
    twv.set_shape(custom_shape, 'b')
    twv.plot()
    twv.show()
    
    return


if __name__ == "__main__":
    main()

