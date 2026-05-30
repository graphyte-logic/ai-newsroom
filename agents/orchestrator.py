import feedparser
import re
import requests
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from datetime import datetime

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


# =====================================================================
# ENGINE DI PROCESSING AUTOMATICO (Deduplica, Scoring & Classificazione)
# =====================================================================

PRIORITY_SCORES = {
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
    # Normativa e Regolamenti Tech (EBA, DORA, AI Act)
    "dora": 5, "eba": 5, "rts": 4, "ai act": 5,
    "regulation": 4, "compliance": 3, "guidelines": 2,
    "sanction": 4, "efama": 3, "esma": 4, "eiopa": 4,
    
    # Procurement & Supply Chain
    "procurement": 5, "supply chain": 4, "vendor": 3, "third-party": 4,
    "sourcing": 3, "disruption": 3, "logistics": 2, "tender": 3,
    
    # Tech & Innovazione
    "llm": 4, "generative ai": 4, "quantum": 4, "cybersecurity": 4,
    "cloud": 2, "framework": 2, "benchmark": 3
}


def _clean_text_to_words(text: str) -> set:
    """Sana il testo estraendo un set di parole uniche per la tokenizzazione"""
    if not text:
        return set()
    text = text.lower()
    # Rimuove la punteggiatura e i caratteri speciali
    text = re.sub(r'[^\w\s]', ' ', text)
    # Ritorna un set di parole saltando gli spazi vuoti e stringhe cortissime
    return {w for w in text.split() if len(w) > 2}


def _calculate_similarity(title_a: str, title_b: str) -> float:
    """
    --- C8: CORREZIONE CRITICA - INDICE DI SIMILARITÀ DI JACCARD ---
    Risolve l'asimmetria del calcolo precedente calcolando l'esatta intersezione 
    divisa per l'unione dei due set di parole.
    """
    words_a = _clean_text_to_words(title_a)
    words_b = _clean_text_to_words(title_b)
    
    if not words_a or not words_b:
        return 0.0
        
    intersection = words_a & words_b
    union = words_a | words_b
    
    return len(intersection) / len(union)


def _compute_article_score(article: dict, src_config: dict) -> int:
    """Calcola il punteggio di rilevanza dell'articolo basandosi sulle regole configurate"""
    score = 0
    title_and_desc = (article.get("title", "") + " " + article.get("description", "")).lower()
    
    # 1. Impatto prioritario della sorgente
    src_priority = src_config.get("priority", "medium")
    score += PRIORITY_SCORES.get(src_priority, 2)
    
    # 2. Impatto del tipo di segnale della sorgente
    sig_type = src_config.get("signal_type", "trend")
    score += SIGNAL_TYPE_SCORES.get(sig_type, 3)
    
    # 3. Boost analitico delle keyword mirate
    for kw, boost in KEYWORD_BOOST.items():
        # C7: Usiamo i word boundary (\b) per evitare che parole corte facciano partial-match distorcendo lo score
        if re.search(r'\b' + re.escape(kw) + r'\b', title_and_desc):
            score += boost
            
    return score


# =====================================================================
# NODI DEL GRAFO (LangGraph Nodes)
# =====================================================================

def fetch_news_node(state: NewsState) -> NewsState:
    """Scarica, filtra per keyword, calcola lo score e deduplica gli articoli delle sorgenti"""
    target_category = state.get("category", "tech")
    print(f"📥 [Node: Fetch] Avvio scansione feed per la categoria: {target_category.upper()}")
    
    # Estrae l'elenco delle categorie sorgenti ammesse da mappare in questa stanza
    allowed_source_categories = CATEGORY_MAPPING.get(target_category, [target_category])
    
    scanned_articles = []
    
    # Filtriamo le sorgenti attive per le categorie concesse
    active_sources = [s for s in SOURCES if s.get("category") in allowed_source_categories and s.get("active", True)]
    
    for src in active_sources:
        print(f"📡 Scansione sorgente: {src['name']} ({src['url']})")
        try:
            # --- C5: INTRODUZIONE TIMEOUT PREVENTIVO ---
            # Evita il blocco infinito del thread se un feed RSS della sorgente è offline o lento
            response = requests.get(src["url"], timeout=10, headers={"User-Agent": "GraphyteBot/1.0"})
            if response.status_code != 200:
                print(f"⚠️ [Fetch] Risposta non valida dal server ({response.status_code}) per {src['name']}")
                continue
                
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                description = entry.get("summary", entry.get("description", ""))
                
                # Controllo preventivo dei dati minimi
                if not title or not link:
                    continue
                    
                combined_text = (title + " " + description).lower()
                
                # Controllo Keyword globali ed esclusive di Esclusione
                exclude_match = any(re.search(r'\b' + re.escape(ex_kw) + r'\b', combined_text) for ex_kw in GLOBAL_KEYWORDS_EXCLUDE)
                if exclude_match:
                    continue
                    
                # Controllo Keyword di inclusione specifiche della sorgente (se presenti)
                src_includes = src.get("keywords_include", [])
                if src_includes:
                    include_match = any(re.search(r'\b' + re.escape(in_kw) + r'\b', combined_text) for in_kw in src_includes)
                    if not include_match:
                        continue
                        
                # Costruzione oggetto Articolo Grezzo
                article_obj = {
                    "title": title,
                    "url": link,
                    "description": description,
                    "source": src["name"],
                    "source_category": src["category"],
                    "fetched_at": datetime.now().isoformat()
                }
                
                # Calcolo del punteggio algoritmico
                article_obj["score"] = _compute_article_score(article_obj, src)
                scanned_articles.append(article_obj)
                
        except requests.exceptions.RequestException as te:
            print(f"⏳ [Fetch Timeout/Error] Sorgente temporaneamente non raggiungibile: {src['name']} ({te})")
        except Exception as e:
            print(f"❌ [Fetch Errore] Impossibile processare il feed di {src['name']}: {e}")

    print(f"📊 [Fetch Completed] Recuperati {len(scanned_articles)} articoli grezzi potenziali.")

    # --- REGOLA DI SBARRAMENTO ADATTIVA (FILTRO SCORE) ---
    filtered_by_score = []
    for art in scanned_articles:
        score = art["score"]
        
        # C4: Risolto mismatch logico/commento. Applichiamo le soglie pulite per stanza
        if target_category == "procurement" and score >= 5:
            filtered_by_score.append(art)
        elif target_category == "legal" and score >= 3: # C4: Allineata alla soglia reale
            filtered_by_score.append(art)
        elif target_category == "tech" and score >= 3:
            filtered_by_score.append(art)

    print(f"✂️ [Score Filter] Superano la soglia minima di rilevanza: {len(filtered_by_score)} articoli.")

    # --- PROCESSO DI DEDUPLICAZIONE ROBUSTA (ALGORITMO JACCARD) ---
    deduplicated_list = []
    for current_art in filtered_by_score:
        is_duplicate = False
        for saved_art in deduplicated_list:
            # Calcolo dell'indice di similarità simmetrico
            similarity = _calculate_similarity(current_art["title"], saved_art["title"])
            if similarity > 0.45:  # Soglia di sovrapposizione del 45% dei termini chiave
                is_duplicate = True
                # In caso di duplicato, manteniamo l'articolo con il punteggio (score) più alto
                if current_art["score"] > saved_art["score"]:
                    saved_art["title"] = current_art["title"]
                    saved_art["description"] = current_art["description"]
                    saved_art["score"] = current_art["score"]
                    saved_art["url"] = current_art["url"]
                break
        if not is_duplicate:
            deduplicated_list.append(current_art)

    print(f"✨ [Deduplication Completed] Rimasti {len(deduplicated_list)} articoli unici candidati alla sintesi.")
    
    # Ordiniamo per punteggio decrescente
    deduplicated_list.sort(key=lambda x: x["score"], reverse=True)
    
    # Limitiamo il carico massimo (es. top 15 articoli) per ottimizzare i costi API e i tempi di elaborazione
    state["articles"] = deduplicated_list[:15]
    return state


def summarize_news_node(state: NewsState) -> NewsState:
    """Invia il pacchetto di articoli scremati all'agente generativo Claude per la sintesi strutturata"""
    articles_to_process = state.get("articles", [])
    category = state.get("category", "tech")
    
    if not articles_to_process:
        print("ℹ️ [Node: Summarize] Nessun articolo valido da riassumere.")
        state["summaries"] = []
        return state
        
    print(f"🤖 [Node: Summarize] Invocazione di Claude in corso su {len(articles_to_process)} articoli...")
    
    # Invia gli articoli all'agente integrato in summarizer.py
    summarized_data = summarize_articles(articles_to_process, category)
    
    print(f"✅ [Node: Summarize] Generati con successo {len(summarized_data)} oggetti di intelligence arricchiti.")
    state["summaries"] = summarized_data
    return state


def compile_digest_node(state: NewsState) -> NewsState:
    """Compila il report editoriale finale in formato Markdown per l'Executive Digest"""
    summaries = state.get("summaries", [])
    category = state.get("category", "tech")
    
    print(f"📝 [Node: Digest] Compilazione rassegna editoriale Markdown...")
    
    current_date = datetime.now().strftime("%d/%m/%Y")
    digest = f"# 📊 Executive Intelligence Digest — Canale {category.upper()}\\n"
    digest += f"*Ecosistema informativo Graphyte Logic — Report del {current_date}*\\n\\n"
    digest += "━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
    
    if not summaries:
        digest += "### 🔍 Nessun aggiornamento di rilievo registrato nelle ultime ore.\\n"
        digest += "Il sistema di scansione non ha intercettato anomalie critiche conformi ai filtri di sicurezza.\\n"
        state["digest"] = digest
        return state

    # Prendiamo al massimo i primi 8 articoli d'impatto per il digest scritto
    for i, summary in enumerate(summaries[:8], 1):
        title = summary.get('title', 'No Title')
        source = summary.get('source', 'Sorgente Sconosciuta')
        url = summary.get('url', '#')
        text = summary.get('summary', '')
        
        geo = summary.get('geo', 'Global')
        sig_type = summary.get('signal_type', 'trend').upper()
        sub_cat = summary.get('sub_category', 'General')
        
        prefix = "🔴 [REGULATORY]" if sig_type == "REGULATORY" else "⚡ [SIGNAL]"
        
        digest += f"**{i}. {prefix} {title}**\\n"
        digest += f"└─ 🌍 Ambito: *{geo}* | Canale: *{sub_cat}* | Fonte: *{source}*\\n"
        digest += f"{text}\\n"
        digest += f"> [🔗 Apri Documentazione Originale]({url})\\n\\n"
        
    digest += "━━━━━━━━━━━━━━━━━━━━━━━━\\n"
    digest += f"*Generato autonomamente dal sistema Graphyte Workflow Engine*"
    
    state["digest"] = digest
    return state


# 5. Costruzione ed esportazione del Workflow (LangGraph Graph)
def build_news_graph():
    """Costruisce la pipeline LangGraph e la compila una volta sola all'avvio"""
    graph = StateGraph(NewsState)
    
    graph.add_node("fetch", fetch_news_node)
    graph.add_node("summarize", summarize_news_node)
    graph.add_node("digest", compile_digest_node)
    
    # Definizione delle dipendenze dei nodi (Flusso Sequenziale)
    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "digest")
    graph.add_edge("digest", END)
    
    return graph.compile()

# Istanza pronta all'uso importabile nel main.py
news_graph = build_news_graph()