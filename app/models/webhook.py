"""Pydantic models for rubitime webhook payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

WebhookEvent = Literal[
    "event-create-record",
    "event-update-record",
    "event-remove-record",
]


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class WebhookRecordData(BaseModel):
    """Rubitime record payload embedded in the webhook."""

    model_config = ConfigDict(extra="allow")

    id: int
    parent_record: int | None = None
    whom: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    record: str | None = None
    name: str = ""
    price: int | None = None
    phone: str = ""
    email: str = ""
    comment: str = ""
    status: int | None = None
    status_title: str = ""
    cooperator_id: int | None = None
    cooperator_title: str = ""
    branch_id: int | None = None
    branch_title: str = ""
    service_id: int | None = None
    service_title: str = ""
    duration: int | None = None
    prepayment: int | None = None
    prepayment_date: str | None = None
    prepayment_url: str | None = None
    custom_field1: str = ""
    custom_field2: str = ""
    url: str = ""

    @field_validator("price", "status", "duration", "prepayment", mode="before")
    @classmethod
    def normalize_int_fields(cls, value: Any) -> int | None:
        return _coerce_int(value)


class WebhookPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    from_: str | None = Field(default=None, alias="from")
    event: WebhookEvent
    data: WebhookRecordData

    @field_validator("event", mode="before")
    @classmethod
    def normalize_event(cls, value: Any) -> str:
        return str(value).strip().lower()

    @property
    def record_id(self) -> int:
        return self.data.id
