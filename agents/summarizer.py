import json
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Filtri parole chiave riutilizzati come guardrail interni prima della chiamata API
KEYWORDS_FILTER = ["eba", "dora", "rts", "guidelines", "consultation", "third-party", "procurement", "sourcing", "outsourcing"]
AI_KEYWORDS = ["ai", "artificial intelligence", "intelligenza artificiale", "llm", "gpt", "claude", "openai", "nvidia", "machine learning", "deep learning", "neural", "copilot", "agent", "anthropic", "gemini"]

def process_single_article(article: dict, category: str) -> dict:
    """Esegue l'interrogazione atomica a Claude per un singolo articolo in modo isolato"""
    titolo = article.get('title', '')
    contenuto_grezzo = article.get('summary') or article.get('description') or ''
    fonte = article.get('source', '')
    tier = article.get('tier', 'Priority: MEDIUM')
    
    # Troncamento intelligente a 500 caratteri senza spaccare le parole
    if len(contenuto_grezzo) > 500:
        contenuto = contenuto_grezzo[:500].rsplit(' ', 1)[0] + "..."
    else:
        contenuto = contenuto_grezzo

    text_to_check = (titolo + " " + contenuto).lower()

    # ----------------------------------------------------
    # PROMPT CANALE 1: PROCUREMENT & COMPLIANCE
    # ----------------------------------------------------
    if category == "procurement":
        if not any(k in text_to_check for k in KEYWORDS_FILTER) and "HIGH" not in tier:
            return None
            
        prompt = f"""You are an intelligence analyst specialized in banking procurement, regulatory compliance (EBA, DORA), and AI.

Input Article to Analyze:
Title: {titolo}
Content: {contenuto}
Source Context: {fonte} ({tier})

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
                return {
                    **parsed_json,
                    "url": article.get("url", ""),
                    "source": fonte,
                    "geo": article.get("geo", "global"),
                    "sub_category": article.get("sub_category", "General")
                }
        except Exception as e:
            print(f"⚠️ Errore JSON Claude per '{titolo}': {e}")
            return None

    # ----------------------------------------------------
    # PROMPT CANALE 2 & 3: TECH AI VERTICAL o LEGAL
    # ----------------------------------------------------
    else:
        is_legal = category == "legal" or "regulatory" in article.get("category", "")
        
        if is_legal:
            prompt = f"Riassumi questa notizia giuridica in modo ultra-conciso.\nTitolo: {titolo}\nContenuto: {contenuto}\n\nREGOLA TASSATIVA: Scrivi un'unica frase di massimo 25 parole in perfetto italiano. Vai dritto al sodo (cosa stabilisce la norma/sentenza). Non scrivere introduzioni."
        else:
            if not any(k in text_to_check for k in AI_KEYWORDS):
                return None
                
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
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            summary_text = response.content[0].text.strip()
            
            if not is_legal and "REJECT" in summary_text:
                return None
            
            if summary_text.startswith('"') and summary_text.endswith('"'):
                summary_text = summary_text[1:-1]
                
            return {
                "title": titolo,
                "url": article.get("url"),
                "source": fonte,
                "summary": summary_text,
                "geo": article.get("geo", "global"),
                "signal_type": article.get("signal_type", "trend"),
                "sub_category": article.get("sub_category", "General")
            }
        except Exception as e:
            print(f"⚠️ Errore micro-riassunto Claude per '{titolo}': {e}")
            return None
    return None

def summarize_articles(articles: list, category: str = "tech") -> list:
    """Distribuisce l'elaborazione degli articoli su un pool di thread paralleli"""
    if not articles:
        return []
        
    pool_size = min(len(articles), 15)
    print(f"🚀 Concorrenza Attiva: Lancio di {pool_size} chiamate parallele simultanee a Claude...")
    
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = list(executor.map(lambda art: process_single_article(art, category), articles[:15]))
        
    # Filtra i None (articoli scartati dai guardrail o falliti)
    return [r for r in results if r is not None]