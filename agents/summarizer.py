from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def summarize_articles(articles: list) -> list:
    """Use Claude to summarize articles"""
    summaries = []
    
    for article in articles[:10]:  # Top 10
        prompt = f"""Given this tech/AI news article:

Title: {article.get('title', '')}
Source: {article.get('source', '')}
Summary/Content: {article.get('summary', '')[:300]}

Provide a 2-3 sentence summary focused on:
1. What happened
2. Why it matters for developers
3. Any actionable insight

Be concise and technical. Keep it under 150 chars."""
        
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            summary_text = response.content[0].text
            
            summaries.append({
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source"),
                "summary": summary_text,
            })
        except Exception as e:
            print(f"Error summarizing {article.get('title')}: {e}")
    
    return summaries