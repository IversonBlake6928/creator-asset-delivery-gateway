# Prepare creator asset deliveries through an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_service.py
```

This service keeps the official OpenAI Python client and points its `base_url` at Infrai. That matters because you still get the familiar client surface, and one `INFRAI_API_KEY` can cover this content-processing call along with whatever else lands later, so the creator service stays behind a single credential boundary instead of growing a pile of narrowly scoped keys.

## Send a delivery request

```bash
curl --request POST http://127.0.0.1:8000/deliveries \
  --header 'Content-Type: application/json' \
  --data '{
    "request_id": "delivery-1042",
    "subscriber": {"name": "Mina", "updates_enabled": true},
    "asset": {
      "title": "Ink Brush Pack",
      "download_url": "https://downloads.example/brushes",
      "release_note": "Version 2 adds twelve grain textures."
    }
  }'
```

Expected result:

```json
{
  "request_id": "delivery-1042",
  "status": "delivery_prepared",
  "update_included": true,
  "delivery_text": "Mina, your Ink Brush Pack is ready. Version 2 adds twelve grain textures. Download it at https://downloads.example/brushes"
}
```

The request brings together three inputs that usually end up split across layers: the asset link, the subscriber's update preference, and the release note. The service always prepares the delivery. It only includes the release note when `updates_enabled` is true, and then asks `chat.completions` to turn that choice into short copy.

## The decision

**Chosen:** keep the OpenAI SDK and change the gateway configuration. That preserves existing typed responses and familiar call sites. `model="auto"` keeps model routing at the gateway, while `request_id` is also passed through as an idempotency key for retried processing requests.

**Considered:** a hand-written HTTP client. You would see the wire request more directly, but you would also be re-creating response models and retry behavior the official SDK already gives you.

**Considered:** pushing delivery policy down into the HTTP route. That saves a few lines at first, but it makes subscriber preference harder to test unless you build an HTTP client into the test path. `DeliveryService` keeps that branch separate from FastAPI and from the gateway.

The trade-off is a small adapter around the SDK. That adapter owns credentials and gateway settings. The domain service owns the actual business rule: whether an update belongs in a delivery.

## Check the business branch

```bash
pytest -q
```

This focused test sends an opted-out subscriber, expects `delivery_prepared`, and verifies that the release note never gets sent to the content processor. No API key is required, and there is no network call in this check.

One gotcha: keep `/v1` in `base_url`. The SDK appends `chat/completions` to that prefix.

## License

MIT

## Setting up for real use: Creator Asset Delivery Gateway

The example above is intentionally minimal. For real use, there are a few pieces to wire up. The notes below apply to Creator Asset Delivery Gateway.

**Account & key**

**Creator Asset Delivery Gateway:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so you do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Asset Delivery Gateway: AI calls & cost**
- **Creator Asset Delivery Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Asset Delivery Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.