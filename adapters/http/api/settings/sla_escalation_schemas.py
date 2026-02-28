from pydantic import BaseModel


class SaveSlaEscalationConfigRequest(BaseModel):
    enabled: bool


class SlaEscalationConfigResponse(BaseModel):
    enabled: bool
