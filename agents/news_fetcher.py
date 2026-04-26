from sources.hackernews import fetch_hackernews_top
from sources.rss_feeds import fetch_rss_feeds

def fetch_all_news():
    """Fetch from all sources and combine"""
    hn_articles = fetch_hackernews_top(limit=20, hours_back=12)
    rss_articles = fetch_rss_feeds(hours_back=12)
    
    # Combine and deduplicate by URL
    all_articles = hn_articles + rss_articles
    seen_urls = set()
    unique = []
    
    for article in all_articles:
        url = article.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)
    
    return unique