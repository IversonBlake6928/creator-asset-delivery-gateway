"""HTTP boundary for creator asset delivery."""

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError

from .delivery_service import DeliveryService
from .gateway_client import InfraiContentProcessor
from .models import DeliveryRequest, DeliveryResult

app = FastAPI(title="Creator delivery service")


@app.post("/deliveries", response_model=DeliveryResult)
def prepare_delivery(request: DeliveryRequest) -> DeliveryResult:
    service = DeliveryService(InfraiContentProcessor())
    try:
        return service.prepare(request)
    except APIStatusError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=caller_status, detail="Content request rejected") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=502, detail="Content request could not be completed") from exc
