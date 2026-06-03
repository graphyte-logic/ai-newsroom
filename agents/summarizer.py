import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic
from dotenv import load_dotenv

# Carica il file .env se sei in locale (sul server Render non farà nulla perché la chiave è già nel sistema)
load_dotenv()

# Prende la chiave direttamente dall'ambiente di sistema
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("⚠️ ERRORE: La variabile ANTHROPIC_API_KEY non è stata configurata!")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL_HEAVY = "claude-sonnet-4-6"
MODEL_LIGHT = "claude-haiku-4-5"

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


def _gatekeeper_haiku(article: dict, category: str) -> bool:
    """
    PASSAGGIO 1 (Fast Filter): Usa Haiku per scartare in < 1 secondo le notizie fuori contesto.
    Abbatte i costi e i tempi non inviando spazzatura a Opus.
    """
    titolo = article.get('title', '')
    contenuto = _truncate(article.get('summary') or article.get('description') or '', limit=300)

    if category == "procurement":
        prompt = f"""Analyze this article:
Title: {titolo}
Content: {contenuto}

Is this article strictly relevant to corporate procurement, supply chain strategy, third-party vendor management, or ICT banking regulations (like DORA, EBA guidelines)?
Reply ONLY with the exact word YES or NO. Do not add any other text."""
        
        res = _call_claude(prompt, MODEL_LIGHT, max_tokens=10).upper()
        return "YES" in res
        
    return True # Tech e Legal usano già Haiku nel passaggio principale


def _process_procurement(article: dict) -> dict | None:
    """
    PASSAGGIO 2 (Deep Extraction): Opus riceve SOLO articoli pre-validati da Haiku.
    Nessun check di pertinenza nel prompt, dritti alla generazione XML.
    """
    titolo = article.get('title', '')
    contenuto = _truncate(article.get('summary') or article.get('description') or '')
    fonte = article.get('source', '')
    priority = article.get('priority', 'medium')

    prompt = f"""You are an intelligence analyst specialized in corporate procurement, supply chain strategy, third-party risk management (TPRM), and financial compliance (EBA, DORA).

Input Article to Analyze:
Title: {titolo}
Content: {contenuto}
Source Context: {fonte} (Priority: {priority.upper()})

Task: This article has already been pre-screened as relevant. Write your deep analysis strictly wrapped in the XML tags specified below. 

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

Do not include any JSON brackets, introductory text, or markdown code blocks."""

    try:
        raw_res = _call_claude(prompt, MODEL_HEAVY, max_tokens=600)
        
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

        if not parsed_json["summary"]:
            return None

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
        # Prompt corretto: ora accetta anche Consultation Papers, Guidelines e Framework normativi
        prompt = f"""You are an expert tech lawyer and regulatory compliance analyst specialized in digital law.
Analyze this article:
Title: {titolo}
Content: {contenuto}

CRITICAL LEGAL FILTER: Does this article cover regulatory updates, relevant court rulings/judgments, consultation papers (e.g., EBA/ESMA), digital law, privacy, or legislative frameworks applied to tech/banking (like DORA, AI Act)?
- If it is NOT related to these topics, return exactly: REJECT
- If YES, write a single impactful summary sentence in perfect Italian (max 25 words). Explain what the regulation, ruling, or guideline establishes. Do not use introductory phrases or markdown."""
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
        # Attiva il filtro rapido prima di consumare token Opus
        if not _gatekeeper_haiku(article, category):
            print(f"⏩ [Gatekeeper] Articolo scartato da Haiku: {article.get('title')}")
            return None
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