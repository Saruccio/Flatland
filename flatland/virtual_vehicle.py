# File: vehicle.py
# Date: 19-08-2020
# Author: Saruccio Culmone
#
"""
Implementation a virtual vehicle with one or more virtual sensors on
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
from virtual_sensor import VirtualSensor
from vehicle import Vehicle, ChassisShape
from flatland import FlatLand
from shapes import Circle


# Point type
Point = namedtuple("Point", ["x", "y"])

# DataPath: position and orientation of the Vehicle
DataPath = namedtuple("DataPath", ["x", "y", "angle", "seq"]) 


class VirtualVehicle(Vehicle):
    """
    A VirualVehicle is a Vehicle equipped with Virtual Sensors
    
    Every time the vehicle moves, the positiona and the orientation of each
    sensor will be updated.
    """
    def __init__(self, name: str, chassis_shape: ChassisShape):
        """
        Defines dimensions and graphical aspect of the vehicle
        
        Parameters
        ----------
        name : str
            name of the vehicle

        color : str
            color string as allowed by matplotlib's plot method
        """
        super().__init__(name, chassis_shape)


    def mount_sensor(self, name: str, beam: float, range: float, accuracy: float, mnt_pt: Point, mnt_orient: float):
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
        # Call baseclass method 
        super().mount_sensor(name, beam, range, accuracy, mnt_pt, mnt_orient)
        
        # Get orizontal and vertical dimensions from vhicle shape
        x_min, x_max = self.shape.x_min_max()
        y_min, y_max = self.shape.y_min_max()

        if ((mnt_pt.x < x_min) or (mnt_pt.x > x_max)):
            return False

        if ((mnt_pt.y < y_min) or (mnt_pt.y > y_max)):
            return False

        self.sensors[name] = VirtualSensor(name, beam, range, accuracy, mnt_pt, mnt_orient)
        self.sensors[name].update_placement(self.position, self.orientation)
        return True


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
        
        ping_res = self.sensors[sensor_name].ping(angle)
        logger.debug("Ping sensor '{}' at angle {}° = {}".format(sensor_name, angle, ping_res))
        return ping_res


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




# Test sction ---------------------------------------------------------------
def main():
    # Vehicle sizes (all dimensione in cm)
    length = 20
    width = 15
    color = "k"

    # Compose a vehicle
    # Set default Shape
    twv_shape = ChassisShape(length, width)
    twv = VirtualVehicle("TWV", twv_shape)
    print("Vehicle print test: ", twv)

    # Create a sensor and put it in the middle of the front side of the vehicle
    twv.mount_sensor(name="S_Front", beam=40, range=60, accuracy=2,
                      mnt_pt=Point(length/4, 0), mnt_orient=0)
    
    # Create 2 more sensors and mount them at +/-45 deg into the chassis
    # Left sensor
    twv.mount_sensor("S_Left", 40, 60, 2, Point(-length/4, width/2), 45)
    
    # Right sensor
    twv.mount_sensor("S_Right", 40, 60, 2, Point(-length/4, -width/2), -45)
    twv.plot(safe_reg=True)
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
    
    
    twv.turn(90)
    twv.plot()
    twv.show()
    
    return


if __name__ == "__main__":
    main()

