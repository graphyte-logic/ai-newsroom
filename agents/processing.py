# agents/processing.py
import re

PRIORITY_SCORES = {
    "Tier 1 (CRITICAL)": 5,
    "Tier 2 (HIGH)": 3,
    "Tier 3 (TREND)": 1,
    "high": 4,
    "medium": 2,
    "low": 1
}

SIGNAL_TYPE_SCORES = {
    "regulatory": 5,
    "trend": 3,
    "weak_signal": 1
}

KEYWORD_BOOST = {
    "dora": 5,
    "eba": 5,
    "rts": 4,
    "outsourcing": 4,
    "third party": 4,
    "third-party": 4,
    "procurement": 3,
    "supplier": 3,
    "sourcing": 3,
    "ai": 2,
    "intelligenza artificiale": 2,
    "llm": 2
}

def compute_score(article):
    score = 0
    # Gestisce sia la nomenclatura tier che priority per sicurezza
    tier = article.get("tier", article.get("priority", "low"))
    score += PRIORITY_SCORES.get(tier, 1)
    
    sig_type = article.get("signal_type", "trend")
    score += SIGNAL_TYPE_SCORES.get(sig_type, 3)

    content = (article.get("title", "") + " " + article.get("summary", "")).lower()

    for keyword, boost in KEYWORD_BOOST.items():
        if keyword in content:
            score += boost

    return score

def normalize_text(text):
    if not text:
        return ""
    return re.sub(r'[^a-z0-9 ]', '', text.lower())

def similarity(a, b):
    a_words = set(a.split())
    b_words = set(b.split())
    if not a_words or not b_words:
        return 0
    return len(a_words & b_words) / max(len(a_words), 1)

def deduplicate_articles(articles, threshold=0.6):
    unique = []
    for article in articles:
        norm = normalize_text(article.get("title", ""))
        if not any(similarity(norm, normalize_text(u.get("title", ""))) > threshold for u in unique):
            unique.append(article)
    return unique