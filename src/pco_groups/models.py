from pydantic import BaseModel, Field, field_validator

class GroupRow(BaseModel):
    name: str
    group_type: str
    description: str | None = None
    leader_name: str | None = None
    campus: str | None = None
    tag_1: str | None = None
    tag_2: str | None = None
    location_name: str | None = None
    street_address: str | None = None
    admin_alert_days: int | None = Field(default=None, ge=0)
    meeting_frequency: str | None = None
    meeting_day: str | None = None
    start_hour: str | None = None
    start_minute: str | None = None
    start_ampm: str | None = None
    end_hour: str | None = None
    end_minute: str | None = None
    end_ampm: str | None = None

    @field_validator("start_hour", "end_hour", mode="before")
    @classmethod
    def coerce_hour(cls, v):
        if v is None:
            return None
        return str(v).strip()

    @field_validator("start_minute", "end_minute", mode="before")
    @classmethod
    def coerce_minute(cls, v):
        if v is None:
            return None
        return str(v).strip().zfill(2)