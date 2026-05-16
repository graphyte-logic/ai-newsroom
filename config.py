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

# --- CONFIGURAZIONE RAMO LEGAL ---
# Puoi usare lo stesso ID canale di prima per i test, oppure crearne uno nuovo su Discord
LEGAL_CHANNEL_ID = 1497874759893913620  # Cambialo se crei un canale separato

FONTI_LEGAL = [
    "https://www.altalex.com/rss",
    "https://www.filodiritto.com/rss.xml",
    "https://www.diritto.it/feed/"
]