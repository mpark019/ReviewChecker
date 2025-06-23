import uvicorn
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from googleReview import fetch_reviews
from typing import List, Optional

app = FastAPI()

class ReviewsRequest(BaseModel):
    place_url: str
    max_reviews: int = 10
    specificDate: Optional[str] = None
    specificStar: int = None
    names: Optional[List[str]] = None
    untilDate: Optional[str] = None

class ReviewOut(BaseModel):
    reviewText: Optional[str]
    stars: int
    date: Optional[str]

@app.post("/api/reviews", response_model=list[ReviewOut])
async def get_reviews(req: ReviewsRequest):
    try:
        raw = fetch_reviews(req.place_url, req.max_reviews)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    if not raw:
        raise HTTPException(404, detail="No reviews found")
    filtered = raw
    if req.specificDate:
        filtered = [
            rv for rv in raw
            if rv.get("publishedAtDate", "").startswith(req.specificDate)
        ]
    if req.specificStar is not None:
        filtered = [
            rv for rv in filtered
            if rv.get("stars") == req.specificStar
        ]
    if req.names:
        patterns = {
            name: re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
            for name in req.names
        }
        filtered = [
            rv for rv in filtered
            if any(pat.search(rv.get("text", "") or "") for pat in patterns.values())
        ]
    return [
        ReviewOut(
            reviewText=rv.get("text"),
            stars=rv.get("stars"),
            date=rv.get("publishedAtDate"),
        )
        for rv in filtered
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 