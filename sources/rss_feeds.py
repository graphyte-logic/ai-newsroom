import feedparser
from datetime import datetime, timedelta
from .sources_config import FEEDS

def fetch_rss_feeds(hours_back=24):
    """Fetch articles from RSS feeds"""
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    for feed_key, feed_config in FEEDS.items():
        if feed_key == "hackernews":
            continue  # Handle separately
        
        try:
            feed = feedparser.parse(feed_config["url"])
            for entry in feed.entries[:10]:
                # Try to parse published time
                pub_time = None
                if "published_parsed" in entry:
                    pub_time = datetime(*entry.published_parsed[:6])
                else:
                    pub_time = datetime.now()
                
                if pub_time > cutoff_time:
                    articles.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": feed_config["name"],
                        "timestamp": pub_time.timestamp(),
                        "summary": entry.get("summary", "")[:200],
                    })
        except Exception as e:
            print(f"Error fetching {feed_key}: {e}")
    
    return articles