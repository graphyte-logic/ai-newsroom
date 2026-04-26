# AI Newsroom 🤖

Autonomous system that aggregates tech & AI news, summarizes with Claude, and publishes to Discord via LangGraph orchestration.

## Features

- **Multi-source aggregation:** HackerNews + RSS feeds (customizable)
- **Intelligent filtering:** Keyword-based relevance detection
- **Claude-powered summaries:** 2-3 sentence summaries for each article
- **Discord integration:** Beautiful embeds, daily automated posts
- **Scalable architecture:** LangGraph multi-agent orchestration
- **Low cost:** ~$3/month (Claude API only)

## Demo

Command: `!digest` in Discord

Outputs:
- 🎯 8 most relevant tech articles
- 📝 Claude-generated summaries
- 🔗 Direct links to full articles
- 📰 Source attribution

## Demo Video

[![AI Newsroom Demo](https://img.youtube.com/vi/u7h4ycIYW28/maxresdefault.jpg)](https://youtu.be/u7h4ycIYW28)

**[Watch the full demo](https://youtu.be/u7h4ycIYW28)** — Complete walkthrough of architecture, live Discord demo, and scalability.

## Architecture
HackerNews + RSS Feeds
↓
[LangGraph Orchestrator]
├─ Node 1: Fetch & Deduplicate
├─ Node 2: Filter by Keywords
├─ Node 3: Summarize with Claude
└─ Node 4: Format as Discord Embeds
↓
Discord Bot (automated 8 AM & 6 PM or manual !digest)

## Setup

### Prerequisites
- Python 3.10+
- Discord server (create free at discord.com)
- Anthropic API key (get at console.anthropic.com)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-newsroom.git
cd ai-newsroom
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. New Application → name "AI Newsroom"
3. Tab "Bot" → Add Bot
4. Copy TOKEN
5. Enable "Message Content Intent" under Privileged Gateway Intents
6. OAuth2 → URL Generator:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `View Channels`
7. Use generated URL to invite bot to your server

### 3. Setup Environment

```bash
cp .env.example .env
```

Edit `.env`:

ANTHROPIC_API_KEY=sk-ant-your-key-here
DISCORD_TOKEN=your-bot-token-here
DATABASE_URL=postgresql://user:pass@host/dbname


### 4. Get Discord Channel ID

- Enable Developer Mode: User Settings → Advanced → Developer Mode
- Right-click channel → Copy Channel ID
- Edit `discord_client.py`, find `NEWS_CHANNEL_ID = None` → replace with your ID

### 5. Run Locally

```bash
python main.py
```

Bot will:
- Post at 8 AM & 6 PM (configurable in `config.py`)
- Respond to `!digest` command in Discord

## Customization

### Change News Sources

Edit `sources/sources_config.py`:

```python
FEEDS = {
    "hackernews": {...},
    "your_feed": {
        "url": "https://example.com/rss",
        "name": "Your Feed",
        "weight": 1
    }
}
```

### Change Keywords

Edit `KEYWORDS` list in `sources/sources_config.py`:

```python
KEYWORDS = ["AI", "LLM", "Claude", "your-keyword", ...]
```

### Change Posting Times

Edit `config.py`:

```python
MORNING_HOUR = 8  # Change to desired hour
EVENING_HOUR = 18
```

### Change Number of Articles

In `agents/orchestrator.py`, change `[:8]` to desired count:

```python
for i, summary in enumerate(state["summaries"][:8], 1):  # Change 8
```

## Deploy to Railway

1. Push to GitHub
2. Go to https://railway.app
3. New Project → Deploy from GitHub
4. Select this repo
5. Add environment variables in Railway dashboard
6. Deploy

Bot runs 24/7 without your computer.

## Extend to Other Verticals

**Finance News:**
```python
KEYWORDS = ["crypto", "trading", "bitcoin", "fintech", "SEC", "IPO"]
FEEDS = {
    "cointelegraph": {"url": "https://cointelegraph.com/rss", ...},
    "finance_feeds": {...}
}
```

**Legal News:**
```python
KEYWORDS = ["law", "regulation", "GDPR", "compliance", "court", "legal"]
FEEDS = {
    "legal_blogs": {...},
    "gov_notices": {...}
}
```

**DevOps News:**
```python
KEYWORDS = ["Kubernetes", "Docker", "DevOps", "CI/CD", "infrastructure"]
FEEDS = {
    "devops_digest": {...}
}
```

## Costs

| Component | Cost/Month |
|-----------|-----------|
| Claude API | ~$3 |
| Discord Bot | Free |
| Railway (free tier) | Free |
| **Total** | **~$3** |

Scales: 2 digests/day × 30 days × ~$0.05/digest = ~$3/month

## Tech Stack

- **Orchestration:** LangGraph
- **LLM:** Claude 3 (Anthropic)
- **News Sources:** HackerNews API, RSS feeds
- **Discord:** discord.py
- **Backend:** Python + FastAPI
- **Deployment:** Railway

## API Usage

Token cost per digest:
- Input: ~1,000 tokens (5 articles × 200 tokens each)
- Output: ~500 tokens (summaries)
- Total: ~1,500 tokens per digest
- Cost: ~$0.05 per digest (Claude 3 Sonnet pricing)

## Future Enhancements

- [ ] PostgreSQL storage + deduplication
- [ ] Web dashboard to view archive
- [ ] Custom digest scheduling per user
- [ ] Slack/Email integrations
- [ ] Sentiment analysis
- [ ] Topic clustering

## License

MIT

## Author

Claudio L.F.

---

**Portfolio Note:** This project demonstrates:
- Multi-agent orchestration (LangGraph)
- LLM integration at scale (Claude API)
- Production-grade patterns (dedup, scheduling, error handling)
- Real deployment (Railway)

Perfect for showcasing agentic AI systems to potential clients.

