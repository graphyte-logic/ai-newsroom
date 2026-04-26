# RSS feeds italiane tech + HN
FEEDS = {
    "hackernews": {
        "url": "https://news.ycombinator.com/rss",
        "name": "HackerNews",
        "weight": 2
    },
    "italiani_dev": {
        "url": "https://italiani.dev/rss",
        "name": "Italiani.dev",
        "weight": 1
    },
    "dev_to_ai": {
        "url": "https://dev.to/api/articles?tags=ai,machine-learning&top=7",
        "name": "Dev.to AI",
        "weight": 1
    },
    "medium_tech": {
        "url": "https://medium.com/feed/tag/technology",
        "name": "Medium Tech",
        "weight": 1
    },
}

# Keywords da tracciare
KEYWORDS = [
    "AI", "LLM", "Claude", "GPT", "Gemini", "agentic", "transformer",
    "Python", "JavaScript", "API", "database",
    "startup", "funding", "neural", "model"
]