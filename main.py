import json
import os
import subprocess
import threading
import traceback
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

# --- C2: BLINDAGGIO ENCODING EMOJI PER WINDOWS / RENDER LOGS ---
# Reconfigura lo stdout per usare tassativamente UTF-8 evitando errori di codifica 'charmap'/cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agents.orchestrator import news_graph

# Garantisce l'esistenza della cartella di output per i digest Markdown
os.makedirs("data", exist_ok=True)

# --- M5: DIZIONARIO GLOBALE PER TRACCIARE LO STATO DI AVANZAMENTO REALE ---
GLOBAL_STATUS = {
    "tech": {"running": False, "message": "In attesa", "updated_at": None},
    "legal": {"running": False, "message": "In attesa", "updated_at": None},
    "procurement": {"running": False, "message": "In attesa", "updated_at": None}
}

# --- C11: LIFESPAN CONTEXT MANAGER (Risolve la deprecazione di on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Logica di Avvio (Startup)
    print("🚀 Inizializzazione Scheduler Automatico...")
    scheduler.start()
    yield
    # Logica di Spegnimento (Shutdown)
    print("🛑 Arresto Scheduler...")
    scheduler.shutdown(wait=False)

# Inizializzazione FastAPI con il lifespan manager
app = FastAPI(title="Graphyte Intelligence Hub Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔒 LOCK GLOBALE: Impedisce a thread simultanei di corrompere la cartella Git locale
git_lock = threading.Lock()

def auto_push_to_github(json_file: str, md_file: str):
    """Sincronizza in modo sicuro i database JSON e i report Markdown su GitHub Pages"""
    with git_lock:
        print(f"🔒 [Lock Git] Accesso esclusivo acquisito per il push di {json_file} e {md_file}")
        try:
            # M13 Quick Win: Eseguiamo un pull preventivo con rebase per evitare collisioni se origin è avanti
            print("🔄 [Git] Esecuzione git pull --rebase preventivo...")
            subprocess.run(["git", "pull", "--rebase"], check=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            
            subprocess.run(["git", "add", json_file, md_file], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                f"⚡ Auto-update {json_file}/{md_file}: {datetime.now().strftime('%H:%M:%S')}"
            ], check=True)
            
            print("📤 [Git] Invio delle modifiche al repository remoto (git push)...")
            subprocess.run(["git", "push", "origin", "master"], check=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            print(f"✅ [Git] Push completato con successo per {json_file} e {md_file}")
        except subprocess.CalledProcessError as e:
            print(f"❌ [Git] Errore critico durante le operazioni git: {e}")
        except Exception as ex:
            print(f"❌ [Git] Errore imprevisto nella pipeline Git: {ex}")

def esegui_workflow_news(category: str):
    """Esegue il grafo LangGraph per elaborare le notizie e aggiorna i database locali"""
    print(f"\n🔮 [Workflow] Avvio dell'Agente Intelligente per la categoria: {category.upper()}")
    
    # Configurazione dello stato iniziale per il grafo
    inputs = {
        "category": category,
        "articles": [],
        "digest_markdown": ""
    }
    
    # Esecuzione del grafo LangGraph compilato
    outputs = news_graph.invoke(inputs)
    
    processed_articles = outputs.get("articles", [])
    digest_md = outputs.get("digest_markdown", "")
    
    # 💾 SALVATAGGIO DEI RISULTATI NEI RISPETTIVI FILE STATICI SUL DISCO
    json_filename = f"{category}_news.json"
    md_filename = f"data/{category}_digest.md"
    
    with open(json_filename, "w", encoding="utf-8") as jf:
        json.dump(processed_articles, jf, ensure_ascii=False, indent=4)
    print(f"💾 [File System] Database JSON salvato: {json_filename} ({len(processed_articles)} articoli)")
    
    with open(md_filename, "w", encoding="utf-8") as mf:
        mf.write(digest_md)
    print(f"💾 [File System] Digest settimanale generato in: {md_filename}")
    
    # Sincronizzazione asincrona su GitHub Pages tramite Git
    auto_push_to_github(json_filename, md_filename)
    
    return {
        "category": category,
        "total_processed": len(processed_articles),
        "has_digest": len(digest_md) > 0
    }

def aggiornamento_automatico_totale():
    """Rinfresca ciclicamente tutti e tre i canali informativi verticali"""
    print(f"\n⏰ [Scheduler] Avvio della rassegna pianificata del {datetime.now()}")
    for cat in ["tech", "legal", "procurement"]:
        try:
            GLOBAL_STATUS[cat]["running"] = True
            GLOBAL_STATUS[cat]["message"] = "Aggiornamento pianificato in corso"
            esegui_workflow_news(cat)
            GLOBAL_STATUS[cat]["running"] = False
            GLOBAL_STATUS[cat]["message"] = "Completato"
            GLOBAL_STATUS[cat]["updated_at"] = datetime.now().isoformat()
        except Exception as e:
            GLOBAL_STATUS[cat]["running"] = False
            GLOBAL_STATUS[cat]["message"] = f"Errore: {str(e)}"
            print(f"🚨 [Scheduler] Fallimento aggiornamento automatico per {cat}: {e}")

# --- M6: FUNZIONE DI TARGET PER BACKGROUND TASK ---
def background_refresh_task(category: str):
    try:
        GLOBAL_STATUS[category]["running"] = True
        GLOBAL_STATUS[category]["message"] = "Analisi fonti e generazione riassunti AI in corso..."
        GLOBAL_STATUS[category]["updated_at"] = None
        
        esegui_workflow_news(category)
        
        GLOBAL_STATUS[category]["running"] = False
        GLOBAL_STATUS[category]["message"] = "Completato con successo"
        GLOBAL_STATUS[category]["updated_at"] = datetime.now().isoformat()
    except Exception as e:
        GLOBAL_STATUS[category]["running"] = False
        GLOBAL_STATUS[category]["message"] = f"Errore: {str(e)}"
        GLOBAL_STATUS[category]["updated_at"] = datetime.now().isoformat()
        print(f"❌ [API Task] Errore nel task in background per {category}: {e}")

# ==============================================================================
# 🌐 ENDPOINTS ENDPOINTS API (REST INTEGRATE PER INTERFACCIA WEB)
# ==============================================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Graphyte AI Intelligence Engine Backend",
        "endpoints": ["/api/refresh/{category}", "/api/status/{category}"]
    }

# --- M5: NUOVO ENDPOINT PER INTERROGARE LO STATO IN TEMPO REALE ---
@app.get("/api/status/{category}")
def get_status(category: str):
    cat = category.lower()
    if cat not in GLOBAL_STATUS:
        return {"status": "error", "message": "Categoria non valida"}
    return GLOBAL_STATUS[cat]

# --- M6: ENDPOINT REFRESH ASINCRONO CON BACKGROUND TASK (Risolve C12) ---
@app.post("/api/refresh/{category}")
def trigger_refresh(category: str, background_tasks: BackgroundTasks):
    cat = category.lower()
    if cat not in GLOBAL_STATUS:
        return {"status": "error", "message": "Categoria non valida"}
    
    if GLOBAL_STATUS[cat]["running"]:
        return {"status": "ignored", "message": "Un aggiornamento per questa categoria è già in esecuzione"}
    
    # Lanciamo il lavoro pesante in background liberando subito la risposta HTTP
    background_tasks.add_task(background_refresh_task, cat)
    return {"status": "started", "message": f"Aggiornamento asincrono avviato per {cat}"}


# --- SCHEDULER AUTOMATICO INTERVALLATO ---
scheduler = BackgroundScheduler()
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)


# ==============================================================================
# 🚀 AVVIO DIRETTO E FORZATO DEL SERVER
# ==============================================================================
if __name__ == "__main__":
    import os
    print("🖥️ Sincronizzazione inizializzata. Avvio server Uvicorn...")
    
    # Se siamo su Render prende la porta dinamica, altrimenti usa la 8000 locale
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main.py:app", host="0.0.0.0", port=port, reload=False)