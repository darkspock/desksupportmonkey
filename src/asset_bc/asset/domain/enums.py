from enum import Enum


class SystemLocation(str, Enum):
    IN_TRANSIT = "in_transit"
    MAIN_WAREHOUSE = "main_warehouse"


class AssetStatus(str, Enum):
    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    IN_REPAIR = "in_repair"
    DECOMMISSIONED = "decommissioned"


# in_stock <-> assigned transitions handled by F1 assign/unassign commands
VALID_TRANSITIONS: dict[AssetStatus, list[AssetStatus]] = {
    AssetStatus.IN_STOCK: [AssetStatus.IN_REPAIR, AssetStatus.DECOMMISSIONED],
    AssetStatus.ASSIGNED: [AssetStatus.IN_REPAIR, AssetStatus.DECOMMISSIONED],
    AssetStatus.IN_REPAIR: [AssetStatus.IN_STOCK, AssetStatus.DECOMMISSIONED],
    AssetStatus.DECOMMISSIONED: [],
}


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: AssetStatus, target: AssetStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current.value} to {target.value}")
