from typing import Optional

from src.request_bc.request.domain.enums import RequestPriority


TYPE_WEIGHTS: dict[str, int] = {
    "incident": 2,
    "repair": 1,
    "onboarding": 1,
    "new_equipment": 0,
    "configuration": 0,
    "access_request": 0,
}

SUBTYPE_WEIGHTS: dict[str, int] = {
    "security": 1,
    "hardware": 1,
}

ROLE_WEIGHTS: dict[str, int] = {
    "admin": 1,
    "super_admin": 1,
}


class PriorityScorer:
    def compute(
        self,
        request_type: str,
        subtype: Optional[str],
        department_priority_weight: int,
        user_role: str,
        ai_priority_hint: int = 0,
    ) -> tuple[RequestPriority, dict]:
        type_w = TYPE_WEIGHTS.get(request_type, 0)
        subtype_w = SUBTYPE_WEIGHTS.get(subtype, 0) if subtype else 0
        dept_w = department_priority_weight
        role_w = ROLE_WEIGHTS.get(user_role, 0)
        ai_hint_w = ai_priority_hint
        # Business rule: early-start computer provisioning is operationally urgent.
        # When AI flags urgency on new equipment/computer requests, boost it so
        # critical language ("starts tomorrow", "cannot work") can reach URGENT.
        if (
            request_type == "new_equipment"
            and subtype == "computer"
            and ai_hint_w > 0
        ):
            ai_hint_w += 2

        raw_score = type_w + subtype_w + dept_w + role_w + ai_hint_w

        if raw_score >= 4:
            priority = RequestPriority.URGENT
        elif raw_score >= 3:
            priority = RequestPriority.HIGH
        elif raw_score >= 2:
            priority = RequestPriority.MEDIUM
        else:
            priority = RequestPriority.LOW

        breakdown = {
            "type_weight": type_w,
            "subtype_weight": subtype_w,
            "department_weight": dept_w,
            "role_weight": role_w,
            "ai_hint_weight": ai_hint_w,
            "raw_score": raw_score,
        }
        return priority, breakdown
