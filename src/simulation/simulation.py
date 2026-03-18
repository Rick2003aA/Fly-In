from pydantic import BaseModel
from ..domain.drone import Drone
from ..domain.enums import DroneStatus, ZoneType
from ..domain.graph import Graph
"""
zone_occupancy = {
    "start": {2, 3},
    "roof1": set(),
    "goal": set(),
}

connection_occupancy = {
    "start-roof1": {1},
}
"""


class SimulationState(BaseModel):
    current_turn_number: int
    drones: list[Drone]
    zone_occupancy: dict[str, set[int]]
    connection_occupancy: dict[str, set[int]]

    # ==== Looking for drones in any zones and connections ====

    def get_drone(self, drone_id: int) -> Drone:
        """
        get drone info from its id
        """
        for drone in self.drones:
            if drone.drone_id == drone_id:
                return drone
        raise ValueError(f"Drone {drone_id} not found")

    def drones_in_zone(self, zone_name: str) -> list[Drone]:
        drones = []
        drone_ids = self.zone_occupancy[zone_name]
        for drone_id in drone_ids:
            drones.append(self.get_drone(drone_id))
        return drones

    def drones_in_connection(self, connection_name: str) -> list[Drone]:
        drones = []
        drone_ids = self.connection_occupancy[connection_name]
        for drone_id in drone_ids:
            drones.append(self.get_drone(drone_id))
        return drones

    # ==== add/remove drones from zones and connections ====

    def add_drone_to_zone(self, zone_name: str, drone: Drone) -> None:
        self.zone_occupancy[zone_name].add(drone.drone_id)

    def remove_drone_from_zone(self, zone_name: str, drone: Drone) -> None:
        self.zone_occupancy[zone_name].remove(drone.drone_id)

    def add_drone_to_connection(self, connection_name: str,
                                drone: Drone) -> None:
        self.connection_occupancy[connection_name].add(drone.drone_id)

    def remove_drone_from_connection(self, connection_name: str,
                                     drone: Drone) -> None:
        self.connection_occupancy[connection_name].remove(drone.drone_id)

    # ==== Investigating the drone status ====

    def restricted_transit_drones(self) -> list[Drone]:
        return [
            drone
            for drone in self.drones
            if drone.status == DroneStatus.IN_RESTRICTED_TRANSIT
        ]

    def forced_arrival_drones(self) -> list[Drone]:
        return [
            drone
            for drone in self.drones
            if drone.remaining_travel_turns == 1
            and drone.status == DroneStatus.IN_RESTRICTED_TRANSIT
        ]

    def free_drones(self) -> list[Drone]:
        return [
            drone
            for drone in self.drones
            if drone.status == DroneStatus.AT_ZONE
        ]

    def delivered_drones(self) -> list[Drone]:
        return [
            drone
            for drone in self.drones
            if drone.status == DroneStatus.DELIVERED
        ]

    def undelivered_drones(self) -> list[Drone]:
        return [
            drone
            for drone in self.drones
            if drone.status != DroneStatus.DELIVERED
        ]

    def all_delivered(self):
        for drone in self.drones:
            if drone.status != DroneStatus.DELIVERED:
                return False
        return True

    # ==== Implementing drone vehaviors ====

    def apply_forced_arrivals(self, graph: Graph):
        for drone in self.forced_arrival_drones():
            connection_name = drone.current_connection
            target_zone = drone.target_zone
            self.remove_drone_from_connection(connection_name, drone)
            self.add_drone_to_zone(target_zone, drone)
            drone.current_zone = target_zone
            if target_zone == graph.end_hub_name:
                drone.status = DroneStatus.DELIVERED
                drone.current_zone = target_zone
                drone.remaining_travel_turns = 0
                drone.target_zone = None
            else:
                drone.status = DroneStatus.AT_ZONE
                drone.current_zone = target_zone
                drone.current_connection = None
                drone.remaining_travel_turns = 0
