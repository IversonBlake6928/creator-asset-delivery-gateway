"""Business decision for digital-asset delivery."""

from typing import Any

from .models import DeliveryRequest, DeliveryResult


class DeliveryService:
    def __init__(self, processor: Any) -> None:
        self._processor = processor

    def prepare(self, request: DeliveryRequest) -> DeliveryResult:
        include_update = request.subscriber.updates_enabled
        delivery_text = self._processor.prepare_delivery_text(
            request_id=request.request_id,
            subscriber_name=request.subscriber.name,
            asset_title=request.asset.title,
            download_url=str(request.asset.download_url),
            release_note=request.asset.release_note if include_update else None,
        )
        return DeliveryResult(
            request_id=request.request_id,
            status="delivery_prepared",
            update_included=include_update,
            delivery_text=delivery_text,
        )
