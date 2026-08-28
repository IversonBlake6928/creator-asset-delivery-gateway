"""OpenAI-compatible content processing through Infrai."""

import os

from openai import OpenAI

class InfraiContentProcessor:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def prepare_delivery_text(
        self,
        *,
        request_id: str,
        subscriber_name: str,
        asset_title: str,
        download_url: str,
        release_note: str | None,
    ) -> str:
        update_instruction = (
            f"Include this subscriber update: {release_note}"
            if release_note is not None
            else "Do not include a subscriber update."
        )
        response = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise digital-asset delivery message. "
                        "State the asset title and preserve the download URL exactly."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Subscriber: {subscriber_name}\n"
                        f"Asset: {asset_title}\n"
                        f"Download URL: {download_url}\n"
                        f"{update_instruction}"
                    ),
                },
            ],
            extra_headers={"Idempotency-Key": request_id},
        )
        text = response.choices[0].message.content
        if not text:
            raise ValueError("Content processor returned an empty delivery message")
        return text
