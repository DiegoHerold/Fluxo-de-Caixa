from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountNature


class ChartAccountBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., min_length=2, max_length=160)
    parent_id: int | None = None
    account_nature: AccountNature
    is_active: bool = True


class ChartAccountCreate(ChartAccountBase):
    pass


class ChartAccountUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: Annotated[str | None, Field(default=None, max_length=32)] = None
    name: Annotated[str | None, Field(default=None, min_length=2, max_length=160)] = None
    parent_id: int | None = None
    account_nature: AccountNature | None = None
    is_active: bool | None = None


class ChartAccountRead(ChartAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChartAccountTree(ChartAccountRead):
    children: list["ChartAccountTree"] = Field(default_factory=list)
