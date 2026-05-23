import json
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def summarize_articles(articles: list, category: str = "tech") -> list:
    """Usa Claude per generare micro-riassunti d'impatto o schede di procurement in italiano"""
    summaries = []
    
    # Filtro parole chiave per ottimizzare i passaggi su DORA/EBA
    keywords_filter = ["eba", "dora", "rts", "guidelines", "consultation", "third-party", "procurement", "sourcing", "outsourcing"]
    
    for article in articles[:15]:  # Analizziamo un pool leggermente più ampio per via dei filtri
        titolo = article.get('title', '')
        contenuto_grezzo = article.get('summary') or article.get('description') or ''
        contenuto = contenuto_grezzo[:500]
        fonte = article.get('source', '')
        tier = article.get('tier', 'Tier 3 (TREND)')
        
        if category == "procurement":
            # Applichiamo un controllo preventivo blando basato sulle tue parole chiave
            text_to_check = (titolo + " " + contenuto).lower()
            if not any(k in text_to_check for k in keywords_filter) and "Tier 1" not in fonte:
                continue # Salta gli articoli palesemente fuori focus prima della chiamata API
                
            prompt = f"""You are an intelligence analyst specialized in banking procurement, regulatory compliance (EBA, DORA), and AI.

Input Article to Analyze:
Title: {titolo}
Content: {contenuto}
Source Context: {fonte} (Priority: {tier})

Execute the following steps accurately:
STEP 1 – RELEVANCE FILTER: Keep only if related to banking/financial services AND (procurement, sourcing, outsourcing, third-party risk, EBA/ECB/DORA, ICT risk, AI in banking). If not relevant, return exactly: {{"not_relevant": true}}
STEP 2 – PRIORITY BOOST: Boost priority if EBA or DORA or cloud providers (AWS, Azure, Google) or vendor dependency risk are mentioned.
STEP 3 – CLASSIFICATION: Assign one: REGULATION / PROCUREMENT / AI_TECH / RISK / MARKET_SIGNAL
STEP 4 – OUTPUT CARD: Generate a strict JSON object with the keys specified below.
STEP 5 – ALERT: If regulatory compliance issue or strict deadline/guideline → set "regulatory_alert": true and write a 1-line warning.

Return ONLY a valid JSON object matching this schema, no markdown blocks, no extra text:
{{
    "title": "Max 12 words title in Italian",
    "summary": "Max 80 words analytical summary in Italian",
    "why_it_matters": "Why it matters for financial procurement in Italian",
    "classification": "REGULATION or PROCUREMENT or AI_TECH or RISK or MARKET_SIGNAL",
    "impact": "LOW or MEDIUM or HIGH",
    "horizon": "SHORT or MID or LONG",
    "action_item": "Clear actionable instruction for the procurement leader in Italian",
    "regulatory_alert": true_or_false,
    "executive_warning": "1-line strict critical warning in Italian if regulatory_alert is true, else empty string",
    "url": "{article.get('url')}",
    "source": "{fonte}"
}}"""
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022", # Sonnet garantisce un output JSON strutturato perfetto
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                text_res = response.content[0].text.strip()
                
                # Rimozione di blocchi markdown accidentali
                if text_res.startswith("```json"):
                    text_res = text_res[7:-3].strip()
                elif text_res.startswith("```"):
                    text_res = text_res[3:-3].strip()
                    
                parsed_json = json.loads(text_res)
                
                if "not_relevant" not in parsed_json:
                    summaries.append(parsed_json)
            except Exception as e:
                print(f"⚠️ Errore AI Procurement per '{titolo}': {e}")
                
        else:
            # Flusso Standard Tech & Legal preesistente
            source_lower = fonte.lower()
            is_legal = "diritto" in source_lower or "legal" in source_lower or "fonte legal" in source_lower or category == "legal"
            
            if is_legal:
                prompt = f"""Riassumi questa notizia giuridica in modo ultra-conciso.\nTitolo: {titolo}\nContenuto: {contenuto}\n\nREGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano. \nVai dritto al sodo (cosa stabilisce la norma/sentenza). Non scrivere introduzioni o formule di errore."""
            else:
                prompt = f"""Riassumi questa notizia tech in modo ultra-conciso.\nTitolo: {titolo}\nContenuto: {contenuto}\n\nREGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano.\nEvidenzia solo la novità tecnica o l'impatto. Non scrivere introduzioni o formule di errore."""

            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=80,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary_text = response.content[0].text.strip()
                
                if summary_text.startswith('I') and summary_text.endswith('\"'):
                    summary_text = summary_text[1:-1]
                    
                summaries.append({
                    "title": titolo,
                    "url": article.get("url"),
                    "source": fonte,
                    "summary": summary_text
                })
            except Exception as e:
                print(f"⚠️ Errore riassunto ordinario: {e}")
                
    return summaries