import json
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def summarize_articles(articles: list, category: str = "tech") -> list:
    """Usa Claude per generare micro-riassunti d'impatto o schede di procurement in italiano"""
    summaries = []
    
    # Filtro parole chiave per ottimizzare i passaggi su DORA/EBA (Procurement)
    keywords_filter = ["eba", "dora", "rts", "guidelines", "consultation", "third-party", "procurement", "sourcing", "outsourcing"]
    
    # Filtro parole chiave stringenti per canale Tech verticale su AI
    ai_keywords = ["ai", "artificial intelligence", "intelligenza artificiale", "llm", "gpt", "claude", "openai", "nvidia", "machine learning", "deep learning", "neural", "copilot", "agent", "midjourney", "anthropic", "gemini"]

    for article in articles[:15]:  # Analizziamo un pool di massimo 15 articoli filtrati
        titolo = article.get('title', '')
        contenuto_grezzo = article.get('summary') or article.get('description') or ''
        contenuto = contenuto_grezzo[:500]
        fonte = article.get('source', '')
        tier = article.get('tier', 'Tier 3 (TREND)')
        
        # ----------------------------------------------------
        # FLUSSO 1: PROCUREMENT & COMPLIANCE
        # ----------------------------------------------------
        if category == "procurement":
            # Controllo preventivo basato sulle parole chiave normative
            text_to_check = (titolo + " " + contenuto).lower()
            if not any(k in text_to_check for k in keywords_filter) and "Tier 1" not in fonte:
                continue # Salta gli articoli fuori focus prima della chiamata API
                
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
    "executive_warning": "1-line strict critical warning in Italian if regulatory_alert is true, else empty string"
}}"""
            try:
                response = client.messages.create(
                    model="claude-opus-4-6", 
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                text_res = response.content[0].text.strip()
                
                if text_res.startswith("```json"):
                    text_res = text_res[7:-3].strip()
                elif text_res.startswith("```"):
                    text_res = text_res[3:-3].strip()
                    
                parsed_json = json.loads(text_res)
                
                if "not_relevant" not in parsed_json:
                    parsed_json["url"] = article.get("url", "")
                    parsed_json["source"] = fonte
                    summaries.append(parsed_json)
            except Exception as e:
                print(f"⚠️ Errore AI Procurement per '{titolo}': {e}")
                
        # ----------------------------------------------------
        # FLUSSO 2: TECH AI VERTICAL o LEGAL
        # ----------------------------------------------------
        else:
            source_lower = fonte.lower()
            is_legal = "diritto" in source_lower or "legal" in source_lower or "fonte legal" in source_lower or category == "legal"
            
            if is_legal:
                # Flusso Ordinario Legal
                prompt = f"""Riassumi questa notizia giuridica in modo ultra-conciso.\nTitolo: {titolo}\nContenuto: {contenuto}\n\nREGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano. \nVai dritto al sodo (cosa stabilisce la norma/sentenza). Non scrivere introduzioni o formule di errore."""
            else:
                # Pre-filtraggio locale per eliminare tech generico non-AI
                text_to_check = (titolo + " " + contenuto).lower()
                if not any(k in text_to_check for k in ai_keywords):
                    continue  # Salta a piè pari l'articolo senza interrogare l'API
                    
                # Guardiano LLM per scartare notizie borderline prive di AI pura
                prompt = f"""You are an expert AI technology analyst.
Analyze this technical article:
Title: {titolo}
Content: {contenuto}

CRITICAL FILTER: Is this article strictly about Artificial Intelligence, Generative AI, LLMs, neural hardware, or closely related AI infrastructure? 
If NO, return exactly: REJECT
If YES, write a single impactful sentence in perfect Italian (max 25 words) summarizing the AI innovation or its direct impact. Do not include introductions, markdown or error formulas."""

            try:
                response = client.messages.create(
                    model="claude-opus-4-6", 
                    max_tokens=80,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary_text = response.content[0].text.strip()
                
                # Se Claude rifiuta l'articolo Tech perché non incentrato sull'AI, lo scartiamo
                if not is_legal and "REJECT" in summary_text:
                    continue
                
                if summary_text.startswith('"') and summary_text.endswith('"'):
                    summary_text = summary_text[1:-1]
                    
                summaries.append({
                    "title": titolo,
                    "url": article.get("url"),
                    "source": fonte,
                    "summary": summary_text
                })
            except Exception as e:
                print(f"⚠️ Errore riassunto ordinario ({category}): {e}")
                
    return summaries