import os
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "Asra's AI Assistant"

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "Asra_ai_assistant")
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "user_profiles")

CORS_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
