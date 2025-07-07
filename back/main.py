import uvicorn
import re
import models
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from googleReview import fetch_reviews
from typing import List, Optional, Annotated
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import desc

app = FastAPI()

# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# NAMES = [
#     "AJ",
#     "Angelina",
#     "Averey",
#     "Avery",
#     "Cathy",
#     "Christine",
#     "Doan",
#     "Dorothy",
#     "Ella",
#     "Emma",
#     "Isaack",
#     "Kaylee",
#     "Lucas",
#     "Mathew",
#     "Matthew",
#     "Mina",
#     "Quincy",
#     "Reuben",
#     "Sissy",
#     "Victoria",
#     "Yixin"
# ]

NAMES = {
    "AJ": ["AJ"],
    "Angelina": ["Angelina"],
    "Averey": ["Averey", "Avery"],
    "Cathy": ["Cathy"],
    "Christine": ["Christine"],
    "Doan": ["Doan"],
    "Dorothy": ["Dorothy"],
    "Ella": ["Ella"],
    "Emma": ["Emma"],
    "Isaack": ["Isaack"],
    "Kaylee": ["Kaylee"],
    "Lucas": ["Lucas"],
    "Matthew": ["Matthew", "Mathew", "Matt"],
    "Mina": ["Mina"],
    "Quincy": ["Quincy"],
    "Reuben": ["Reuben"],
    "Sissy": ["Sissy"],
    "Victoria": ["Victoria"],
    "Yixin": ["Yixin"],
}

alias_to_canon = {
    variant.lower(): canon
    for canon, variants in NAMES.items()
    for variant in variants
}
dateTest = "2025-07-04"

class ReviewsRequest(BaseModel):
    place_url: str = "https://www.google.com/maps/place/Mirai+Arcade/@28.5537855,-81.204756,17z/data=!4m8!3m7!1s0x88e767bc998e5b93:0x9c7c2a15715f540c!8m2!3d28.5537855!4d-81.2021811!9m1!1b1!16s%2Fg%2F11w23m4mqy?hl=en-us&entry=ttu&g_ep=EgoyMDI1MDYyMy4yIKXMDSoASAFQAw%3D%3D"
    max_reviews: int = 100
    specificDate: Optional[str] = dateTest
    specificStar: int = 5
    names: Optional[List[str]] = NAMES
    # untilDate: Optional[str] = None

class ReviewOut(BaseModel):
    name: str
    # reviewText: Optional[str]
    # stars: int
    date: Optional[str]

# @app.post("/api/reviews", response_model=list[ReviewOut])
# async def get_reviews(req: ReviewsRequest, db: db_dependency):
#     try:
#         raw = fetch_reviews(req.place_url, req.max_reviews)
#     except Exception as e:
#         raise HTTPException(500, detail=str(e))
#     if not raw:
#         raise HTTPException(404, detail="No reviews found")
#     filtered = raw
#     if req.specificDate:
#         filtered = [
#             rv for rv in raw
#             if rv.get("publishedAtDate", "").startswith(req.specificDate)
#         ]
#     if req.specificStar is not None:
#         filtered = [
#             rv for rv in filtered
#             if rv.get("stars") == req.specificStar
#         ]
#     if req.names:
#         patterns = {
#             name: re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
#             for name in req.names
#         }
#         filtered = [
#             rv for rv in filtered
#             if any(pat.search(rv.get("text", "") or "") for pat in patterns.values())
#         ]
#         matched = []
#         counts_today: dict[str, int] = defaultdict(int)
#         for rv in filtered:
#             text = (rv.get("text", "") or "")
#             for name, pat in patterns.items():
#                 if pat.search(text):
#                     matched.append((rv, name))
#                     counts_today[name] += 1
#                     break
#         for name, cnt_value in counts_today.items():
#             emp = db.query(models.Employees).filter(models.Employees.employee_name == name).first()
#             if not emp:
#                 emp = models.Employees(employee_name=name)
#                 db.add(emp)
#                 db.commit()
#                 db.refresh(emp)
        
#             daily = db.query(models.Counts).filter(models.Counts.employee_id == emp.id, models.Counts.date == date.today()).first()
#             if not daily:
#                 daily = models.Counts(employee_id=emp.id, date=date.today(), count=cnt_value)
#                 db.add(daily)
#             else:
#                 daily.count = cnt_value
#             db.commit()
#     return [
#         ReviewOut(
#             name = name,
#             # reviewText=rv.get("text"),
#             # stars=rv.get("stars"),
#             date=rv.get("publishedAtDate"),
#         )
#         for rv, name in matched
#     ]

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 

import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("SLACK_TOKEN")
if not TOKEN:
    raise RuntimeError("Set SLACK_TOKEN in your .env")


client = slack.WebClient(TOKEN)

def get_reviews(req: ReviewsRequest, db: db_dependency):
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
        # patterns = {
        #     name: re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
        #     for name in req.names
        # }
        patterns = {
            variant: re.compile(rf"\b{re.escape(variant)}\b", re.IGNORECASE)
            for variants in NAMES.values()
            for variant in variants
        }
        filtered = [
            rv for rv in filtered
            if any(pat.search(rv.get("text", "") or "") for pat in patterns.values())
        ]
        matched = []
        counts_today: dict[str, int] = defaultdict(int)
        for rv in filtered:
            text = (rv.get("text", "") or "").lower()
            # for name, pat in patterns.items():
            #     if pat.search(text):
            #         matched.append((rv, name))
            #         counts_today[name] += 1
            #         break
            for variant, pat in patterns.items():
                if pat.search(text):
                    canon = alias_to_canon[variant.lower()]
                    counts_today[canon] += 1
                    break
        for name, cnt_value in counts_today.items():
            emp = db.query(models.Employees).filter(models.Employees.employee_name == name).first()
            if not emp:
                emp = models.Employees(employee_name=name)
                db.add(emp)
                db.commit()
                db.refresh(emp)
        
            daily = db.query(models.Counts).filter(models.Counts.employee_id == emp.id, models.Counts.date == dateTest).first()
            if not daily:
                daily = models.Counts(employee_id=emp.id, date=dateTest, count=cnt_value)
                db.add(daily)
            else:
                daily.count = cnt_value
            db.commit()

def load_counts(db: db_dependency):
    return (
        db.query(
            models.Employees.employee_name,
            models.Counts.count
        )
        .join (
            models.Counts,
            models.Employees.id == models.Counts.employee_id
        )
        .filter(models.Counts.date == dateTest)
        .order_by(desc(models.Counts.count))
        .all()
    )

def main():
    db = SessionLocal()
    try :
        countsInitial = load_counts(db)
        if not countsInitial:
            # get_reviews(ReviewsRequest(), db)
            client.chat_postMessage(channel='#pigglytest', text="boing")

        counts = load_counts(db)

        writeDate = (date.fromisoformat(dateTest)).strftime("%B %d, %Y")
        if not counts:
            text = f"{writeDate}: \n" + "No reviews today"
        else:
            lines = [f"{name}: {count} review{'s' if count>1 else ''}"
            for name, count in counts]
            text = f"{writeDate}: \n" + "\n".join(lines)
        
        client.chat_postMessage(channel='#pigglytest', text=text)

    finally:
        db.close()

if __name__ == "__main__":
    main()
