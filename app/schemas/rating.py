from enum import Enum
from pydantic import BaseModel
from pydantic.types import conint


class RatingGet(BaseModel):
    average_rating: float
    lowest_rating: int
    highest_rating: int


class RatingPostConfirmationResultEnum(str, Enum):
    SUCCESSFUL = "Rating added successfully"


class RatingPostConfirmation(BaseModel):
    result: RatingPostConfirmationResultEnum


class RatingValidator(BaseModel):
    rating: conint(ge=1, le=5)
