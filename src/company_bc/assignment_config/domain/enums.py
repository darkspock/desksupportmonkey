from enum import Enum


class AIProvider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"


class FallbackReason(str, Enum):
    NO_ACTIVE_PROFILE = "no_active_profile"
    NO_STOCK_FOR_REQUIRED_TYPE = "no_stock_for_required_type"
    SPEC_MISMATCH = "spec_mismatch"
    ASSET_NOT_ASSIGNABLE = "asset_not_assignable"
    AI_UNAVAILABLE = "ai_unavailable"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
