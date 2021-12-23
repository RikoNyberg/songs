from typing import Any
import datetime
from pydantic import BaseModel, validator, constr, Field
from typing_extensions import Annotated

from pydantic.types import confloat, conint

from db.schemas.helpers import PyObjectId


class SongBase(BaseModel):
    artist: constr(min_length=1, max_length=50)
    title: constr(min_length=1, max_length=100)
    difficulty: confloat(gt=0, le=100)
    level: conint(gt=0, le=100)


class SongCreate(SongBase):
    released: datetime.datetime

    # validation
    @validator("released")
    def ensure_date_range(cls: Any, released: datetime.date):
        if datetime.datetime.now() < released:
            raise ValueError("Released date can not be in the future")
        return released


class SongInDB(SongCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
