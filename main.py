import json
import subprocess
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
    
    config = {"configurable": {"thread_id": f"manual_{category}"}}
    inputs = {"category": category, "articles": [], "summaries": [], "digest": ""}
    
    compiled_graph = news_graph
    data = compiled_graph.invoke(inputs, config=config)
    
    if data and "summaries" in data and len(data["summaries"]) > 0:
        # Configurazione file in base alla categoria richiesta
        if category == "legal":
            filename = "legal_news.json"
            notizie_salvabili = data["summaries"]
        elif category == "procurement":
            filename = "procurement_news.json"
            notizie_salvabili = data["summaries"] # Preserviamo l'intera struttura ricca generata
        else:
            filename = "news.json"
            notizie_salvabili = data["summaries"]

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(notizie_salvabili, f, ensure_ascii=False, indent=4)
            
        print(f"💾 [Locale] Salvate {len(notizie_salvabili)} notizie in {filename}")
        auto_push_to_github(filename)
        return {"status": "success", "count": len(notizie_salvabili)}
    else:
        print(f"📭 Nessuna notizia trovata o filtrata per {category}")
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

# --- SCHEDULER AUTOMATICO ---
scheduler = BackgroundScheduler()
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)
scheduler.start()

if __name__ == "__main__":
    print("🖥️ Backend Graphyte attivo e in ascolto su http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)