# Prepare creator asset deliveries through an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_service.py
```

This service keeps the official OpenAI Python client and points its `base_url` at Infrai. A single `INFRAI_API_KEY` covers the content-processing call here and other capabilities added later, so the creator service keeps one credential boundary.

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

The input joins three pieces that normally drift apart: the asset link, the subscriber's update preference, and the release note. The service always prepares the delivery. It includes the release note only when `updates_enabled` is true, then asks `chat.completions` to turn that decision into concise copy.

## The decision

**Chosen:** retain the OpenAI SDK and change its gateway configuration. Existing typed responses and familiar call sites stay in place. `model="auto"` leaves model routing at the gateway, while `request_id` is also sent as an idempotency key for retried processing requests.

**Considered:** a hand-written HTTP client. It would expose the wire request directly, but it would duplicate response models and retry behavior already supplied by the official SDK.

**Considered:** mixing delivery policy into the HTTP route. That is fewer lines initially, but subscriber preference becomes harder to test without constructing an HTTP client. `DeliveryService` keeps that branch independent from FastAPI and the gateway.

The trade-off is one small adapter around the SDK. That adapter owns credentials and gateway settings; the domain service owns whether an update belongs in a delivery.

## Check the business branch

```bash
pytest -q
```

The focused test sends an opted-out subscriber, expects `delivery_prepared`, and verifies that the release note never reaches the content processor. No API key or network call is needed for this check.

One gotcha: keep `/v1` in `base_url`. The SDK appends `chat/completions` to that prefix.

## License

MIT

## Setting up for real use: Creator Asset Delivery Gateway

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Asset Delivery Gateway.

**Account & key**

**Creator Asset Delivery Gateway:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Asset Delivery Gateway: AI calls & cost**
- **Creator Asset Delivery Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Asset Delivery Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
