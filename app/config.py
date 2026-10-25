import os
from dotenv import load_dotenv

load_dotenv()   


class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "redundancy_db")
    # names at least this similar (0..1) + same phone = same person
    NAME_SIMILARITY_THRESHOLD = float(os.getenv("NAME_SIMILARITY_THRESHOLD", "0.85"))