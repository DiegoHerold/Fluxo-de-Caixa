from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DashboardWidgetType
from app.schemas.report_indicator_schema import ReportIndicatorEvaluation


class DashboardWidgetBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    widget_type: DashboardWidgetType = DashboardWidgetType.indicator
    indicator_id: int | None = None
    saved_report_id: int | None = None
    position: int = 100
    width: int = Field(default=1, ge=1, le=3)
    height: int = Field(default=1, ge=1, le=3)
    notes: str | None = None
    is_active: bool = True


class DashboardWidgetCreate(DashboardWidgetBase):
    pass


class DashboardWidgetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    widget_type: DashboardWidgetType | None = None
    indicator_id: int | None = None
    saved_report_id: int | None = None
    position: int | None = None
    width: int | None = Field(default=None, ge=1, le=3)
    height: int | None = Field(default=None, ge=1, le=3)
    notes: str | None = None
    is_active: bool | None = None


class DashboardWidgetRead(DashboardWidgetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardWidgetEvaluation(DashboardWidgetRead):
    indicator: ReportIndicatorEvaluation | None = None
    export_url: str | None = None
