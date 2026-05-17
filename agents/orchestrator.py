from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from agents.news_fetcher import fetch_all_news
from agents.summarizer import summarize_articles
from sources.sources_config import KEYWORDS
from config import FONTI_LEGAL 

# 1. Definizione dello stato con la categoria blindata
class NewsState(TypedDict):
    articles: List[dict]
    summaries: List[dict]
    digest: str
    category: str  # Gestisce la separazione dei flussi (tech o legal)

def fetch_news_node(state: NewsState) -> NewsState:
    """Fetch dalle fonti corrette in base alla categoria richiesta nello stato"""
    # Se category non è presente, impostiamo il default su 'tech'
    categoria = state.get("category", "tech")
    
    # Validazione rigida: se non è espressamente 'legal', puliamo a 'tech'
    if categoria != "legal":
        categoria = "tech"
        
    print(f"🔮 [LangGraph] Nodo Fetching ATTIVO per categoria: {categoria.upper()}")
    
    if categoria == "legal":
        import feedparser
        articles = []
        print(f"⚖️ Lettura archivi feed legali in corso da: {FONTI_LEGAL}")
        for url in FONTI_LEGAL:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get("title", "Fonte Legal")
                for entry in feed.entries[:7]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "url": entry.get("link", ""),
                        "source": source_name
                    })
            except Exception as e:
                print(f"⚠️ Errore lettura feed legal {url}: {e}")
        
        state["articles"] = articles[:20]
    else:
        # Ramo TECH standard
        print("🌐 Lettura feed tecnologici in corso...")
        raw_articles = fetch_all_news()
        filtered = [
            a for a in raw_articles
            if any(kw.lower() in a.get("title", "").lower() for kw in KEYWORDS)
        ]
        state["articles"] = filtered[:20]
    
    # Manteniamo traccia della categoria validata nello stato
    state["category"] = categoria
    print(f"✅ Trovati {len(state['articles'])} articoli per {categoria.upper()}")
    return state

def summarize_node(state: NewsState) -> NewsState:
    """Summarize top articles con Claude"""
    print("Summarizing articles...")
    if not state.get("articles"):
        state["summaries"] = []
        return state
        
    summaries = summarize_articles(state["articles"])
    state["summaries"] = summaries
    print(f"Summarized {len(summaries)} articles")
    return state

def generate_digest_node(state: NewsState) -> NewsState:
    """Generate digest basato sulla categoria validata nello stato"""
    from datetime import datetime
    categoria = state.get("category", "tech")
    
    digest = ""
    if categoria == "legal":
        digest += f"```\n⚖️ LEGAL & DIRITTO INTELLIGENCE\n{datetime.now().strftime('%A %d %B %Y')}\n```\n\n"
    else:
        digest += f"```\n🤖 TECH & AI DIGEST\n{datetime.now().strftime('%A %d %B %Y')}\n```\n\n"
    
    for i, summary in enumerate(state.get("summaries", [])[:8], 1):
        title = summary['title']
        source = summary['source']
        text = summary['summary']
        url = summary['url']
        
        digest += f"**{i}. {title}**\n└─ 📰 *{source}*\n{text}\n> [🔗 Read full article]({url})\n\n"
    
    digest += f"━━━━━━━━━━━━━━━━━━━━━━━━\n*Powered by Graphyte {categoria.capitalize()} Room*"
    state["digest"] = digest
    return state

def build_news_graph():
    """Build LangGraph workflow"""
    from langgraph.graph import START
    
    graph = StateGraph(NewsState)
    
    graph.add_node("fetch", fetch_news_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("generate", generate_digest_node)
    
    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()

# Global instance
news_graph = build_news_graph()