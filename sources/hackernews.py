import requests
from datetime import datetime, timedelta

def fetch_hackernews_top(limit=30, hours_back=24):
    """Fetch top HN stories from last N hours"""
    
    # HN API: Get top story IDs
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        response = requests.get(top_stories_url, timeout=10)
        top_ids = response.json()[:limit]
    except Exception as e:
        print(f"Error fetching HN top stories: {e}")
        return []
    
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    for story_id in top_ids:
        try:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            item = requests.get(item_url, timeout=5).json()
            
            if item and "time" in item:
                post_time = datetime.fromtimestamp(item["time"])
                if post_time > cutoff_time:
                    articles.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "source": "HackerNews",
                        "timestamp": item["time"],
                        "score": item.get("score", 0),
                    })
        except Exception as e:
            print(f"Error fetching HN item {story_id}: {e}")
            continue
    
    return sorted(articles, key=lambda x: x["score"], reverse=True)
