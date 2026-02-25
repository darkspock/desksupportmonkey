from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class WorkflowTemplateModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "workflow_templates"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    require_all_complete: Mapped[bool] = mapped_column(Boolean, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_workflow_templates_company_name"),
        Index("ix_workflow_templates_company", "company_id"),
    )


class WorkflowSubtypeModel(ULIDMixin, Base):
    __tablename__ = "workflow_subtypes"

    template_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")

    __table_args__ = (
        UniqueConstraint("template_id", "name", name="uq_workflow_subtypes_template_name"),
        Index("ix_workflow_subtypes_template", "template_id"),
    )


class ChecklistItemDefinitionModel(ULIDMixin, Base):
    __tablename__ = "checklist_item_definitions"

    template_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee_role: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    is_required: Mapped[bool] = mapped_column(Boolean, server_default="true")

    __table_args__ = (
        Index("ix_checklist_item_definitions_template", "template_id"),
    )
