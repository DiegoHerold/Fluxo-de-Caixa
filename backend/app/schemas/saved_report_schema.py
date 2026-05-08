from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.report_indicator_schema import ReportIndicatorEvaluation, ReportIndicatorRead


class SavedReportIndicatorPayload(BaseModel):
    indicator_id: int
    position: int = 0


class SavedReportBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str | None = None
    is_default_dashboard: bool = False
    is_active: bool = True
    display_order: int = 100


class SavedReportCreate(SavedReportBase):
    indicators: list[SavedReportIndicatorPayload] = Field(default_factory=list)


class SavedReportUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_default_dashboard: bool | None = None
    is_active: bool | None = None
    display_order: int | None = None
    indicators: list[SavedReportIndicatorPayload] | None = None


class SavedReportRead(SavedReportBase):
    id: int
    indicators: list[ReportIndicatorRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedReportEvaluation(BaseModel):
    id: int
    name: str
    description: str | None
    is_default_dashboard: bool
    indicators: list[ReportIndicatorEvaluation]
