from src.domain import Graph, Zone, Connection, Drone, DroneStatus, ZoneType
from src.simulation import SimulationState


def set_up_test() -> tuple[Graph, SimulationState]:
    start = Zone(name="start", x=0, y=0, max_drones=1)
    mid = Zone(name="mid", x=1, y=0,
               zone_type=ZoneType.RESTRICTED, max_drones=1)
    goal = Zone(name="goal", x=2, y=0, max_drones=1)

    connection_1 = Connection(
        connection_name="start-mid",
        zone_a="start",
        zone_b="mid",
        max_link_capacity=1
    )

    connection_2 = Connection(
            connection_name="mid-goal",
            zone_a="mid",
            zone_b="goal",
        )

    drone1 = Drone(
        drone_id=1,
        status=DroneStatus.AT_ZONE,
        current_zone="start",
        target_zone=None,
        current_connection=None,
        remaining_travel_turns=0,
    )

    drone2 = Drone(
        drone_id=2,
        status=DroneStatus.AT_ZONE,
        current_zone="start",
        target_zone=None,
        current_connection=None,
        remaining_travel_turns=0,
    )

    graph = Graph(start_hub_name="start", end_hub_name="goal")

    graph.add_zone(start)
    graph.add_zone(mid)
    graph.add_zone(goal)

    graph.add_connection(connection_1)
    graph.add_connection(connection_2)

    state = SimulationState(
        current_turn_number=0,
        drones=[drone1, drone2],
        zone_occupancy={
            "start": {1, 2},
            "mid": set(),
            "goal": set(),
        },
        connection_occupancy={
            "start-mid": set(),
            "mid-goal": set(),
        },
    )
    return graph, state


if __name__ == "__main__":
    graph, state = set_up_test()

    i = 0
    while i < 6:
        print(f"==== Trun {i} ====")
        state.simulate_one_turn(graph)
        print(f"Current turn number: {state.current_turn_number}")
        print(f"Drone position: {state.drones[0].current_zone}")
        print(f"Drone status: {state.drones[0].status}")
        print(f"Zone state: {state.zone_occupancy}")
        print(f"Connection state: {state.connection_occupancy}")
        print(f"Target: {state.drones[0].target_zone}")
        print(f"Connections: {state.drones[0].current_connection}")
        print()
        i += 1
