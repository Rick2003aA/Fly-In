from pydantic import BaseModel
from ..domain.drone import Drone
from ..domain.enums import DroneStatus, ZoneType
from ..domain.graph import Graph
import heapq
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

    def add_drone_to_connection(self, connection_name: str, drone: Drone) -> None:
        self.connection_occupancy[connection_name].add(drone.drone_id)

    def remove_drone_from_connection(self, connection_name: str, drone: Drone) -> None:
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

    def all_delivered(self) -> bool:
        for drone in self.drones:
            if drone.status != DroneStatus.DELIVERED:
                return False
        return True

    # ==== Implementing drone behaviors ====

    def move_drone(self, drone: Drone, target_zone: str, graph: Graph) -> None:
        if graph.get_zone(target_zone).zone_type == ZoneType.RESTRICTED:
            # remove drone from zone
            current_zone = drone.current_zone
            self.remove_drone_from_zone(current_zone, drone)

            # add drone to connection
            connection = graph.get_connection(current_zone, target_zone).connection_name
            self.add_drone_to_connection(connection, drone)
            drone.current_connection = connection

            drone.status = DroneStatus.IN_RESTRICTED_TRANSIT
            drone.target_zone = target_zone
            drone.current_zone = None
            drone.remaining_travel_turns = 1
        else:
            current_zone = drone.current_zone
            self.remove_drone_from_zone(current_zone, drone)
            self.add_drone_to_zone(target_zone, drone)
            drone.current_zone = target_zone
            if target_zone == graph.end_hub_name:
                drone.status = DroneStatus.DELIVERED
            else:
                drone.status = DroneStatus.AT_ZONE
            drone.target_zone = None
            drone.current_connection = None
            drone.remaining_travel_turns = 0

    def apply_forced_arrivals(self, graph: Graph) -> list[Drone]:
        """
        complete the landing
        clean the transit fields
        set status to DELIVERED or AT_ZONE
        """
        arrived_drones = []

        for drone in self.forced_arrival_drones():
            connection_name = drone.current_connection
            target_zone = drone.target_zone

            self.remove_drone_from_connection(connection_name, drone)
            self.add_drone_to_zone(target_zone, drone)

            drone.current_zone = target_zone
            drone.current_connection = None
            drone.remaining_travel_turns = 0
            drone.target_zone = None

            if target_zone == graph.end_hub_name:
                drone.status = DroneStatus.DELIVERED
            else:
                drone.status = DroneStatus.AT_ZONE

            arrived_drones.append(drone)

        return arrived_drones

    # ==== Simulation ====

    def choose_next_zones(self, drone: Drone, graph: Graph) -> list[str]:
        """
        priorityが先、othersが後に処理されるような配列(str)を作成する
        ここですでにPriorityの最適化は完了している
        """
        priority_zones = []
        other_zones = []
        neighbors = graph.neighbor_zones(drone.current_zone)
        if graph.end_hub_name in neighbors:
            return [graph.end_hub_name]

        for zone in neighbors:
            zone_type = graph.get_zone(zone).zone_type
            if zone_type == ZoneType.BLOCKED:
                continue
            if zone_type == ZoneType.PRIORITY:
                priority_zones.append(zone)
            else:
                other_zones.append(zone)

        return priority_zones + other_zones

    def can_enter_zone(self, zone_name: str, graph: Graph) -> bool:
        if zone_name == graph.end_hub_name:
            return True
        if len(self.zone_occupancy[zone_name]) < graph.get_zone(zone_name).max_drones:
            return True
        else:
            return False

    def can_use_connection(self, connection_name: str, graph: Graph) -> bool:
        for connection in graph.connections:
            if connection.connection_name == connection_name:
                return (
                    len(self.connection_occupancy[connection_name])
                    < connection.max_link_capacity
                )
        raise ValueError(f"Connection {connection_name} not found")

    def build_planned_moves(
        self, graph: Graph, free_drones: list[Drone]
    ) -> list[dict[str, object]]:
        planned_moves: list[dict[str, object]] = []

        for drone in free_drones:
            zone_options = self.choose_next_zones(drone, graph)

            if not zone_options:
                continue

            planned_move = {
                "drone": drone,
                "zone_options": zone_options,
            }
            planned_moves.append(planned_move)
        return planned_moves

    def apply_planned_move(self,
                           drone: Drone,
                           target_zone: str,
                           graph: Graph) -> str:

        if graph.get_zone(target_zone).zone_type == ZoneType.RESTRICTED:
            connection = graph.get_connection(drone.current_zone, target_zone)
            connection_name = connection.connection_name
            self.move_drone(drone, target_zone, graph)
            return f"D{drone.drone_id}-{connection_name}"

        self.move_drone(drone, target_zone, graph)
        return f"D{drone.drone_id}-{target_zone}"

    # ==== Dijkstra ====
    def movement_cost(self, zone_name: str, graph: Graph) -> int:
        zone_type = graph.get_zone(zone_name).zone_type
        if zone_type in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        elif zone_type == ZoneType.RESTRICTED:
            return 2
        else:
            raise ValueError("fuck")

    def distances_to_goal(self, graph: Graph) -> dict[str, int]:
        """
        1. ダイクストラの出発点をゴールに設定
        2. 未確定の地点の中から最も小さい値を持つ地点を一つ選び、その値を確定
        3. 2で確定した地点とつながっているかつ未確定な地点に対し、かかる時間を計算し
        書き込まれている数より小さければ更新
        4. すべての地点が確定すれば終了。else, 2に戻る
        """
        distances = {zone_name: float("inf") for zone_name in graph.zones}
        goal = graph.end_hub_name
        distances[goal] = 0
        heap = [(0, goal)]
        while heap:
            current_distance, current_zone = heapq.heappop(heap)
            if current_distance > distances[current_zone]:
                continue
            neighbors = graph.neighbor_zones(current_zone)
            for neighbor in neighbors:
                if graph.get_zone(neighbor).zone_type == ZoneType.BLOCKED:
                    continue

                new_distance = current_distance + self.movement_cost(neighbor, graph)

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    heapq.heappush(heap, (new_distance, neighbor))
        return distances

    # ==== Evoke Simulation ====

    def simulate_one_turn(self, graph: Graph) -> list[str]:
        """
        全体の流れ
        1. Connection上にあるDroneをZoneに移す
        2. その他のDroneに対して、build→can_use/enter→apply
        """
        moved_drones: list[str] = []
        arrived_drones = self.apply_forced_arrivals(graph)

        for drone in arrived_drones:
            moved_drones.append(f"D{drone.drone_id}-{drone.current_zone}")

        free_drones = [
            drone for drone in self.free_drones()
            if drone not in arrived_drones
        ]
        planned_moves = self.build_planned_moves(graph, free_drones)
        for planned_move in planned_moves:
            drone = planned_move["drone"]
            zone_options = planned_move["zone_options"]
            for target_zone in zone_options:
                if graph.get_zone(target_zone).zone_type == ZoneType.RESTRICTED:
                    connection = graph.get_connection(drone.current_zone, target_zone)
                    if (
                        self.can_enter_zone(target_zone, graph)
                        and self.can_use_connection(connection.connection_name, graph)
                    ):
                        moved_drones.append(
                            self.apply_planned_move(drone, target_zone, graph)
                        )
                        break
                else:
                    if self.can_enter_zone(target_zone, graph):
                        moved_drones.append(
                            self.apply_planned_move(drone, target_zone, graph)
                        )
                        break
        self.current_turn_number += 1
        return moved_drones
