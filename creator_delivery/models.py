"""Typed request and response models for asset delivery."""

from pydantic import BaseModel, Field, HttpUrl


class Subscriber(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    updates_enabled: bool


class DigitalAsset(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    download_url: HttpUrl
    release_note: str = Field(min_length=1, max_length=1000)


class DeliveryRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=80)
    subscriber: Subscriber
    asset: DigitalAsset


class DeliveryResult(BaseModel):
    request_id: str
    status: str
    update_included: bool
    delivery_text: str
