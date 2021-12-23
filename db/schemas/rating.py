from typing import List
from pydantic import BaseModel, Field
from pydantic.types import conint
from db.schemas.helpers import PyObjectId

class RatingInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    song_id: PyObjectId = Field(default_factory=PyObjectId)
    rating: int
