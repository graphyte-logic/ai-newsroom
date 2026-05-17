from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def summarize_articles(articles: list) -> list:
    """Usa Claude per riassumere gli articoli adattando il contesto (Tech o Legal)"""
    summaries = []
    
    for article in articles[:10]:  # Top 10
        # Rileviamo se l'articolo appartiene al ramo legale o tecnologico
        # Controllando la fonte o le parole chiave
        source_lower = article.get('source', '').lower()
        is_legal = "diritto" in source_lower or "legal" in source_lower or "fonte legal" in source_lower
        
        if is_legal:
            # Prompt specialistico per notizie giuridiche e normative
            prompt = f"""Analizza questo articolo/provvedimento legale italiano:

Titolo: {article.get('title', '')}
Fonte: {article.get('source', '')}
Contenuto: {article.get('summary', '')[:400]}

Fornisci un riassunto di 2-3 frasi focalizzato su:
1. Cosa stabilisce la norma, sentenza o notizia
2. Quali sono le implicazioni principali per professionisti o imprese
3. Eventuali scadenze o azioni immediate

RISPONDI TASSATIVAMENTE IN LINGUA ITALIANA. Mantieni un tono chiaro, autorevole e conciso."""
        else:
            # Prompt specialistico per il ramo tecnologico
            prompt = f"""Given this tech/AI news article:

Title: {article.get('title', '')}
Source: {article.get('source', '')}
Summary/Content: {article.get('summary', '')[:400]}

Fornisci un riassunto di 2-3 frasi focalizzato su cosa è successo e l'impatto tecnico.
RISPONDI TASSATIVAMENTE IN LINGUA ITALIANA. Mantieni il testo fluido, compatto e professionale."""

        try:
            # Chiamata a Claude
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=250, # Alzato leggermente per permettere un italiano fluente senza tagli
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            summary_text = response.content[0].text.strip()
            
            summaries.append({
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source"),
                "summary": summary_text,
            })
        except Exception as e:
            print(f"Error summarizing {article.get('title')}: {e}")
    
    return summaries