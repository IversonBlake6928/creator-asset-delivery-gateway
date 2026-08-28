from dataclasses import dataclass, field

from creator_delivery.delivery_service import DeliveryService
from creator_delivery.models import DeliveryRequest


@dataclass
class RecordingProcessor:
    calls: list[dict[str, object]] = field(default_factory=list)

    def prepare_delivery_text(self, **values: object) -> str:
        self.calls.append(values)
        return "Your brush pack is ready: https://downloads.example/brushes"


def test_opted_out_subscriber_gets_asset_without_release_update() -> None:
    processor = RecordingProcessor()
    service = DeliveryService(processor)
    request = DeliveryRequest.model_validate(
        {
            "request_id": "delivery-1042",
            "subscriber": {"name": "Mina", "updates_enabled": False},
            "asset": {
                "title": "Ink Brush Pack",
                "download_url": "https://downloads.example/brushes",
                "release_note": "Version 2 adds twelve grain textures.",
            },
        }
    )

    result = service.prepare(request)

    assert result.status == "delivery_prepared"
    assert result.update_included is False
    assert processor.calls[0]["release_note"] is None
    assert processor.calls[0]["request_id"] == "delivery-1042"
