from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import keygen, models, schemas

def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    key = keygen.create_unique_random_key(db)
    db_url = models.URL(
        target_url=url.target_url, key=key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )

def get_all_urls(db: Session) -> models.URL:
    return db.query(models.URL).all()

def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url

# def get_db_url_by_key(db: Session, url_key: str):
#     return db.query(models.URL).filter(models.URL.key == url_key).first()

def delete_db_url(db: Session, url_key: str):
    db_url = get_db_url_by_key(db, url_key)
    if db_url:
        db.delete(db_url)
        db.commit()  
    else:
        raise HTTPException(status_code=404, detail="URL not found")