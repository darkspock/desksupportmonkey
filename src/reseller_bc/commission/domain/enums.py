from enum import Enum


class CommissionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CLAWED_BACK = "clawed_back"
