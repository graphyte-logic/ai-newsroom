from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import feedparser

# Importiamo le nuove configurazioni centralizzate
from sources.sources_config import (
    FEEDS_TECH, KEYWORDS_TECH,
    FEEDS_LEGAL,
    FEEDS_PROCUREMENT, KEYWORDS_PROCUREMENT
)

class NewsState(TypedDict):
    articles: List[dict]
    summaries: List[dict]
    digest: str
    category: str 

def fetch_news_node(state: NewsState) -> NewsState:
    """Fetch dalle fonti centralizzate in sources_config basato sulla stanza attiva"""
    categoria = state.get("category", "tech")
    
    if categoria not in ["tech", "legal", "procurement"]:
        categoria = "tech"
        
    print(f"🔮 [LangGraph] Nodo Fetching ATTIVO per categoria: {categoria.upper()}")
    articles = []
    
    # ----------------------------------------------------
    # ESTRAZIONE PROCUREMENT (Nuova logica pulita su Tiers)
    # ----------------------------------------------------
    if categoria == "procurement":
        for tier_name, urls in FEEDS_PROCUREMENT.items():
            for url in urls:
                try:
                    feed = feedparser.parse(url)
                    source_name = feed.feed.get("title", "Procurement Source")
                    for entry in feed.entries[:8]:
                        articles.append({
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", entry.get("description", "")),
                            "url": entry.get("link", ""),
                            "source": source_name,
                            "tier": tier_name # Passa il Tier a Claude per la priorità
                        })
                except Exception as e:
                    print(f"⚠️ Errore lettura feed Procurement {url}: {e}")

    # ----------------------------------------------------
    # ESTRAZIONE LEGAL
    # ----------------------------------------------------
    elif categoria == "legal":
        for url in FEEDS_LEGAL:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get("title", "Fonte Legal")
                for entry in feed.entries[:8]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "url": entry.get("link", ""),
                        "source": source_name
                    })
            except Exception as e:
                print(f"⚠️ Errore lettura feed Legal {url}: {e}")

    # ----------------------------------------------------
    # ESTRAZIONE TECH (HackerNews + Altri Feed AI)
    # ----------------------------------------------------
    else:
        # Se usi un modulo esterno dedicatò a HN o fetch_all_news, passagli direttamente FEEDS_TECH
        # Altrimenti, per i feed RSS standard configurati nel dizionario TECH:
        for key, info in FEEDS_TECH.items():
            try:
                feed = feedparser.parse(info["url"])
                source_name = info["name"]
                for entry in feed.entries[:10]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "url": entry.get("link", ""),
                        "source": source_name
                    })
            except Exception as e:
                print(f"⚠️ Errore lettura feed Tech {info['url']}: {e}")
                
    state["articles"] = articles
    return state