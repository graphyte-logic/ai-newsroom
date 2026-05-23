# ==============================================================================
# 🌐 CONFIGURAZIONE CANALE: TECH & AI
# ==============================================================================
FEEDS_TECH = {
    "hackernews": {
        "url": "https://news.ycombinator.com/rss",
        "name": "HackerNews"
    },
    "italiani_dev": {
        "url": "https://italiani.dev/rss",
        "name": "Italiani.dev"
    },
    "dev_to_ai": {
        "url": "https://dev.to/api/articles?tags=ai,machine-learning&top=7",
        "name": "Dev.to AI"
    },
    "medium_tech": {
        "url": "https://medium.com/feed/tag/technology",
        "name": "Medium Tech"
    }
}

# Parole chiave stringenti per il canale Tech (solo AI pura e derivati)
KEYWORDS_TECH = [
    "ai", "artificial intelligence", "intelligenza artificiale", "llm", "gpt", 
    "claude", "openai", "nvidia", "machine learning", "deep learning", 
    "neural", "copilot", "agent", "midjourney", "anthropic", "gemini"
]


# ==============================================================================
# ⚖️ CONFIGURAZIONE CANALE: LEGAL & DIRITTO
# ==============================================================================
FEEDS_LEGAL = [
    # Qui abbiamo inserito i feed che prima erano in config.py (FONTI_LEGAL)
    "https://www.gazzettaufficiale.it/rss/provvedimenti/nuovi",
    "https://www.garanteprivacy.it/home/rss",
    "https://www.altalex.com/rss"
]


# ==============================================================================
# 🏛️ CONFIGURAZIONE CANALE: PROCUREMENT & COMPLIANCE
# ==============================================================================
FEEDS_PROCUREMENT = {
    "Tier 1 (ALERT)": [
        "https://eba.europa.eu/news-press/news/rss.xml",
        "https://www.bankingsupervision.europa.eu/home/rss/html/index.en.html",
        "https://www.cssf.lu/en/rss-feed/"
    ],
    "Tier 2 (INTELLIGENCE)": [
        "https://www.bis.org/doclist/rss_all_categories.rss",
        "https://www.finextra.com/rss/headlines.aspx",
        "https://www.finextra.com/rss/channel.aspx?channel=ai",
        "https://www.finextra.com/rss/channel.aspx?channel=risk",
        "https://www.finextra.com/rss/channel.aspx?channel=cloud"
    ],
    "Tier 3 (TREND)": [
        "https://spendmatters.com/feed",
        "https://procurementleaders.com/feed",
        "https://sievo.com/blog/rss.xml",
        "https://feeds.feedburner.com/sc247/rss",
        "https://www.ncsc.nl/rss",
        "https://economic-research.bnpparibas.com/rss/en-us",
        "https://cepr.org/rss/vox-content"
    ]
}

# Parole chiave normative estratte da Procurement_parole chiavi.txt
KEYWORDS_PROCUREMENT = [
    "eba", "dora", "rts", "guidelines", "consultation", 
    "third-party", "procurement", "sourcing", "outsourcing"
]