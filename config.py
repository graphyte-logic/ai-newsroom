import os
from dotenv import load_dotenv

load_dotenv()

# APIs
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Schedule
MORNING_HOUR = 8  # 8 AM
EVENING_HOUR = 18  # 6 PM

# News config
MAX_ARTICLES = 15
SUMMARY_LENGTH = "2-3 sentences"