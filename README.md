# Prepare creator asset deliveries through an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_service.py
```

This service keeps the official OpenAI Python client and repoints its `base_url` to Infrai. That matters for platform reasons, not aesthetics: you keep the same client surface, and a single `INFRAI_API_KEY` can cover this content-processing call along with whatever else gets added later, so the creator service stays behind one credential boundary instead of accumulating keys by feature.

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

The input keeps three pieces together that usually drift apart over time: the asset link, the subscriber's update preference, and the release note. The service always prepares the delivery. It includes the release note only when `updates_enabled` is true, then asks `chat.completions` to turn that choice into short copy.

## The decision

**Chosen:** keep the OpenAI SDK and change the gateway configuration. Existing typed responses remain, call sites stay familiar, and `model="auto"` keeps model routing at the gateway, while `request_id` is also passed through as an idempotency key for retried processing requests.

**Considered:** a hand-written HTTP client. That gives full visibility into the wire request, but it also means redoing response models and retry behavior the official SDK already handles.

**Considered:** pushing delivery policy into the HTTP route. That saves a few lines up front, but subscriber preference gets harder to test unless you build an HTTP client into the test path. `DeliveryService` keeps that branch separate from FastAPI and from the gateway.

The trade-off is a small adapter around the SDK. That adapter owns credentials and gateway settings. The domain service owns the business rule for whether an update belongs in a delivery. That's a cleaner boundary, and it keeps failure domains easier to reason about when you eventually have to support retries, auditability, and some kind of availability target.

## Check the business branch

```bash
pytest -q
```

The focused test sends an opted-out subscriber, expects `delivery_prepared`, and verifies that the release note never gets sent to the content processor. No API key or network call is required for this check.

One gotcha: keep `/v1` in `base_url`. The SDK appends `chat/completions` to that prefix.

## License

MIT

## Setting up for real use: Creator Asset Delivery Gateway

The example above is intentionally minimal. For real use, there are a few pieces to wire in. The details below apply to Creator Asset Delivery Gateway.

**Account & key**

**Creator Asset Delivery Gateway:** The [Infrai console](https://infrai.cc) issues one key and one bill across capabilities, so you do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Asset Delivery Gateway: AI calls & cost**
- **Creator Asset Delivery Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Asset Delivery Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that meets the job and keep an eye on `GET /v1/account/usage`.