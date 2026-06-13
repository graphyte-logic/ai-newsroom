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
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

# --- C2: BLINDAGGIO ENCODING EMOJI PER WINDOWS / RENDER LOGS ---
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

# --- C11: LIFESPAN CONTEXT MANAGER ---
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

# --- CONFIGURAZIONE CORS MIDDLEWARE (Aperto e sicuro per l'integrazione Web) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
            # 🆔 [FIX IDENTITÀ AUTORE]: Configura subito l'identità locale per l'istanza del server
            print("🆔 [Git] Configurazione identità autore per il server...")
            subprocess.run(["git", "config", "user.email", "bot@graphyte-newsroom.local"], check=True)
            subprocess.run(["git", "config", "user.name", "Newsroom Bot"], check=True)
            
            # 🔗 RECUPERO E PULIZIA URL REMOTO: Rimuove spazi, virgolette e invii a capo accidentali da Render
            repo_url = os.environ.get("REPO_URL", "").strip().strip("'\"")
            if repo_url:
                print("🔗 [Git] Rilevato URL remoto dall'ambiente. Configurazione origin...")
                # Rimuove il vecchio origin in modo silente (evita scritte rosse di errore se non esiste)
                subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
            else:
                print("🏠 [Git] Nessuna variabile REPO_URL trovata. Si utilizza l'origin locale.")
            
            # 🔄 SCARICAMENTO CRONOLOGIA: Scarica lo stato remoto di GitHub senza spostare l'indice locale
            print("🔄 [Git] Esecuzione git fetch origin main...")
            subprocess.run(["git", "fetch", "origin", "main"], check=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            
            # 🌿 [FIX DETACHED HEAD]: Sgancia l'ambiente dal commit fantasma e lo ancora al branch main di GitHub
            # Mantiene intatti e non modificati i file JSON/MD appena scritti nella cartella locale
            print("🌿 [Git] Forzatura checkout e allineamento controllato su branch main...")
            subprocess.run(["git", "checkout", "-B", "main"], check=True)
            subprocess.run(["git", "reset", "--mixed", "origin/main"], check=True)
            
            # Forza l'aggiunta dei file appena generati all'area di staging
            subprocess.run(["git", "add", json_file, md_file], check=True)
            
            # 🔍 VERIFICA MODIFICHE REALI: Evita commit vuoti se Claude produce gli stessi identici risultati
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not status.stdout.strip():
                print("💤 [Git] Nessuna reale variazione di dati rispetto a GitHub. Salto il push.")
                return
            
            # Esecuzione del commit sicuro con timestamp aggiornato
            print("📝 [Git] Creazione del commit automatico...")
            subprocess.run([
                "git", "commit", "-m", 
                f"⚡ Auto-update {json_file}/{md_file}: {datetime.now().strftime('%H:%M:%S')}"
            ], check=True)
            
            # 📤 Invio definitivo delle modifiche al repository remoto su branch main
            print("📤 [Git] Invio delle modifiche al repository remoto (git push)...")
            subprocess.run(["git", "push", "origin", "main"], check=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            print(f"✅ [Git] Push completato con successo per {json_file} e {md_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ [Git] Errore critico durante le operazioni git: {e}")
        except Exception as ex:
            print(f"❌ [Git] Errore imprevisto nella pipeline Git: {ex}")
            
            
def esegui_workflow_news(category: str):
    """Esegue il workflow in modalità sincrona (usato dallo scheduler o dai cron job)"""
    print(f"🔄 [Scheduler] Avvio workflow sincrono per la categoria: {category}")
    try:
        inputs = {
            "category": category,
            "articles": [],
            "summaries": [],
            "digest": ""
        }
        
        final_state = news_graph.invoke(inputs)
        
        summaries = final_state.get("summaries", [])
        digest_md = final_state.get("digest", "")
        
        json_file = f"{category}_news.json"
        md_file = f"data/{category}_digest.md"
        
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
            
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(digest_md)
            
        auto_push_to_github(json_file, md_file)
        return f"Successo: elaborati {len(summaries)} articoli."
    except Exception as e:
        print(f"❌ [Scheduler Errore] Fallimento nel workflow sincrono: {e}")
        traceback.print_exc()
        raise e

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

def background_refresh_task(category: str):
    """Esegue l'aggiornamento asincrono lanciato dalle API REST"""
    try:
        GLOBAL_STATUS[category]["running"] = True
        GLOBAL_STATUS[category]["message"] = "Analisi fontes e generazione riassunti AI in corso..."
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
# 🌐 ENDPOINTS API REST (GRAPH INTERFACE & MONITORING)
# ==============================================================================

@app.get("/healthcheck")
def healthcheck():
    return {"status": "online", "backend": "Graphyte Workflow Engine attivo"}

@app.get("/ping-diagnostico")
def ping_diagnostico():
    return {"status": "success", "message": "FastAPI riceve correttamente le chiamate su Render!"}

@app.get("/api/status/{category}")
def get_status(category: str):
    cat = category.lower()
    if cat not in GLOBAL_STATUS:
        return {"status": "error", "message": "Categoria non valida"}
    return GLOBAL_STATUS[cat]

@app.post("/api/refresh/{category}")
def trigger_refresh(category: str, background_tasks: BackgroundTasks):
    cat = category.lower()
    if cat not in GLOBAL_STATUS:
        return {"status": "error", "message": "Categoria non valida"}
    
    if GLOBAL_STATUS[cat]["running"]:
        return {"status": "ignored", "message": "Un aggiornamento per questa categoria è già in esecuzione"}
    
    background_tasks.add_task(background_refresh_task, cat)
    return {"status": "started", "message": f"Aggiornamento asincrono avviato per {cat}"}


# ==============================================================================
# 📁 MOUNT FILE STATICI (FRONTEND & DATABASE JSON)
# ==============================================================================
app.mount("/", StaticFiles(directory=".", html=True), name="static")


# --- SCHEDULER AUTOMATICO INTERVALLATO ---
scheduler = BackgroundScheduler()
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)


# ==============================================================================
# 🚀 AVVIO DIRETTO DEL SERVER SU PORTA DINAMICA
# ==============================================================================
if __name__ == "__main__":
    print("🖥️ Sincronizzazione inizializzata. Avvio server Uvicorn...")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)