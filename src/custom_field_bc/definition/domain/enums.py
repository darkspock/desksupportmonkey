from enum import Enum


class EntityType(str, Enum):
    ASSET = "asset"
    REQUEST = "request"
    INCIDENT = "incident"


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    FILE = "file"
