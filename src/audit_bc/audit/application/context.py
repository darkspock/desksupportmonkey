from contextvars import ContextVar
from typing import Optional

audit_changes: ContextVar[Optional[dict]] = ContextVar(
    "audit_changes", default=None
)
audit_action_override: ContextVar[Optional[str]] = ContextVar(
    "audit_action_override", default=None
)
