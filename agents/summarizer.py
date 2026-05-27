import json
import re
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
import sys
from pathlib import Path
   # Aggiunge la cartella principale del progetto al percorso di ricerca di Python
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL_HEAVY = "claude-opus-4-7"
MODEL_LIGHT = "claude-haiku-4-5-20251001"

MAX_ARTICLES = 15
MAX_PARALLEL = 8
CONTENT_TRUNCATE_CHARS = 500

AI_KEYWORDS = [
    "ai", "artificial intelligence", "intelligenza artificiale",
    "llm", "gpt", "claude", "openai", "nvidia", "machine learning",
    "deep learning", "neural", "copilot", "agent", "midjourney",
    "anthropic", "gemini"
]


def _truncate(text: str, limit: int = CONTENT_TRUNCATE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0] + "..."


def _call_claude(prompt: str, model: str, max_tokens: int) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def _parse_xml_field(text: str, tag: str) -> str:
    """Estrae in modo sicuro il contenuto all'interno di tag XML generati dall'LLM"""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _process_procurement(article: dict) -> dict | None:
    titolo = article.get('title', '')
    contenuto = _truncate(article.get('summary') or article.get('description') or '')
    fonte = article.get('source', '')
    priority = article.get('priority', 'medium')

    # Prompt basato su tag XML: immune a qualsiasi errore di punteggiatura o virgolette
    prompt = f"""You are an intelligence analyst specialized in corporate procurement, supply chain strategy, third-party risk management (TPRM), and financial compliance (EBA, DORA).

Input Article to Analyze:
Title: {titolo}
Content: {contenuto}
Source Context: {fonte} (Priority: {priority.upper()})

Execute the following steps accurately:
STEP 1 – RELEVANCE FILTER: Evaluate if related to modern corporate procurement, sourcing strategies, supply chain developments, third-party risk, vendor management, or banking regulations (EBA, DORA, ICT risk). If the text is completely out of scope, write <not_relevant>true</not_relevant>.
STEP 2 – GENERATE FIELDS: If relevant, write your analysis strictly wrapped in the XML tags specified below. 

Your entire response must follow exactly this format:
<title>Max 12 words title in Italian</title>
<summary>Max 80 words analytical summary in Italian</summary>
<why_it_matters>Why it matters for financial procurement in Italian</why_it_matters>
<classification>REGULATION or PROCUREMENT or AI_TECH or RISK or MARKET_SIGNAL</classification>
<impact>LOW or MEDIUM or HIGH</impact>
<horizon>SHORT or MID or LONG</horizon>
<action_item>Clear actionable instruction for the procurement leader in Italian</action_item>
<regulatory_alert>true or false</regulatory_alert>
<executive_warning>1-line strict critical warning in Italian if regulatory_alert is true, else leave empty</executive_warning>

Do not include any JSON brackets or markdown code blocks."""

    try:
        raw_res = _call_claude(prompt, MODEL_HEAVY, max_tokens=600)
        
        # Se Claude dichiara esplicitamente l'articolo non rilevante, lo scartiamo
        if "<not_relevant>true</not_relevant>" in raw_res:
            return None

        # Ricostruiamo il dizionario estraendo i dati dai tag XML (impossibile da rompere)
        parsed_json = {
            "title": _parse_xml_field(raw_res, "title") or titolo,
            "summary": _parse_xml_field(raw_res, "summary"),
            "why_it_matters": _parse_xml_field(raw_res, "why_it_matters"),
            "classification": _parse_xml_field(raw_res, "classification") or "PROCUREMENT",
            "impact": _parse_xml_field(raw_res, "impact") or "MEDIUM",
            "horizon": _parse_xml_field(raw_res, "horizon") or "MID",
            "action_item": _parse_xml_field(raw_res, "action_item"),
            "regulatory_alert": _parse_xml_field(raw_res, "regulatory_alert").lower() == "true",
            "executive_warning": _parse_xml_field(raw_res, "executive_warning")
        }

        # Controllo di sicurezza minimo per validare la scheda
        if not parsed_json["summary"]:
            return None

        # Arricchimento metadati stabili per il frontend
        parsed_json["url"] = article.get("url", "")
        parsed_json["source"] = fonte
        parsed_json["geo"] = article.get("geo", "global")
        parsed_json["signal_type"] = article.get("signal_type", "trend")
        parsed_json["sub_category"] = article.get("sub_category", "General")
        
        return parsed_json
        
    except Exception as e:
        print(f"⚠️ Errore AI Procurement per '{titolo}': {e}")
        return None


def _process_tech_or_legal(article: dict, category: str) -> dict | None:
    titolo = article.get('title', '')
    contenuto = _truncate(article.get('summary') or article.get('description') or '')
    fonte = article.get('source', '')

    is_legal = category == "legal" or article.get("signal_type") == "regulatory"

    if is_legal:
        # Prompt perfettamente allineato al perimetro della stanza Legal
        prompt = f"""You are an expert tech lawyer and regulatory compliance analyst specialized in digital law.
Analyze this article:
Title: {titolo}
Content: {contenuto}

CRITICAL LEGAL FILTER: Does this article cover regulatory updates, relevant court rulings/judgments, digital law, privacy/GDPR, data protection, or legislation applied to new technologies (like AI Act, cybersecurity frameworks, crypto regulations)?
- If it is NOT related to tech law, digital regulation, court rulings, or privacy (e.g., general retail banking news, standard corporate finance, macroeconomic policies), return exactly: REJECT
- If YES, write a single impactful summary sentence in perfect Italian (max 25 words). Go straight to the point, explaining what the regulation, ruling, or legal update establishes. Do not use introductory phrases or markdown backticks."""
    else:
        text_to_check = (titolo + " " + contenuto).lower()
        if not any(k in text_to_check for k in AI_KEYWORDS):
            return None

        prompt = f"""You are an expert AI technology analyst.
Analyze this technical article:
Title: {titolo}
Content: {contenuto}

CRITICAL FILTER: Is this article strictly about Artificial Intelligence, Generative AI, LLMs, hardware accelerators, or closely related AI infrastructure?
If NO, return exactly: REJECT
If YES, write a single impactful sentence in perfect Italian (max 25 words) summarizing the AI innovation or its direct impact. Do not include introductions, markdown or error formulas."""

    try:
        summary_text = _call_claude(prompt, MODEL_LIGHT, max_tokens=120)

        # Se il prompt restituisce REJECT (sia per legal che per tech), l'articolo viene scartato
        if "REJECT" in summary_text:
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
            "sub_category": article.get("sub_category", "General"),
        }
    except Exception as e:
        print(f"⚠️ Errore riassunto ordinario ({category}): {e}")
        return None


def _process_single(article: dict, category: str) -> dict | None:
    if category == "procurement":
        return _process_procurement(article)
    return _process_tech_or_legal(article, category)


def summarize_articles(articles: list, category: str = "tech") -> list:
    """Distribuisce l'elaborazione degli articoli su un pool di thread paralleli"""
    if not articles:
        return []

    pool = articles[:MAX_ARTICLES]
    workers = min(len(pool), MAX_PARALLEL)
    print(f"🚀 Concorrenza attiva: {workers} chiamate parallele a Claude su {len(pool)} articoli...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda art: _process_single(art, category), pool))

    return [r for r in results if r is not None]