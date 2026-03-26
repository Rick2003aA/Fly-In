from src.domain import Graph, Zone, Connection, Drone, DroneStatus, ZoneType
from src.simulation import SimulationState


def set_up_test() -> tuple[Graph, SimulationState]:
    # ==== adding zones ====
    start = Zone(name="start", x=0, y=0, max_drones=1)

    mid = Zone(name="mid", x=1, y=0,
               zone_type=ZoneType.NORMAL, max_drones=1)

    blocked_mid = Zone(name="blocked_mid", x=1, y=1,
                       zone_type=ZoneType.BLOCKED, max_drones=1)

    priority_mid = Zone(name="priority_mid", x=1, y=2,
                        zone_type=ZoneType.PRIORITY, max_drones=1)

    goal = Zone(name="goal", x=2, y=0, max_drones=1)

    # ==== adding connections ====

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

    # ==== for blocked area ====

    connection_3 = Connection(
        connection_name="start-blocked",
        zone_a="start",
        zone_b="blocked_mid",
    )

    connection_4 = Connection(
        connection_name="blocked-goal",
        zone_a="blocked_mid",
        zone_b="goal",
    )

    # ==== for priority area ====

    connection_5 = Connection(
        connection_name="start-priority",
        zone_a="start",
        zone_b="priority_mid",
    )

    connection_6 = Connection(
        connection_name="priority-goal",
        zone_a="priority_mid",
        zone_b="goal",
    )

    # ==== adding drones ====

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
    graph.add_zone(blocked_mid)
    graph.add_zone(priority_mid)
    graph.add_zone(goal)

    graph.add_connection(connection_1)
    graph.add_connection(connection_2)
    graph.add_connection(connection_3)
    graph.add_connection(connection_4)
    graph.add_connection(connection_5)
    graph.add_connection(connection_6)

    state = SimulationState(
        current_turn_number=0,
        drones=[drone1, drone2],
        zone_occupancy={
            "start": {drone1.drone_id, drone2.drone_id},
            "mid": set(),
            "blocked_mid": set(),
            "priority_mid": set(),
            "goal": set(),
        },
        connection_occupancy={
            "start-mid": set(),
            "mid-goal": set(),
            "start-blocked": set(),
            "blocked-goal": set(),
            "start-priority": set(),
            "priority-goal": set()
        },
    )
    return graph, state


if __name__ == "__main__":
    graph, state = set_up_test()
    all_turns = []
    while not state.all_delivered():
        turn_moves = state.simulate_one_turn(graph)
        all_turns.append(turn_moves)

    for turn in all_turns:
        print(" ".join(turn))

    # i = 0
    # while i < 3:
    #     print(f"==== Trun {i} ====")
    #     state.simulate_one_turn(graph)
    #     print(f"Current turn number: {state.current_turn_number}")
    #     print(f"Drone position: {state.drones[0].current_zone}")
    #     print(f"Drone status: {state.drones[0].status}")
    #     print(f"Zone state: {state.zone_occupancy}")
    #     print(f"Connection state: {state.connection_occupancy}")
    #     print(f"Target: {state.drones[0].target_zone}")
    #     print(f"Connections: {state.drones[0].current_connection}")
    #     print()
    #     i += 1
