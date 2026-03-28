from src.parsing import parser


if __name__ == "__main__":
    nb_drones, graph, state = parser.parse_map_file("maps/easy/01_linear_path.txt")
    print(nb_drones)
    print(graph.start_hub_name)
    print(graph.end_hub_name)
    print(graph.zones.keys())
    print(state.zone_occupancy)
    print(state.distances_to_goal(graph))

    while not state.all_delivered():
        turn_moves = state.simulate_one_turn(graph)
        print(" ".join(turn_moves))
