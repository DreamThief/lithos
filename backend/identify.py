"""
LEGO piece identification via the Brickognize API.
https://brickognize.com

POST https://api.brickognize.com/predict/
  - multipart/form-data: file (JPEG/PNG image)

Response:
{
  "items": [
    {
      "id": "3001",
      "name": "Brick 2 x 4",
      "score": 0.97,
      "img_url": "https://img.bricklink.com/ItemImage/PN/11/3001.png"
    },
    ...
  ]
}
"""

import logging
from io import BytesIO

import httpx

logger = logging.getLogger(__name__)

BRICKOGNIZE_URL = "https://api.brickognize.com/predict/"
# Number of top candidates to return to the UI
TOP_N = 5
# Seconds before giving up on the API call
REQUEST_TIMEOUT = 15.0


async def identify_piece(image: BytesIO, filename: str = "image.jpg") -> dict:
    """
    Send an image to Brickognize and return structured identification results.

    Returns a dict with:
      - items: list of {id, name, score, img_url}
      - error: present only on failure
    """
    image.seek(0)
    image_bytes = image.read()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                BRICKOGNIZE_URL,
                files={"query_image": (filename, image_bytes, "image/jpeg")},
            )
            response.raise_for_status()

        data = response.json()
        items = data.get("items", [])[:TOP_N]

        logger.info(
            "Brickognize returned %d result(s); top: %s (%.0f%%)",
            len(items),
            items[0]["name"] if items else "—",
            (items[0]["score"] * 100) if items else 0,
        )

        return {"items": items}

    except httpx.HTTPStatusError as exc:
        logger.error("Brickognize HTTP error %s: %s", exc.response.status_code, exc.response.text)
        return {"items": [], "error": f"API error {exc.response.status_code}"}

    except httpx.RequestError as exc:
        logger.error("Brickognize request failed: %s", exc)
        return {"items": [], "error": "Could not reach Brickognize API — check internet connection"}

    except Exception as exc:
        logger.exception("Unexpected error during identification")
        return {"items": [], "error": str(exc)}
