from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from datetime import datetime
import feedparser

# Importiamo l'agente summarizer e i nuovi oggetti data-driven
from agents.summarizer import summarize_articles
from sources.sources_config import (
    SOURCES, 
    GLOBAL_KEYWORDS_INCLUDE, 
    GLOBAL_KEYWORDS_EXCLUDE, 
    CATEGORY_MAPPING
)

# 1. Definizione dello stato esteso (LangGraph State)
class NewsState(TypedDict):
    articles: List[dict]
    summaries: List[dict]
    digest: str
    category: str 

# Funzione helper di filtraggio testuale intelligente
def matches_filters(title: str, summary: str, src_inc: List[str], src_exc: List[str]) -> bool:
    text = f"{title} {summary}".lower()
    
    # 1. Controlla Keyword Escluse della Sorgente o Globali (Se ne trova anche una sola, scarta)
    all_excludes = set([k.lower() for k in src_exc] + [k.lower() for k in GLOBAL_KEYWORDS_EXCLUDE])
    if any(exc in text for exc in all_excludes):
        return False
        
    # 2. Controlla Keyword Incluse Specifiche della Sorgente
    if src_inc:
        if not any(inc.lower() in text for inc in src_inc):
            return False
            
    # 3. Se la sorgente non ha keyword stringenti, controlla se soddisfa almeno un criterio globale
    else:
        all_global_includes = [k.lower() for k in GLOBAL_KEYWORDS_INCLUDE]
        if not any(g_inc in text for g_inc in all_global_includes):
            return False
            
    return True

# 2. Nodo 1: Estrazione dei Feed Dinamica ed Intelligente
def fetch_news_node(state: NewsState) -> NewsState:
    """Esegue il fetching filtrato basandosi sulla configurazione data-driven di SOURCES"""
    room = state.get("category", "tech")
    
    # Identifica quali categorie strutturali appartengono alla stanza attiva della UI
    allowed_categories = CATEGORY_MAPPING.get(room, ["tech"])
    
    print(f"🔮 [LangGraph Hub] Fetching ATTIVO per Stanza: {room.upper()} (Categorie analizzate: {allowed_categories})")
    articles = []
    
    # Cicla sulle fonti unificate
    for src in SOURCES:
        if src["category"] not in allowed_categories:
            continue
            
        print(f"📡 Scansione sorgente: {src['name']} [{src['priority'].upper()}]")
        try:
            feed = feedparser.parse(src["url"])
            entry_count = 0
            
            for entry in feed.entries[:12]: # Analizza fino a 12 articoli recenti
                title = entry.get("title", "")
                summary_raw = entry.get("summary", entry.get("description", ""))
                url = entry.get("link", "")
                
                # Applica il motore di filtraggio semantico/testuale a monte
                if matches_filters(title, summary_raw, src["keywords_include"], src["keywords_exclude"]):
                    articles.append({
                        "title": title,
                        "summary": summary_raw,
                        "url": url,
                        "source": src["name"],
                        "category": src["category"],
                        "sub_category": src.get("sub_category", "General"),
                        "priority": src["priority"],
                        "signal_type": src["signal_type"],
                        "geo": src["geo"]
                    })
                    entry_count += 1
            print(f"   └─ Ricevuti {entry_count} articoli validi superati dai filtri.")
        except Exception as e:
            print(f"⚠️ Errore estrazione da {src['name']}: {e}")
            
    # Ordina gli articoli inseriti mettendo in cima quelli a priorità Alta ("high")
    articles.sort(key=lambda x: 0 if x["priority"] == "high" else (1 if x["priority"] == "medium" else 2))
    
    state["articles"] = articles
    return state

# 3. Nodo 2: Processamento AI dei sommari
def generate_summaries_node(state: NewsState) -> NewsState:
    """Invia gli articoli normalizzati all'agente Claude"""
    print(f"🤖 [LangGraph] Generazione schede AI per la stanza: {state['category'].upper()}")
    articles = state.get("articles", [])
    room = state.get("category", "tech")
    
    state["summaries"] = summarize_articles(articles, category=room)
    return state

# 4. Nodo 3: Compilazione del Report / Digest Avanzato
def compile_digest_node(state: NewsState) -> NewsState:
    """Compila il digest finale arricchendo il testo con i nuovi metadati (Geo, Priorità, Segnale)"""
    room = state.get("category", "tech")
    print(f"📝 [LangGraph] Compilazione report unificato per: {room.upper()}")
    
    data_str = datetime.now().strftime('%A %d %B %Y')
    
    digest = "```\n"
    digest += f"🚀 GRAPHITE INTELLIGENCE NETWORK - ROOM: {room.upper()}\n"
    digest += f"Data Rilascio: {data_str}\n"
    digest += "```\n\n"
    
    summaries = state.get("summaries", [])
    if not summaries:
        digest += "*Nessun segnale rilevante intercettato nelle ultime 24 ore rispetto ai filtri impostati.*\n"
    
    for i, summary in enumerate(summaries[:8], 1):
        title = summary.get('title', 'No Title')
        source = summary.get('source', 'Sorgente Sconosciuta')
        url = summary.get('url', '#')
        text = summary.get('summary', '')
        
        # Estraiamo i metadati nativi iniettati dal nuovo modulo sorgenti
        geo = summary.get('geo', 'Global')
        sig_type = summary.get('signal_type', 'trend').upper()
        sub_cat = summary.get('sub_category', 'General')
        
        # Prefisso grafico basato sulla tipologia di segnale
        prefix = "🔴 [REGULATORY]" if sig_type == "REGULATORY" else "⚡ [SIGNAL]"
        
        digest += f"**{i}. {prefix} {title}**\n"
        digest += f"└─ 🌍 Ambito: *{geo}* | Canale: *{sub_cat}* | Fonte: *{source}*\n"
        digest += f"{text}\n"
        digest += f"> [🔗 Apri Documentazione Originale]({url})\n\n"
        
    digest += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    digest += f"*Generato autonomamente dal sistema Graphyte Workflow Engine*"
    
    state["digest"] = digest
    return state

# 5. Costruzione ed esportazione del Workflow (LangGraph Graph)
def build_news_graph():
    """Costruisce la pipeline LangGraph e la compila una volta sola all'avvio"""
    graph = StateGraph(NewsState)
    
    # Registrazione nodi nel grafo
    graph.add_node("fetch", fetch_news_node)
    graph.add_node("summarize", generate_summaries_node)
    graph.add_node("compile", compile_digest_node)
    
    # Definizione delle connessioni sequenziali stabili
    graph.add_edge("__start__", "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "compile")
    graph.add_edge("compile", END)
    
    return graph.compile()

# Esportazione dell'istanza già compilata (Risolve il crash in main.py alla riga 38)
news_graph = build_news_graph()