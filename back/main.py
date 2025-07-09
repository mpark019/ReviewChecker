import re
import models
from pydantic import BaseModel
from googleReview import fetch_reviews
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date
from collections import defaultdict
from sqlalchemy import desc, func
from typing import Optional, List

import slack
import os
from dotenv import load_dotenv
import calendar

models.Base.metadata.create_all(bind=engine)

load_dotenv()

TOKEN = os.getenv("SLACK_TOKEN")
if not TOKEN:
    raise RuntimeError("SLACK_TOKEN MISSING")


client = slack.WebClient(TOKEN)

today = date.today()

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

class ReviewsRequest(BaseModel):
    place_url: str = "https://www.google.com/maps/place/Mirai+Arcade/@28.5537855,-81.204756,17z/data=!4m8!3m7!1s0x88e767bc998e5b93:0x9c7c2a15715f540c!8m2!3d28.5537855!4d-81.2021811!9m1!1b1!16s%2Fg%2F11w23m4mqy?hl=en-us&entry=ttu&g_ep=EgoyMDI1MDYyMy4yIKXMDSoASAFQAw%3D%3D"
    max_reviews: int = 100
    specificDate: str = today.strftime("%Y-%m-%d")
    specificStar: int = 5
    names: List[str] = NAMES

class ReviewOut(BaseModel):
    name: str
    date: Optional[str]

def get_reviews(req: ReviewsRequest, db: Session):
    db = SessionLocal()
    try:
        try:
            raw = fetch_reviews(req.place_url, req.max_reviews)
        except Exception as e:
            raise Exception(500, detail=str(e))
        if not raw:
            raise Exception(404, detail="No reviews found")
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
            
                daily = db.query(models.Counts).filter(models.Counts.employee_id == emp.id, models.Counts.date == today).first()
                if not daily:
                    daily = models.Counts(employee_id=emp.id, date=today, count=cnt_value)
                    db.add(daily)
                else:
                    daily.count = cnt_value
                db.commit()
    finally:
        db.close()

def load_counts(db: Session):
    db = SessionLocal()
    try:
        return (
            db.query(
                models.Employees.employee_name,
                models.Counts.count
            )
            .join (models.Counts, models.Employees.id == models.Counts.employee_id)
            .filter(models.Counts.date == today)
            .order_by(desc(models.Counts.count))
            .all()
        )
    finally:
        db.close()

def total_counts(firstDay: int, lastDay: int, year: int, month: int, db: Session):
    try:
        date1 = date(year, month, firstDay)
        date2 = date(year, month, lastDay)
        return (
            db.query(
                models.Employees.employee_name,
                func.sum(models.Counts.count).label("total_count")
            )
            .join(models.Counts, models.Employees.id == models.Counts.employee_id)
            .filter(models.Counts.date >= date1, models.Counts.date <= date2)
            .group_by(models.Employees.employee_name)
            .order_by(desc("total_count"))
            .all()
        )
    finally:
        db.close()

def endOfMonth(db: Session):
    db = SessionLocal()
    try:

        todayYear = today.strftime("%Y")
        todayMonth = today.strftime("%-m")
        todayDay = today.strftime("%-d")

        yearInt = int(todayYear)
        monthInt = int(todayMonth)
        dayInt = int(todayDay)

        lastDay = calendar.monthrange(yearInt, monthInt)[1]

        if dayInt == lastDay:
            sumCounts = total_counts(1, lastDay, yearInt, monthInt, db)
            linesFinal = [f"{name}: {sumCount} review{'s' if sumCount>1 else''}"
            for name, sumCount in sumCounts]
            monthDateText = today.strftime("%B %Y")
            textMonth = f"{monthDateText} Monthly Totals: \n" + "\n".join(linesFinal)
            client.chat_postMessage(channel='#pigglytest', text=textMonth)
    finally:
        db.close()

def main():
    db = SessionLocal()
    try :
        countsInitial = load_counts(db)
        if not countsInitial:
            get_reviews(ReviewsRequest(), db)

        counts = load_counts(db)

        writeDate = today.strftime("%B %d, %Y")
        if not counts:
            text = f"{writeDate}: \n" + "No reviews today"
        else:
            lines = [f"{name}: {count} review{'s' if count>1 else ''}"
            for name, count in counts]
            text = f"{writeDate}: \n" + "\n".join(lines)
        
        client.chat_postMessage(channel='#pigglytest', text=text)

        endOfMonth(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
