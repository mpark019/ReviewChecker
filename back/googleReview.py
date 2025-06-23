import os
import re
from typing import List, Dict, Any
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv() 

TOKEN = os.getenv("APIFY_TOKEN")
if not TOKEN:
    raise RuntimeError("Set APIFY_TOKEN in your .env")

ACTOR_ID = "Xb8osYTtOjlsgI6k9"

_client = ApifyClient(TOKEN)
_actor = _client.actor(ACTOR_ID)

def fetch_reviews(
    place_url: str,
    max_reviews: int = 10,
) -> List[Dict[str, Any]]:
    run_input = {
        "startUrls": [{ "url": place_url }],
        "maxReviews": max_reviews,
        "reviewsSort": "newest",
        "language": "en",
        "reviewsOrigin": "all",
        "personalData": True,
    }

    run = _actor.call(run_input=run_input)

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        return []

    return list(_client.dataset(dataset_id).iterate_items())