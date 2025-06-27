import uvicorn
import re
import models
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from googleReview import fetch_reviews
from typing import List, Optional, Annotated
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date
from collections import defaultdict

app = FastAPI()

models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# class NameBase(BaseModel):
#     name_text:str

# class ReviewBase(BaseModel):
#     review_text:str
#     names: List[NameBase]

# @app.get("/names/{name_text}")
# async def read_name(name_text: str, db: db_dependency):
#     result = db.query(models.Names).filter(models.Names.name_text == name_text).all()
#     if not result:
#         raise HTTPException(status_code=404, detail='name not found')
#     return result

# @app.post("/reviews/")
# async def create_reviews(reviews: ReviewBase, db: db_dependency):
#     db_review = models.Reviews(review_text=reviews.review_text)
#     db.add(db_review)
#     db.commit()
#     db.refresh(db_review)
#     for name in reviews.names:
#         db_name = models.Names(name_text=name.name_text, review_id=db_review.id)
#         db.add(db_name)
#     db.commit()

# @app.post("/api/daily_count/")
# def appendCount(employee_name: str, count_value: int, db: db_dependency):
    
#     today = date.today()

#     emp = db.query(models.Employees).filter(models.Employees.employee_name == employee_name).first()
#     if not emp:
#         emp = models.Employees(employee_name=employee_name)
#         db.add(emp)
#         db.commit()
#         db.refresh(emp)

#     cnt = db.query(models.Counts).filter(models.Counts.employee_id == emp.id).first()
#     if not cnt:
#         cnt = models.Counts(employee_id=emp.id, date=today, count=count_value)
#         db.add(cnt)
#     else:
#         cnt.count = count_value
    
#     db.commit()
#     db.refresh(cnt)

#     return {
#         "employee": emp.employee_name,
#         "date": cnt.date.isoformat(),
#         "count": cnt.count
#     }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

NAMES = [
    "AJ",
    "Angelina",
    "Averey",
    "Avery",
    "Cathy",
    "Christine",
    "Doan",
    "Dorothy",
    "Ella",
    "Emma",
    "Isaack",
    "Kaylee",
    "Lucas",
    "Mathew",
    "Matthew",
    "Mina",
    "Quincy",
    "Reuben",
    "Sissy",
    "Victoria",
    "Yixin"
]

class ReviewsRequest(BaseModel):
    place_url: str = "https://www.google.com/maps/place/Mirai+Arcade/@28.5537855,-81.204756,17z/data=!4m8!3m7!1s0x88e767bc998e5b93:0x9c7c2a15715f540c!8m2!3d28.5537855!4d-81.2021811!9m1!1b1!16s%2Fg%2F11w23m4mqy?hl=en-us&entry=ttu&g_ep=EgoyMDI1MDYyMy4yIKXMDSoASAFQAw%3D%3D"
    max_reviews: int = 10
    specificDate: Optional[str] = date.today()
    specificStar: int = 5
    names: Optional[List[str]] = NAMES
    # untilDate: Optional[str] = None

class ReviewOut(BaseModel):
    name: str
    # reviewText: Optional[str]
    # stars: int
    date: Optional[str]

@app.post("/api/reviews", response_model=list[ReviewOut])
async def get_reviews(req: ReviewsRequest, db: db_dependency):
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
        matched = []
        counts_today: dict[str, int] = defaultdict(int)
        for rv in filtered:
            text = (rv.get("text", "") or "")
            for name, pat in patterns.items():
                if pat.search(text):
                    matched.append((rv, name))
                    counts_today[name] += 1
                    break
        for name, cnt_value in counts_today.items():
            emp = db.query(models.Employees).filter(models.Employees.employee_name == name).first()
            if not emp:
                emp = models.Employees(employee_name=name)
                db.add(emp)
                db.commit()
                db.refresh(emp)
        
            daily = db.query(models.Counts).filter(models.Counts.employee_id == emp.id, models.Counts.date == date.today()).first()
            if not daily:
                daily = models.Counts(employee_id=emp.id, date=date.today(), count=cnt_value)
                db.add(daily)
            else:
                daily.count = cnt_value
            db.commit()
    return [
        ReviewOut(
            name = name,
            # reviewText=rv.get("text"),
            # stars=rv.get("stars"),
            date=rv.get("publishedAtDate"),
        )
        for rv, name in matched
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 