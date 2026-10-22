from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.config import Settings, settings


def get_settings() -> Settings:
    return settings
