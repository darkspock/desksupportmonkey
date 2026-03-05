from enum import Enum


class ClientSource(str, Enum):
    MANUAL = "manual"
    REFERRAL = "referral"
    INVITATION = "invitation"
