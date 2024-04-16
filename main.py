from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from url_labeler import categorize, URLItem
from pydantic import BaseModel
from typing import List
from url_graph import URLModel
from traversal.search import extract_data

app = FastAPI()

class URL(BaseModel):
    href: str
    text: str

class URLList(BaseModel):
    reference_url: str
    place_id: str
    urls: List[URL]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post('/create_urls')
def create_urls(urls: URLList):
    reference_url_model = None
    if urls.reference_url:
        reference_url_model = URLModel.find_by_href_and_place_id(urls.reference_url, urls.place_id)
        if reference_url_model is None:
            reference_url_model = URLModel(href=urls.reference_url, text='', found_types='', place_id=urls.place_id, category=None)
            reference_url_model.save()

    existing_urls = URLModel.find_by_href_list_and_place_id([url.href for url in urls.urls], urls.place_id)
    if len(existing_urls) == 0:
        print('No URLS found')

    existing_urls_map = {url.href: url for url in existing_urls}
    new_urls_to_create = list({url.href: url for url in urls.urls if url.href not in existing_urls_map}.values())
    created_ids = URLModel.bulk_create([(url.href, url.text) for url in new_urls_to_create], urls.place_id, reference_url_model.id if reference_url_model is not None else None)
    return {"created_urls": len(created_ids)}

@app.post("/process_urls")
def process_urls(url_item: URLItem):
    existing_url = URLModel.find_by_href_and_place_id(url_item.href, url_item.place_id)
    if existing_url is None:
        return { 'error': 'Failure' }
    url_item.text = existing_url.text
    category = categorize(url_item)
    url_item.category = category
    return url_item

class Content(BaseModel):
    urls: List[URL]
    visited: List[str]
@app.post('/process_content')
def process_content(content: Content):
    return { 'result': extract_data(content.urls, content.visited)}
