import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@EnglishGrammarEX")
CPM_LINK = os.getenv("CPM_LINK", "")

POST_TIMES = [t.strip() for t in os.getenv("POST_TIMES", "09:00,18:00").split(",") if t.strip()]
TIMEZONE = os.getenv("TIMEZONE", "UTC")

TOPIC_POOL = [t.strip() for t in os.getenv(
    "TOPIC_POOL",
    "Tenses,Modal Verbs,Conditionals,Prepositions,Subject-Verb Agreement"
).split(",") if t.strip()]

DB_PATH = os.path.join(os.path.dirname(__file__), "quiz.db")
FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
BG_DIR = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing. Copy .env.example to .env and fill it in.")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing. Copy .env.example to .env and fill it in.")
