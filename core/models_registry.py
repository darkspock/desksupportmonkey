"""
SQLAlchemy Models Registry

This module imports all SQLAlchemy models to ensure they're loaded
before mapper configuration. This prevents "failed to locate name"
errors when models have bidirectional relationships.

Import this module early in the application startup to ensure
all models are registered with SQLAlchemy's mapper.
"""

# Company BC
from src.company_bc.company.infrastructure.models import CompanyModel  # noqa: F401
from src.company_bc.company.infrastructure.models import CompanyEmailDomainModel  # noqa: F401
from src.company_bc.company.infrastructure.models import ProcessedStripeEventModel  # noqa: F401
from src.company_bc.department.infrastructure.models import DepartmentModel  # noqa: F401
from src.company_bc.employee_role.infrastructure.models import EmployeeRoleModel  # noqa: F401
from src.company_bc.equipment_profile.infrastructure.models import EquipmentProfileModel  # noqa: F401
from src.company_bc.equipment_profile.infrastructure.models import EquipmentProfileItemModel  # noqa: F401
from src.company_bc.classification_config.infrastructure.models import ClassificationConfigModel  # noqa: F401
from src.company_bc.nav_config.infrastructure.models import NavConfigModel  # noqa: F401
from src.company_bc.sla_escalation_config.infrastructure.models import SlaEscalationConfigModel  # noqa: F401
from src.company_bc.assignment_config.infrastructure.models import *  # noqa: F401, F403

# Auth BC
from src.auth_bc.user.infrastructure.models import UserModel  # noqa: F401
from src.auth_bc.magic_link.infrastructure.models import MagicLinkModel  # noqa: F401
# Asset BC
from src.asset_bc.asset.infrastructure.models import AssetModel  # noqa: F401
from src.asset_bc.asset.infrastructure.models import AssetEventModel  # noqa: F401
from src.asset_bc.asset.infrastructure.models import AssetLocationModel  # noqa: F401
from src.asset_bc.asset.infrastructure.models import CIRelationshipModel  # noqa: F401
from src.asset_bc.checkout.infrastructure.models import AssetCheckoutModel  # noqa: F401
from src.asset_type_bc.definition.infrastructure.models import AssetTypeDefinitionModel  # noqa: F401

# Request BC
from src.request_bc.request.infrastructure.models import ServiceRequestModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestEventModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestCommentModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestNoteModel  # noqa: F401

# Notification BC
from src.notification_bc.notification.infrastructure.models import NotificationModel  # noqa: F401

# Report BC
from src.report_bc.report.infrastructure.models import ReportModel  # noqa: F401

# MCP BC
from src.mcp_bc.server.infrastructure.models import ApiKeyModel  # noqa: F401

# Procurement BC
from src.procurement_bc.vendor.infrastructure.models import VendorModel  # noqa: F401
from src.procurement_bc.vendor.infrastructure.models import VendorContractModel  # noqa: F401
from src.procurement_bc.vendor.infrastructure.models import VendorContractDocumentModel  # noqa: F401
from src.procurement_bc.vendor.infrastructure.models import VendorRiskAssessmentModel  # noqa: F401
from src.procurement_bc.vendor.infrastructure.models import VendorDependencyModel  # noqa: F401
from src.procurement_bc.purchase_order.infrastructure.models import PurchaseOrderModel  # noqa: F401
from src.procurement_bc.purchase_order.infrastructure.models import PurchaseOrderItemModel  # noqa: F401
from src.procurement_bc.purchase_order.infrastructure.models import PurchaseOrderRequestModel  # noqa: F401
from src.procurement_bc.budget.infrastructure.models import DepartmentBudgetModel  # noqa: F401

# Appointment BC
from src.appointment_bc.appointment.infrastructure.models import AppointmentModel  # noqa: F401

# Shipping BC
from src.shipping_bc.shipment.infrastructure.models import ShipmentModel  # noqa: F401
from src.shipping_bc.shipment.infrastructure.models import ShipmentItemModel  # noqa: F401
from src.shipping_bc.address.infrastructure.models import ShippingAddressModel  # noqa: F401

# Maintenance BC
from src.maintenance_bc.maintenance_template.infrastructure.models import MaintenanceTemplateModel  # noqa: F401
from src.maintenance_bc.maintenance_template.infrastructure.models import MaintenanceChecklistItemModel  # noqa: F401
from src.maintenance_bc.maintenance_template.infrastructure.models import MaintenancePlanModel  # noqa: F401
from src.maintenance_bc.maintenance_record.infrastructure.models import MaintenanceRecordModel  # noqa: F401

# Incident BC
from src.incident_bc.incident.infrastructure.models import SecurityIncidentModel  # noqa: F401
from src.incident_bc.incident.infrastructure.models import IncidentTimelineModel  # noqa: F401
from src.incident_bc.incident.infrastructure.models import IncidentAssetModel  # noqa: F401
from src.incident_bc.incident.infrastructure.models import IncidentVendorModel  # noqa: F401
from src.incident_bc.incident.infrastructure.models import RegulatoryReportModel  # noqa: F401
from src.incident_bc.incident.infrastructure.models import PostMortemModel  # noqa: F401

# Risk BC
from src.risk_bc.risk.infrastructure.models import RiskModel  # noqa: F401
from src.risk_bc.risk.infrastructure.models import MitigationPlanModel  # noqa: F401
from src.risk_bc.risk.infrastructure.models import RiskLinkModel  # noqa: F401
from src.risk_bc.risk.infrastructure.models import RiskHistoryModel  # noqa: F401

# Change BC
from src.change_bc.change_request.infrastructure.models import ChangeRequestModel  # noqa: F401
from src.change_bc.change_request.infrastructure.models import ChangeEventModel  # noqa: F401
from src.change_bc.change_request.infrastructure.models import ChangeAssetModel  # noqa: F401
from src.change_bc.change_request.infrastructure.models import PostImplementationReviewModel  # noqa: F401

# Vulnerability BC
from src.vulnerability_bc.vulnerability.infrastructure.models import VulnerabilityModel  # noqa: F401
from src.vulnerability_bc.vulnerability.infrastructure.models import VulnerabilityEventModel  # noqa: F401
from src.vulnerability_bc.vulnerability.infrastructure.models import VulnerabilityAssetModel  # noqa: F401

# KB BC
from src.kb_bc.article.infrastructure.models import ArticleCategoryModel  # noqa: F401
from src.kb_bc.article.infrastructure.models import ArticleModel  # noqa: F401
from src.kb_bc.article.infrastructure.models import ArticleVersionModel  # noqa: F401

# SLA BC
from src.sla_bc.sla.infrastructure.models import SlaPolicyModel  # noqa: F401
from src.sla_bc.sla.infrastructure.models import SlaBreachRecordModel  # noqa: F401

# Audit BC
from src.audit_bc.audit.infrastructure.models import AuditEntryModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import ComplianceControlModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import GdprRequestModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import RetentionPolicyModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import ComplianceAssessmentModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import ComplianceEvidenceModel  # noqa: F401
from src.audit_bc.audit.infrastructure.models import AuditEntryTagModel  # noqa: F401

# Custom Field BC
from src.custom_field_bc.definition.infrastructure.models import CustomFieldDefinitionModel  # noqa: F401

# Workflow BC
from src.workflow_bc.template.infrastructure.models import WorkflowTemplateModel  # noqa: F401
from src.workflow_bc.template.infrastructure.models import WorkflowSubtypeModel  # noqa: F401
from src.workflow_bc.template.infrastructure.models import ChecklistItemDefinitionModel  # noqa: F401
from src.workflow_bc.checklist.infrastructure.models import RequestChecklistItemModel  # noqa: F401
