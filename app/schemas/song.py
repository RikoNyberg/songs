from pydantic.main import BaseModel
from db.schemas.song import SongCreate, SongInDB

class SongGet(SongCreate):
    id: str

class SongsAverageDifficultyGet(BaseModel):
    average_difficulty: float