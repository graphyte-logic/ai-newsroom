# AI Newsroom 🤖

Autonomous system that aggregates tech, AI, legal, and procurement news, summarizes and analyzes them with Claude, and displays them on a premium integrated web dashboard via LangGraph orchestration.

## Features

- **Multi-source aggregation:** HackerNews + customizable RSS feeds (EBA, ESMA, EC Finance, Spend Matters, dev.to, TechCrunch, etc.).
- **Intelligent filtering:** Keyword-based relevance detection and Jaccard Term Similarity deduplication.
- **Claude-powered analysis:** Generates single impactful summaries in Italian for Tech & Legal, and comprehensive structural risk analyses (Why It Matters, Action Items, impact levels, executive warnings) for Procurement.
- **Integrated Web Dashboard:** Premium, responsive dashboard with glassmorphic cards, fluid gradients, hover effects, and real-time refresh status.
- **Unified FastAPI backend:** The API server directly hosts the static web interface, preventing CORS issues.
- **Scalable architecture:** Powered by LangGraph multi-agent workflow engines.

## Demo

Open the web interface to view live analyses and request manual on-demand updates:
- 🎯 Filtered tech, legal, and compliance news.
- 📝 Claude-generated Italian summaries and action items.
- ⚠️ Dynamic executive warnings for regulatory alerts.

## Setup

### Prerequisites
- Python 3.10+
- Anthropic API key (get at console.anthropic.com)

### 1. Clone & Install

```bash
git clone [https://github.com/YOUR_USERNAME/ai-newsroom.git](https://github.com/YOUR_USERNAME/ai-newsroom.git)
cd ai-newsroom
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Setup Environment

Create `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and configure:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Run Locally

```bash
python main.py
```

Open your browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

You will see the main hub dashboard. From there you can:
- View current aggregated articles.
- Trigger manual updates by clicking the **"Aggiorna Ora"** button on each channel (updates run asynchronously via background tasks).

## Customization

### Change News Sources

Edit `sources/sources_config.py` and modify the `SOURCES` list:

```python
SOURCES = [
    {
        "name": "Your Source",
        "url": "https://example.com/rss",
        "category": "tech",  # tech, legal, procurement, market
        "priority": "high",
        "signal_type": "trend",
        ...
    }
]
```

### Change Keywords

Edit global inclusion/exclusion keywords in `sources/sources_config.py`:

```python
GLOBAL_KEYWORDS_INCLUDE = ["ai", "llm", "procurement", ...]
GLOBAL_KEYWORDS_EXCLUDE = ["crypto", ...]
```

### Automatic Posting & Scheduler

The background scheduler is configured in `main.py` and runs updates automatically at 8:00 AM and 6:00 PM:

```python
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=8, minute=0)
scheduler.add_job(aggiornamento_automatico_totale, 'cron', hour=18, minute=0)
```

## Deploy to Render or Railway

1. Push your repository to GitHub.
2. Create a Web Service on **Render** (or Railway).
3. Connect your GitHub repository.
4. Set the build command to:
   `pip install -r requirements.txt`
5. Set the start command to:
   `python main.py`
6. Add the environment variable:
   - `ANTHROPIC_API_KEY`: Your Anthropic API Key
7. Deploy.
8. Access your live application at the provided `.onrender.com` URL!

## Tech Stack

- **Orchestration:** LangGraph (StateGraph workflow engine)
- **LLM:** Claude (Anthropic API: Claude 3.5 Sonnet / Claude 3.5 Haiku)
- **News Sources:** HackerNews RSS, European Banking Authority, European Commission, ESMA, Dev.to, TechCrunch Fintech, Spend Matters.
- **Backend & Web Server:** Python + FastAPI
- **Web Frontend:** Vanilla HTML5, CSS3 (Glassmorphism, custom typography, animations), JavaScript (Fetch, polling).

## License

MIT

## Author

Claudio L.F.
