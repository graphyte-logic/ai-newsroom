from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from agents.news_fetcher import fetch_all_news
from agents.summarizer import summarize_articles
from sources.sources_config import KEYWORDS
from config import FONTI_LEGAL 

# 1. Definizione dello stato esteso per supportare i metadati ricchi del procurement
class NewsState(TypedDict):
    articles: List[dict]
    summaries: List[dict]
    digest: str
    category: str  # Gestisce la separazione dei flussi (tech, legal, procurement)

def fetch_news_node(state: NewsState) -> NewsState:
    """Fetch dalle fonti corrette in base alla categoria richiesta nello stato"""
    categoria = state.get("category", "tech")
    
    # Validazione rigida della categoria
    if categoria not in ["tech", "legal", "procurement"]:
        categoria = "tech"
        
    print(f"🔮 [LangGraph] Nodo Fetching ATTIVO per categoria: {categoria.upper()}")
    
    articles = []
    
    if categoria == "procurement":
        import feedparser
        # Configurazione fonti strutturata in base a Proc_strategia.txt e Procurement_indirizzi.txt
        FONTI_PROCUREMENT = {
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
        
        for tier, urls in FONTI_PROCUREMENT.items():
            for url in urls:
                try:
                    feed = feedparser.parse(url)
                    source_name = feed.feed.get("title", "Procurement Source")
                    for entry in feed.entries[:8]:
                        articles.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "url": entry.get("link", ""),
                            "summary": entry.get("summary", entry.get("description", "")),
                            "source": f"{source_name} ({tier})",
                            "tier": tier
                        })
                except Exception as e:
                    print(f"⚠️ Errore lettura feed procurement {url}: {e}")
                    
    elif categoria == "legal":
        import feedparser
        print(f"⚖️ Lettura archivi feed legali in corso da: {FONTI_LEGAL}")
        for url in FONTI_LEGAL:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get("title", "Fonte Legal")
                for entry in feed.entries[:10]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "source": source_name
                    })
            except Exception as e:
                print(f"⚠️ Errore lettura feed {url}: {e}")
    else:
        # Ramo Tech standard
        print(f"🌐 Avvio modulo fetch_all_news per canali verticali Tech")
        raw_news = fetch_all_news()
        for item in raw_news:
            articles.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "url": item.get("link", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", "HackerNews")
            })

    state["articles"] = articles
    return state

def summarize_news_node(state: NewsState) -> NewsState:
    """Generazione dei riassunti intelligenti tramite LLM passando il contesto di categoria"""
    articles = state.get("articles", [])
    categoria = state.get("category", "tech")
    
    print(f"🧠 [LangGraph] Nodo Summarization ATTIVO. Articoli da elaborare: {len(articles)}")
    
    # Passiamo la categoria alla funzione per abilitare il prompt strutturato sul procurement
    state["summaries"] = summarize_articles(articles, category=categoria)
    return state

def generate_digest_node(state: NewsState) -> NewsState:
    """Generate digest basato sulla categoria validata nello stato"""
    from datetime import datetime
    categoria = state.get("category", "tech")
    
    digest = ""
    if categoria == "legal":
        digest += f"```\\n⚖️ LEGAL & DIRITTO INTELLIGENCE\\n{datetime.now().strftime('%A %d %B %Y')}\\n```\\n\\n"
    elif categoria == "procurement":
        digest += f"```\\n🏛️ PROCUREMENT & COMPLIANCE REPORT\\n{datetime.now().strftime('%A %d %B %Y')}\\n```\\n\\n"
    else:
        digest += f"```\\n🤖 TECH & AI DIGEST\\n{datetime.now().strftime('%A %d %B %Y')}\\n```\\n\\n"
    
    for i, summary in enumerate(state.get("summaries", [])[:8], 1):
        title = summary['title']
        source = summary['source']
        url = summary['url']
        
        if categoria == "procurement":
            text = summary.get('summary', '')
            impact = summary.get('impact', 'MEDIUM')
            warn = f" [ALERT: {summary['executive_warning']}]" if summary.get('regulatory_alert') else ""
            digest += f"**{i}. {title}** (Impatto: {impact}){warn}\\n└─ 📰 *{source}*\\n{text}\\n> [🔗 Read full report]({url})\\n\\n"
        else:
            text = summary['summary']
            digest += f"**{i}. {title}**\\n└─ 📰 *{source}*\\n{text}\\n> [🔗 Read full article]({url})\\n\\n"
    
    digest += f"━━━━━━━━━━━━━━━━━━━━━━━━\\n*Powered by Graphyte {categoria.capitalize()} Room*"
    state["digest"] = digest
    return state

def build_news_graph():
    """Build LangGraph workflow"""
    from langgraph.graph import START
    
    graph = StateGraph(NewsState)
    
    graph.add_node("fetch", fetch_news_node)
    graph.add_node("summarize", summarize_news_node)
    graph.add_node("digest", generate_digest_node)
    
    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "digest")
    graph.add_edge("digest", END)
    
    return graph.compile()

news_graph = build_news_graph()