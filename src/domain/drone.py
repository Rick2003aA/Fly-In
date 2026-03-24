from pydantic import BaseModel, Field
from .enums import DroneStatus

"""
There are some elements which are unneccessary depending on drone status
"""


class Drone(BaseModel):
    """
    Represents one drone in the simulation.

    Field meaning:
    - drone_id: Stable identifier for the drone.
    - status: Current simulation status of the drone.
    - current_zone: Zone where the drone is currently located.
    - target_zone: Destination zone when the drone is in restricted transit.
    - current_connection: Connection currently occupied during restricted transit.
    - remaining_travel_turns: Number of turns left before the drone finishes travel.

    Status invariants:
    - AT_ZONE:
      - current_zone must be set.
      - target_zone must be None.
      - current_connection must be None.
      - remaining_travel_turns must be 0.

    - IN_RESTRICTED_TRANSIT:
      - current_zone must be None.
      - target_zone must be set.
      - current_connection must be set.
      - remaining_travel_turns must be 1.

    - DELIVERED:
      - current_zone should be the end hub name.
      - target_zone must be None.
      - current_connection must be None.
      - remaining_travel_turns must be 0.
    """

    drone_id: int
    status: DroneStatus
    current_zone: str | None
    target_zone: str | None
    current_connection: str | None
    remaining_travel_turns: int = Field(default=0)
