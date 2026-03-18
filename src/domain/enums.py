from enum import Enum, auto


class ZoneType(Enum):
    NORMAL = auto()
    BLOCKED = auto()
    RESTRICTED = auto()
    PRIORITY = auto()


class DroneStatus(Enum):
    """
    AT_ZONE: The drone is currently standing in a zone and may act this turn.
    IN_RESTRICTED_TRANSIT: The drone is traveling through a connection toward a restricted zone.
    DELIVERED: The drone has reached the end hub and no longer needs to move.
    """
    AT_ZONE = auto()
    IN_RESTRICTED_TRANSIT = auto()
    DELIVERED = auto()
