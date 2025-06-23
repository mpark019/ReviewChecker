from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict
import json
import spacy
from playwright.sync_api import sync_playwright
from collections import defaultdict
from typing import Optional

app = FastAPI()

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load employee names from a JSON file
def load_employee_names(path: str = "data/employee_names.json") -> List[str]:
    with open(path, "r") as f:
        return json.load(f)

# Scrape reviews using Playwright
def get_reviews(url: str, max_reviews: int = 30) -> List[str]:
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(5000)

        # Scroll and wait to load more reviews
        for _ in range(5):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(2000)

        # Select reviews (adjust selector based on inspection)
        review_elements = page.query_selector_all('div[class*="review"]')
        for element in review_elements[:max_reviews]:
            text = element.inner_text()
            if text:
                reviews.append(text)

        browser.close()
    return reviews

# Match employee names

def match_employee_names(review: str, employee_names: List[str]) -> List[str]:
    matches = []
    for name in employee_names:
        if name.lower() in review.lower():
            matches.append(name)
    return matches

# Count mentions

def count_name_mentions(reviews: List[str], employee_names: List[str]) -> Dict[str, int]:
    counter = defaultdict(int)
    for review in reviews:
        matched_names = match_employee_names(review, employee_names)
        for name in matched_names:
            counter[name] += 1
    return dict(counter)

@app.get("/filter")
def filter_reviews(url: Optional[str] = Query(None)):
    employee_names = load_employee_names()

    # reviews = get_reviews(url)
    reviews = [
        "Ella was amazing",
        "Yixin was awesome",
        "Averey was wonderful",
        "aj. was cool"
    ]


    counts = count_name_mentions(reviews, employee_names)
    return {"counts": counts}
