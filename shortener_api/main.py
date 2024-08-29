# shortener_api/main.py
import validators
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from starlette.datastructures import URL

from . import  crud, models, schemas
from .database import SessionLocal, engine

from .config import get_settings

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"

@app.get("/urls", response_model=list[schemas.URLInfo] )
def read_links(db: Session = Depends(get_db)):
    urls = crud.get_all_urls(db)
    return [
        schemas.URLInfo(
            url=url.key, 
            **url.__dict__  
        )
        for url in  urls]

@app.get("/{url_key}")
def forward_to_target_url(url_key: str, request: Request, db: Session = Depends(get_db)):
    db_url = (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)
    db_url.url = db_url.key
    return db_url

@app.delete("/url/{url_key}", status_code=204)  
def delete_url(url_key: str, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_by_key(db, url_key)
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    
    crud.delete_db_url(db, url_key)
    db.commit() 

    return Response(status_code=204)  


   