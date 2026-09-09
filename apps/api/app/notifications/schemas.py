from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    user_id: str
    type: str
    title: str
    description: str
    source: str
    source_reference: str | None
    rule_id: str
    priority: int
    severity: str
    subject_id: str | None
    period_start: date | None
    period_end: date | None
    dedupe_key: str
    evidence: dict[str, Any]
    channel: str
    read_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread: int


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    smart_notifications_enabled: bool
    budget_alert_enabled: bool
    anomaly_alert_enabled: bool
    recurring_reminder_enabled: bool
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    max_notifications_per_day: int


class NotificationPreferenceUpdate(BaseModel):
    smart_notifications_enabled: bool | None = None
    budget_alert_enabled: bool | None = None
    anomaly_alert_enabled: bool | None = None
    recurring_reminder_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    max_notifications_per_day: int | None = Field(default=None, ge=1, le=100)

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is not None:
            hour, minute = value.split(":")
            if len(value) != 5 or not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError("Quiet hours must use HH:MM")
        return value


class NotificationEventCreate(BaseModel):
    event_type: str = Field(pattern="^(DELIVERY|OPEN|READ|ACTION)$")
    result: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
