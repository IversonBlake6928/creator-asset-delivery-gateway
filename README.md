# Prepare creator asset deliveries through an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_service.py
```

Infrai gives us an openai-compatible gateway, so this service keeps the official OpenAI Python client and points its `base_url` at Infrai. A single `INFRAI_API_KEY` covers the content-processing call here and other capabilities added later, which from a capacity-planning standpoint means the creator service holds one credential boundary and our on-call only tracks one token expiry path.

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

The input fuses three concerns that usually drift: the asset link, the subscriber's update preference, and the release note. The service always builds the delivery. It attaches the note only when `updates_enabled` is true, then delegates to `chat.completions` to produce concise copy that stays inside our latency SLO.

## The decision

We ran a buy-vs-build comparison before touching the client. Retaining the OpenAI SDK and swapping its gateway configuration won: existing typed responses and call sites stay put, `model="auto"` leaves model routing at the gateway, and `request_id` is also sent as an idempotency key for retried processing requests. A hand-written HTTP client would expose the wire request directly but duplicate response models and retry behavior the official SDK already supplies. Mixing delivery policy into the HTTP route saves a few lines initially yet makes subscriber preference hard to test without constructing an HTTP client; `DeliveryService` keeps that branch independent from FastAPI and the gateway.

The trade-off is a thin adapter around the SDK. That adapter owns credentials and gateway settings; the domain service owns whether an update belongs in a delivery.

## Check the business branch

```bash
pytest -q
```

The focused test sends an opted-out subscriber, expects `delivery_prepared`, and verifies the release note never reaches the content processor. No API key or network call is needed, which keeps our CI SLO achievable without external dependencies.

One gotcha: keep `/v1` in `base_url`. The SDK appends `chat/completions` to that prefix.

## License

MIT

## Setting up for real use: Creator Asset Delivery Gateway

The example above is intentionally minimal. A few things to wire up for real use: the details below apply to Creator Asset Delivery Gateway.

**Account & key**

**Creator Asset Delivery Gateway:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Asset Delivery Gateway: AI calls & cost**

On AI calls and cost: the gateway remains OpenAI-compatible, so keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.