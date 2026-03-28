from pydantic import BaseModel, Field

from ..domain.connection import Connection
from ..domain.drone import Drone
from ..domain.enums import DroneStatus, ZoneType
from ..domain.graph import Graph
from ..domain.zone import Zone
from ..simulation import SimulationState


class ParsedZoneRecord(BaseModel):
    prefix: str
    name: str
    x: int
    y: int
    metadata: dict[str, str] = Field(default_factory=dict)


class ParsedConnectionRecord(BaseModel):
    zone_a: str
    zone_b: str
    metadata: dict[str, str] = Field(default_factory=dict)


class ParsedMapData(BaseModel):
    nb_drones: int | None = None
    start_hub_name: str | None = None
    end_hub_name: str | None = None
    zones: list[ParsedZoneRecord] = Field(default_factory=list)
    connections: list[ParsedConnectionRecord] = Field(default_factory=list)


def read_input_file(path: str) -> list[str]:
    """Read raw file lines."""
    with open(path, "r", encoding="utf-8") as file:
        return file.readlines()


def clean_line(line: str) -> str:
    """
    コメントを削除
    先頭と末尾の空白及び改行を削除
    """
    line_without_comment = line.split("#", 1)[0]
    return line_without_comment.strip()

# ==== Helper methods ====


def split_main_and_metadata(content: str) -> tuple[str, str | None]:
    """Split a line body into main content and optional metadata text."""
    if "[" not in content:
        return content.strip(), None

    main_part, raw_metadata = content.split("[", 1)
    metadata_part = raw_metadata.rstrip("]").strip()
    return main_part.strip(), metadata_part

# ==== Parser ====


def parse_metadata(raw: str | None) -> dict[str, str]:
    """Parse metadata like 'zone=restricted color=red'."""
    if raw is None or not raw:
        return {}

    metadata: dict[str, str] = {}
    for token in raw.split():
        key, value = token.split("=", 1)
        metadata[key] = value
    return metadata


def parse_nb_drones(line: str) -> int:
    """Parse the nb_drones line."""
    _, value = line.split(":", 1)
    return int(value.strip())


def parse_zone_line(line: str, prefix: str) -> ParsedZoneRecord:
    """
    start_hub/hub/end_hubをパースし、Zoneを記録
    """
    _, content = line.split(":", 1)
    main_part, raw_metadata = split_main_and_metadata(content)
    tokens = main_part.split()

    name = tokens[0]
    x = int(tokens[1])
    y = int(tokens[2])
    metadata = parse_metadata(raw_metadata)

    return ParsedZoneRecord(
        prefix=prefix,
        name=name,
        x=x,
        y=y,
        metadata=metadata,
    )


def parse_connection_line(line: str) -> ParsedConnectionRecord:
    """
    connectionをパースし、インスタンスを作成
    """
    _, content = line.split(":", 1)
    main_part, raw_metadata = split_main_and_metadata(content)
    zone_a, zone_b = main_part.split("-", 1)
    metadata = parse_metadata(raw_metadata)

    return ParsedConnectionRecord(
        zone_a=zone_a.strip(),
        zone_b=zone_b.strip(),
        metadata=metadata,
    )


def parse_lines(lines: list[str]) -> ParsedMapData:
    """Turn cleaned lines into raw parsed records."""
    parsed_data = ParsedMapData()

    for raw_line in lines:
        line = clean_line(raw_line)
        if not line:
            continue

        if line.startswith("nb_drones:"):
            parsed_data.nb_drones = parse_nb_drones(line)
        elif line.startswith("start_hub:"):
            zone_record = parse_zone_line(line, "start_hub")
            parsed_data.start_hub_name = zone_record.name
            parsed_data.zones.append(zone_record)
        elif line.startswith("end_hub:"):
            zone_record = parse_zone_line(line, "end_hub")
            parsed_data.end_hub_name = zone_record.name
            parsed_data.zones.append(zone_record)
        elif line.startswith("hub:"):
            parsed_data.zones.append(parse_zone_line(line, "hub"))
        elif line.startswith("connection:"):
            parsed_data.connections.append(parse_connection_line(line))
        else:
            raise ValueError(f"Unsupported line format: {line}")

    return parsed_data

# ==== Building specific graph settings ====


def build_graph(parsed_data: ParsedMapData) -> Graph:
    """Build a Graph from parsed raw records."""
    graph = Graph(
        start_hub_name=parsed_data.start_hub_name,
        end_hub_name=parsed_data.end_hub_name,
    )

    for zone_record in parsed_data.zones:
        zone_type_raw = zone_record.metadata.get("zone", "normal").upper()
        zone_type = ZoneType[zone_type_raw]
        color = zone_record.metadata.get("color", "white")
        max_drones = int(zone_record.metadata.get("max_drones", "1"))

        zone = Zone(
            name=zone_record.name,
            x=zone_record.x,
            y=zone_record.y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
        )
        graph.add_zone(zone)

    for connection_record in parsed_data.connections:
        connection_name = (
            f"{connection_record.zone_a}-{connection_record.zone_b}"
        )
        max_link_capacity = int(
            connection_record.metadata.get("max_link_capacity", "1")
        )

        connection = Connection(
            connection_name=connection_name,
            zone_a=connection_record.zone_a,
            zone_b=connection_record.zone_b,
            max_link_capacity=max_link_capacity,
        )
        graph.add_connection(connection)

    return graph


def build_initial_state(graph: Graph, nb_drones: int) -> SimulationState:
    """ドローンとマップの初期化を行い、一番最初の状態を作る"""
    drones: list[Drone] = []
    start_hub_name = graph.start_hub_name

    for drone_id in range(1, nb_drones + 1):
        drones.append(
            Drone(
                drone_id=drone_id,
                status=DroneStatus.AT_ZONE,
                current_zone=start_hub_name,
                target_zone=None,
                current_connection=None,
                remaining_travel_turns=0,
            )
        )

    zone_occupancy = {zone_name: set()
                      for zone_name in graph.zones}
    for drone in drones:
        zone_occupancy[start_hub_name].add(drone.drone_id)

    connection_occupancy = {
        connection.connection_name: set()
        for connection in graph.connections
    }

    return SimulationState(
        current_turn_number=0,
        drones=drones,
        zone_occupancy=zone_occupancy,
        connection_occupancy=connection_occupancy,
    )


def parse_map_file(path: str) -> tuple[int, Graph, SimulationState]:
    """Read, parse, and build the initial simulation objects."""
    lines = read_input_file(path)
    parsed_data = parse_lines(lines)

    if parsed_data.nb_drones is None:
        raise ValueError("nb_drones is missing")

    graph = build_graph(parsed_data)
    state = build_initial_state(graph, parsed_data.nb_drones)
    return parsed_data.nb_drones, graph, state
