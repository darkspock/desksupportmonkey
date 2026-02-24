from enum import Enum


class SlaBreachType(str, Enum):
    RESPONSE_WARNING = "response_warning"
    RESPONSE_BREACH = "response_breach"
    RESOLUTION_WARNING = "resolution_warning"
    RESOLUTION_BREACH = "resolution_breach"
