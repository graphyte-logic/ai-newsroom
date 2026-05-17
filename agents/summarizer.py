from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def summarize_articles(articles: list) -> list:
    """Usa Claude per generare micro-riassunti d'impatto in italiano"""
    summaries = []
    
    for article in articles[:10]:  # Top 10
        source_lower = article.get('source', '').lower()
        is_legal = "diritto" in source_lower or "legal" in source_lower or "fonte legal" in source_lower
        
        # Prepariamo un contesto pulito per l'IA
        titolo = article.get('title', '')
        contenuto = article.get('summary', '')[:400]
        
        if is_legal:
            prompt = f"""Riassumi questa notizia giuridica in modo ultra-conciso.
Titolo: {titolo}
Contenuto: {contenuto}

REGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano. 
Vai dritto al sodo (cosa stabilisce la norma/sentenza). Non scrivere introduzioni o formule di errore."""
        else:
            prompt = f"""Riassumi questa notizia tech in modo ultra-conciso.
Titolo: {titolo}
Contenuto: {contenuto}

REGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano.
Evidenzia solo la novità tecnica o l'impatto. Non scrivere introduzioni o formule di errore."""

        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=80,  # Ridotto per costringerlo alla sintesi
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            summary_text = response.content[0].text.strip()
            
            # Pulizia di sicurezza nel caso l'IA usi virgolette iniziali
            if summary_text.startswith('"') and summary_text.endswith('"'):
                summary_text = summary_text[1:-1]
                
            summaries.append({
                "title": titolo,
                "url": article.get("url"),
                "source": article.get("source"),
                "summary": summary_text,
            })
        except Exception as e:
            print(f"Error summarizing {titolo}: {e}")
    
    return summaries