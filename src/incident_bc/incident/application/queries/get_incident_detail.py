from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class TimelineEntryDto:
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    created_at: Optional[datetime]
    metadata: Optional[dict]


@dataclass
class ReportDto:
    id: str
    report_type: str
    status: str
    deadline_at: Optional[datetime]
    generated_at: Optional[datetime]
    submitted_at: Optional[datetime]


@dataclass
class IncidentAssetDto:
    asset_id: str
    asset_name: str
    asset_type: Optional[str]
    impact_description: Optional[str]


@dataclass
class IncidentVendorDto:
    vendor_id: str
    vendor_name: str
    involvement_description: Optional[str]


@dataclass
class PostMortemDto:
    id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by: str
    created_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class IncidentDetailDto:
    id: str
    title: str
    description: str
    incident_type: str
    severity: str
    status: str
    attack_vector: Optional[str]
    data_breach_scope: Optional[str]
    reported_by: str
    reported_by_name: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    detected_at: Optional[datetime]
    close_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    timeline: list[TimelineEntryDto] = field(default_factory=list)
    reports: list[ReportDto] = field(default_factory=list)
    assets: list[IncidentAssetDto] = field(default_factory=list)
    vendors: list[IncidentVendorDto] = field(default_factory=list)
    postmortem: Optional[PostMortemDto] = None


@dataclass
class GetIncidentDetailQuery(Query):
    incident_id: str
    company_id: str


class GetIncidentDetailQueryHandler(
    QueryHandler[GetIncidentDetailQuery, IncidentDetailDto]
):
    def __init__(
        self,
        incident_repo: IncidentRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
        asset_reader: Optional[Any] = None,
        vendor_reader: Optional[Any] = None,
    ):
        self.incident_repo = incident_repo
        self.user_name_resolver = user_name_resolver
        self.asset_reader = asset_reader
        self.vendor_reader = vendor_reader

    def handle(self, query: GetIncidentDetailQuery) -> IncidentDetailDto:
        incident = self.incident_repo.find_by_id(
            query.incident_id, query.company_id
        )
        if not incident:
            raise IncidentNotFoundError(query.incident_id)

        timeline_entries = self.incident_repo.find_timeline(incident.id)
        reports = self.incident_repo.find_reports_by_incident(incident.id)
        assets = self.incident_repo.find_assets_by_incident(incident.id)
        vendors = self.incident_repo.find_vendors_by_incident(incident.id)
        postmortem = self.incident_repo.find_postmortem_by_incident(incident.id)

        # Resolve user names
        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {incident.reported_by}
            if incident.assigned_to:
                user_ids.add(incident.assigned_to)
            for entry in timeline_entries:
                user_ids.add(entry.actor_id)
            name_map = self.user_name_resolver(list(user_ids))

        timeline_dtos = [
            TimelineEntryDto(
                id=e.id,
                event_type=e.event_type.value,
                description=e.description,
                actor_id=e.actor_id,
                actor_name=name_map.get(e.actor_id),
                created_at=e.created_at,
                metadata=e.metadata,
            )
            for e in timeline_entries
        ]

        report_dtos = [
            ReportDto(
                id=r.id,
                report_type=r.report_type.value if hasattr(r.report_type, 'value') else r.report_type,
                status=r.status.value if hasattr(r.status, 'value') else r.status,
                deadline_at=r.deadline_at,
                generated_at=r.generated_at,
                submitted_at=r.submitted_at,
            )
            for r in reports
        ]

        # Enrich assets with names from asset_bc
        asset_dtos: list[IncidentAssetDto] = []
        for a in assets:
            asset_name = a.get("asset_id", "")
            asset_type = None
            if self.asset_reader:
                asset_obj = self.asset_reader.find_by_id(
                    a["asset_id"], incident.company_id
                )
                if asset_obj:
                    asset_name = getattr(asset_obj, "brand", "") + " " + getattr(asset_obj, "model", "")
                    asset_name = asset_name.strip() or a["asset_id"]
                    asset_type_val = getattr(asset_obj, "type", None)
                    asset_type = asset_type_val.value if asset_type_val is not None and hasattr(asset_type_val, "value") else asset_type_val
            asset_dtos.append(
                IncidentAssetDto(
                    asset_id=a["asset_id"],
                    asset_name=asset_name,
                    asset_type=asset_type,
                    impact_description=a.get("impact_description"),
                )
            )

        # Enrich vendors with names from procurement_bc
        vendor_dtos: list[IncidentVendorDto] = []
        for v in vendors:
            vendor_name = v.get("vendor_id", "")
            if self.vendor_reader:
                vendor_obj = self.vendor_reader.find_by_id(
                    v["vendor_id"], incident.company_id
                )
                if vendor_obj:
                    vendor_name = getattr(vendor_obj, "name", v["vendor_id"])
            vendor_dtos.append(
                IncidentVendorDto(
                    vendor_id=v["vendor_id"],
                    vendor_name=vendor_name,
                    involvement_description=v.get("involvement_description"),
                )
            )

        # Enrich postmortem with creator name
        postmortem_dto: Optional[PostMortemDto] = None
        if postmortem:
            pm_creator_name = name_map.get(postmortem["created_by"])
            if not pm_creator_name and self.user_name_resolver and postmortem.get("created_by"):
                extra_map = self.user_name_resolver([postmortem["created_by"]])
                pm_creator_name = extra_map.get(postmortem["created_by"])
            postmortem_dto = PostMortemDto(
                id=postmortem["id"],
                root_cause=postmortem["root_cause"],
                lessons_learned=postmortem["lessons_learned"],
                corrective_actions=postmortem["corrective_actions"],
                created_by=postmortem["created_by"],
                created_by_name=pm_creator_name,
                created_at=postmortem.get("created_at"),
                updated_at=postmortem.get("updated_at"),
            )

        return IncidentDetailDto(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            incident_type=incident.incident_type.value,
            severity=incident.severity.value,
            status=incident.status.value,
            attack_vector=incident.attack_vector,
            data_breach_scope=incident.data_breach_scope,
            reported_by=incident.reported_by,
            reported_by_name=name_map.get(incident.reported_by),
            assigned_to=incident.assigned_to,
            assigned_to_name=name_map.get(incident.assigned_to) if incident.assigned_to else None,
            detected_at=incident.detected_at,
            close_reason=incident.close_reason,
            closed_at=incident.closed_at,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            timeline=timeline_dtos,
            reports=report_dtos,
            assets=asset_dtos,
            vendors=vendor_dtos,
            postmortem=postmortem_dto,
        )
