import json
import subprocess
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

from agents.orchestrator import news_graph

app = FastAPI(title="Graphyte Intelligence Hub Backend")

# Permettiamo alle pagine HTML locali o su GitHub di dialogare con questo script Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def auto_push_to_github(filename: str):
    """Sincronizza i database JSON direttamente su GitHub Pages"""
    try:
        subprocess.run(["git", "add", filename], check=True)
        subprocess.run(["git", "commit", "-m", f"⚡ Auto-update {filename}: {datetime.now().strftime('%H:%M:%S')}"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print(f"🚀 [GitHub] {filename} pubblicato con successo!")
    except Exception as e:
        print(f"⚠️ [Git Error] Errore push GitHub per {filename}: {e}")

def esegui_workflow_news(category: str):
    """Invocazione del grafo LangGraph e salvataggio dati"""
    print(f"🔮 Avvio elaborazione LangGraph per: {category.upper()}")
    state = {"articles": [], "summaries": [], "digest": "", "category": category}
    
    # Esecuzione del grafo
    result = news_graph.invoke(state)
    summaries = result.get("summaries", [])
    
    if summaries:
        filename = "news.json" if category == "tech" else "legal_news.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=4)
        print(f"✅ File {filename} salvato in locale.")
        auto_push_to_github(filename)
        return {"status": "success", "count": len(summaries)}
    else:
        print(f"📭 Nessuna notizia trovata per {category}")
        return {"status": "empty", "count": 0}

def aggiornamento_automatico_totale():
    """Esegue il giro completo di aggiornamento per entrambi i rami"""
    print(f"⏰ [Scheduler] Avvio aggiornamento programmato delle {datetime.now().strftime('%H:%M')}")
    esegui_workflow_news("tech")
    esegui_workflow_news("legal")

# --- ENDPOINT PER IL SITO WEB (FORZATURA MANUALE) ---
@app.post("/api/refresh/{category}")
async def force_refresh(category: str):
    """Endpoint chiamato dal tasto 'Aggiorna' sul sito web"""
    if category not in ["tech", "legal"]:
        return {"status": "error", "message": "Categoria non valida"}
    
    try:
        res = esegui_workflow_news(category)
        return {"status": "success", "message": f"Aggiornamento {category} completato", "details": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- SCHEDULER (ORARI AUTOMATICI: 08:00 e 18:00) ---
scheduler = BackgroundScheduler()
# Aggiornamento ore 08:00
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
# Aggiornamento ore 18:00
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)
scheduler.start()

if __name__ == "__main__":
    print("🖥️ Backend Graphyte attivo e in ascolto su http://127.0.0.1:8000")
    print("⏰ Automazioni configurate per le ore 08:00 e 18:00.")
    uvicorn.run(app, host="127.0.0.1", port=8000)