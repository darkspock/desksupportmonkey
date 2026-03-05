from enum import Enum


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ATTRIBUTED = "attributed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
