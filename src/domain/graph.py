from pydantic import BaseModel, Field
from .zone import Zone
from .connection import Connection


class Graph(BaseModel):
    """
    Graph owns the full list of connections and adjacency
    zones (handle them with to mention it by its name):
    {
        "start": Zone(),
        "roof1": Zone(),
        "goal": Zone()
    }

    connections (handle them with list since thet aren't have name):
    [
        Connection(zone_a="start", zone_b="roof1", ...),
        Connection(zone_a="roof1", zone_b="goal", ...),
    ]

    adjacency (handle it with dict to mention it by its name)
    this dict contains information of connection for each zones
    {
        "start": [Connection(start-roof1)],
        "roof1": [Connection(start-roof1), Connection(roof1-goal)],
        "goal": [Connection(roof1-goal)],
    }
    """
    zones: dict[str, Zone] = Field(default_factory=dict)
    connections: list[Connection] = Field(default_factory=list)
    adjacency: dict[str, list[Connection]] = Field(default_factory=dict)
    start_hub_name: str | None = None
    end_hub_name: str | None = None

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone
        if zone.name not in self.adjacency:
            self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
        self.adjacency[connection.zone_a].append(connection)
        self.adjacency[connection.zone_b].append(connection)

    # ==== get zone and connection ====

    def get_zone(self, name: str) -> Zone:
        return self.zones[name]

    def get_connection(self, zone_a: str, zone_b: str) -> Connection:
        for connection in self.adjacency[zone_a]:
            if connection.other_end(zone_a) == zone_b:
                return connection
        raise ValueError("could not get connection")

    # ==== define neighbor zones and connectinos ====

    def neighbor_connections(self, zone_name: str) -> list[Connection]:
        return self.adjacency[zone_name]

    def neighbor_zones(self, zone_name: str) -> list[str]:
        result = []
        adjacent_connection = self.neighbor_connections(zone_name)
        for connection in adjacent_connection:
            result.append(connection.other_end(zone_name))
        return result
