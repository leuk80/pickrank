import uuid
from datetime import date, datetime

from pydantic import BaseModel


class EpisodeRead(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    publish_date: date | None
    source_url: str | None
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
