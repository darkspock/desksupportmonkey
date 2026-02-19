from enum import Enum


class EnforcementMode(str, Enum):
    WARN = "warn"
    STRICT = "strict"
