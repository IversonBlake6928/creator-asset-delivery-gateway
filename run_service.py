"""Run the creator delivery HTTP service."""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("creator_delivery.server:app", host="127.0.0.1", port=8000)
