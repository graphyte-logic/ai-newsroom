import json
import subprocess
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

from agents.orchestrator import news_graph

app = FastAPI(title="Graphyte Intelligence Hub Backend")

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
            subprocess.run(["git", "add", json_file, md_file], check=True)
            subprocess.run([
                "git", "commit", "-m", 
                f"⚡ Auto-update {json_file}/{md_file}: {datetime.now().strftime('%H:%M:%S')}"
            ], check=True)
            subprocess.run(["git", "push", "origin", "master"], check=True)
            print(f"🚀 [GitHub] {json_file} e {md_file} pubblicati con successo!")
        except Exception as e:
            print(f"⚠️ [Git Error] Errore push GitHub: {e}")
        finally:
            print("🔓 [Lock Git] Operazioni completate. Lock rilasciato.")

def esegui_workflow_news(category: str):
    """Invocazione della pipeline LangGraph, salvataggio dei dati (JSON + MD) e push"""
    print(f"🔮 Avvio Rooms LangGraph per la stanza: {category.upper()}")
    
    config = {"configurable": {"thread_id": f"manual_{category}"}}
    inputs = {"category": category, "articles": [], "summaries": [], "digest": ""}
    
    data = news_graph.invoke(inputs, config=config)
    
    if data and "summaries" in data and len(data["summaries"]) > 0:
        if category == "legal":
            json_filename = "legal_news.json"
            md_filename = "data/digest_legal.md"
        elif category == "procurement":
            json_filename = "procurement_news.json"
            md_filename = "data/digest_procurement.md"
        else:
            json_filename = "news.json"
            md_filename = "data/digest_tech.md"

        notizie_salvabili = data["summaries"]
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(notizie_salvabili, f, ensure_ascii=False, indent=4)
        print(f"💾 [Locale] Salvate {len(notizie_salvabili)} notizie in {json_filename}")

        digest_text = data.get("digest", "*Nessun digest generato*")
        with open(md_filename, "w", encoding="utf-8") as f_md:
            f_md.write(digest_text)
        print(f"📝 [Locale] Report editoriale salvato in {md_filename}")
            
        auto_push_to_github(json_filename, md_filename)
        return {"status": "success", "count": len(notizie_salvabili)}
    else:
        print(f"📭 Nessuna notizia trovata o filtrata per la categoria {category}")
        return {"status": "empty", "count": 0}

def aggiornamento_automatico_totale():
    print(f"⏰ [Scheduler] Avvio aggiornamento programmato di tutte le sezioni")
    esegui_workflow_news("tech")
    esegui_workflow_news("legal")
    esegui_workflow_news("procurement")

@app.post("/api/refresh/{category}")
async def force_refresh(category: str):
    if category not in ["tech", "legal", "procurement"]:
        return {"status": "error", "message": "Categoria non valida"}
    try:
        res = esegui_workflow_news(category)
        return {"status": "success", "message": f"Aggiornamento {category} completato", "details": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- SCHEDULER AUTOMATICO INTERVALLATO ---
scheduler = BackgroundScheduler()
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)
scheduler.start()

# ==============================================================================
# 🚀 AVVIO DIRETTO E FORZATO DEL SERVER (SENZA COSTRUTTI AMBIGUI)
# ==============================================================================
print("🖥️ Sincronizzazione inizializzata. Avvio server Uvicorn...")
uvicorn.run(app, host="127.0.0.1", port=8000)