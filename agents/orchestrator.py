from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from agents.news_fetcher import fetch_all_news
from agents.summarizer import summarize_articles
from sources.sources_config import KEYWORDS

class NewsState(TypedDict):
    articles: List[dict]
    summaries: List[dict]
    digest: str

def fetch_news_node(state: NewsState) -> NewsState:
    """Fetch from all sources"""
    print("Fetching news...")
    articles = fetch_all_news()
    
    # Filter by keywords
    filtered = [
        a for a in articles
        if any(kw.lower() in a.get("title", "").lower() for kw in KEYWORDS)
    ]
    
    state["articles"] = filtered[:20]  # Top 20
    print(f"Found {len(state['articles'])} relevant articles")
    return state

def summarize_node(state: NewsState) -> NewsState:
    """Summarize top articles con Claude"""
    print("Summarizing articles...")
    summaries = summarize_articles(state["articles"])
    state["summaries"] = summaries
    print(f"Summarized {len(summaries)} articles")
    return state

def generate_digest_node(state: NewsState) -> NewsState:
    """Generate digest with formatted messages"""
    from datetime import datetime
    
    digest = ""
    
    # Header
    digest += f"```\n🤖 TECH & AI DIGEST\n{datetime.now().strftime('%A %d %B %Y')}\n```\n\n"
    
    # Articles
    for i, summary in enumerate(state["summaries"][:8], 1):
        title = summary['title']
        source = summary['source']
        text = summary['summary']
        url = summary['url']
        
        # Format con separatori
        digest += f"""**{i}. {title}**
└─ 📰 *{source}*
{text}
> [🔗 Read full article]({url})

"""
    
    # Footer
    digest += "━━━━━━━━━━━━━━━━━━━━━━━━\n*Powered by AI Newsroom*"
    
    state["digest"] = digest
    return state

def build_news_graph():
    """Build LangGraph workflow"""
    from langgraph.graph import START
    
    graph = StateGraph(NewsState)
    
    graph.add_node("fetch", fetch_news_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("generate", generate_digest_node)
    
    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()

# Global instance
news_graph = build_news_graph()