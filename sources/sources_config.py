# ==============================================================================
# 🌐 CONFIGURAZIONE UNIFICATA FONTI INTELLIGENTI
# ==============================================================================

SOURCES = [
    # =========================
    # 🔴 REGULATORY / LEGAL (ALTA PRIORITÀ)
    # =========================
    {
        "name": "EBA News",
        "url": "https://www.eba.europa.eu/news-press/news/rss.xml",
        "category": "regulatory",
        "sub_category": "EBA",
        "priority": "high",
        "signal_type": "regulatory",
        "keywords_include": [],
        "keywords_exclude": [],
        "geo": "EU"
    },
    {
        "name": "European Commission Finance",
        "url": "https://ec.europa.eu/finance/rss_en.xml",
        "category": "regulatory",
        "sub_category": "DORA",
        "priority": "high",
        "signal_type": "regulatory",
        "keywords_include": ["dora", "digital operational resilience", "outsourcing"],
        "keywords_exclude": [],
        "geo": "EU"
    },
    {
        "name": "ESMA",
        "url": "https://www.esma.europa.eu/press-news/esma-news/rss",
        "category": "regulatory",
        "sub_category": "ESMA",
        "priority": "high",
        "signal_type": "regulatory",
        "keywords_include": [],
        "keywords_exclude": [],
        "geo": "EU"
    },

    # =========================
    # 🟠 PROCUREMENT / TPRM
    # =========================
    {
        "name": "Spend Matters",
        "url": "https://spendmatters.com/feed",
        "category": "procurement",
        "sub_category": "Trends",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": ["procurement", "vendor", "supplier", "sourcing"],
        "keywords_exclude": [],
        "geo": "global"
    },
    {
        "name": "Procurement Leaders",
        "url": "https://procurementleaders.com/feed/",
        "category": "procurement",
        "sub_category": "Intelligence",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": ["procurement", "outsourcing", "supplier"],
        "keywords_exclude": [],
        "geo": "global"
    },
    {
        "name": "Supply Chain 247",
        "url": "https://feeds.feedburner.com/sc247/rss",
        "category": "procurement",
        "sub_category": "Trends",
        "priority": "medium",
        "signal_type": "trend",
        "keywords_include": ["supply chain", "supplier", "vendor"],
        "keywords_exclude": [],
        "geo": "global"
    },

    # =========================
    # 🔵 TECH / AI
    # =========================
    {
        "name": "HackerNews",
        "url": "https://news.ycombinator.com/rss",
        "category": "tech",
        "sub_category": "Core Tech",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": [],
        "keywords_exclude": [],
        "geo": "global"
    },
    {
        "name": "Dev.to AI",
        "url": "https://dev.to/feed/tag/ai",
        "category": "tech",
        "sub_category": "AI Development",
        "priority": "medium",
        "signal_type": "trend",
        "keywords_include": ["ai", "machine learning", "llm"],
        "keywords_exclude": [],
        "geo": "global"
    },
    {
        "name": "Finextra AI",
        "url": "https://www.finextra.com/rss/channel.aspx?channel=ai",
        "category": "tech",
        "sub_category": "Fintech AI",
        "priority": "medium",
        "signal_type": "trend",
        "keywords_include": ["procurement", "vendor", "supplier", "contract", "outsourcing"],
        "keywords_exclude": ["crypto", "retail banking"],
        "geo": "global"
    },
    {
        "name": "Finextra Risk",
        "url": "https://www.finextra.com/rss/channel.aspx?channel=risk",
        "category": "tech",
        "sub_category": "Risk Intelligence",
        "priority": "medium",
        "signal_type": "trend",
        "keywords_include": ["third party", "outsourcing", "risk"],
        "keywords_exclude": [],
        "geo": "global"
    },

    # =========================
    # 🟢 MARKET SIGNALS
    # =========================
    {
        "name": "TechCrunch Fintech",
        "url": "https://techcrunch.com/tag/fintech/feed/",
        "category": "market",
        "sub_category": "Weak Signal",
        "priority": "low",
        "signal_type": "weak_signal",
        "keywords_include": ["platform", "vendor", "b2b", "saas"],
        "keywords_exclude": ["crypto"],
        "geo": "global"
    }
]

# ==============================================================================
# 🧠 GLOBAL FILTERING KEYWORDS
# ==============================================================================

GLOBAL_KEYWORDS_INCLUDE = [
    "procurement", "outsourcing", "third party", "vendor", "supplier",
    "tprm", "dora", "eba", "ict risk", "ai", "llm", "claude", "gpt",
    "gemini", "agentic", "transformer", "neural", "model"
]

GLOBAL_KEYWORDS_EXCLUDE = [
    "crypto", "retail banking", "consumer loans"
]

# Mappatura delle Stanze UI verso le categorie dei dizionari
CATEGORY_MAPPING = {
    "procurement": ["procurement", "regulatory"],
    "legal": ["regulatory"],
    "tech": ["tech", "market"]
}