# ==============================================================================
# 🌐 CONFIGURAZIONE UNIFICATA FONTI INTELLIGENTI
# ==============================================================================

SOURCES = [
    # =========================
    # 🔴 LEGAL / REGULATORY
    # =========================
    {
        "name": "EBA News",
        "url": "https://www.eba.europa.eu/news-press/news/rss.xml",
        "category": "legal",
        "sub_category": "EBA",
        "priority": "high",
        "signal_type": "regulatory",
        "keywords_include": ["guidelines", "outsourcing", "ict", "risk", "dora", "third party", "critical supplier"],
        "keywords_exclude": [],
        "geo": "EU"
    },
    {
        "name": "European Commission Finance",
        "url": "https://ec.europa.eu/finance/rss_en.xml",
        "category": "legal",
        "sub_category": "DORA",
        "priority": "high",
        "signal_type": "regulatory",
        # M9: Allargate per evitare 0 risultati costanti
        "keywords_include": ["dora", "digital operational resilience", "outsourcing", "third party", "finance", "regulation", "risk"],
        "keywords_exclude": [],
        "geo": "EU"
    },
    {
        "name": "ESMA",
        "url": "https://www.esma.europa.eu/press-news/esma-news/rss",
        "category": "legal",
        "sub_category": "ESMA",
        "priority": "high",
        "signal_type": "regulatory",
        # M9: Allargate per evitare 0 risultati costanti
        "keywords_include": ["outsourcing", "risk", "third party", "supplier", "governance", "regulation", "market"],
        "keywords_exclude": [],
        "geo": "EU"
    },

    # =========================
    # 🟠 PROCUREMENT
    # =========================
    {
        "name": "Spend Matters",
        "url": "https://spendmatters.com/feed",
        "category": "procurement",
        "sub_category": "Strategy & Methods",
        "priority": "high",
        "signal_type": "trend",
        # M9: Rese più ampie per intercettare articoli reali
        "keywords_include": [
            "procurement", "sourcing", "supply chain", "vendor", "strategy"
        ],
        "keywords_exclude": [],
        "geo": "global"
    },
    {
        "name": "Procurement Leaders",
        "url": "https://procurementleaders.com/feed/",
        "category": "procurement",
        "sub_category": "Governance & Operating Model",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": [
            "procurement strategy", "operating model",
            "governance", "procurement function",
            "cpo", "organizational design"
        ],
        "keywords_exclude": [],
        "geo": "global"
    },
    
    # C3 FIX: Unificata la doppia entry di Supply Chain 247
    {
        "name": "Supply Chain 247",
        "url": "https://feeds.feedburner.com/sc247/rss",
        "category": "procurement",
        "sub_category": "Execution & Supply",
        "priority": "medium",
        "signal_type": "trend",
        "keywords_include": [
            "supply chain", "supplier", "vendor",
            "resilience", "procurement execution", "supply disruption"
        ],
        "keywords_exclude": [],
        "geo": "global"
    },

    # 🔹 PROCUREMENT TECHNOLOGY
    {
        "name": "Finextra Payments / Tech",
        "url": "https://www.finextra.com/rss/channel.aspx?channel=technology",
        "category": "procurement",
        "sub_category": "Procurement Technology",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": [
            "procurement platform", "vendor platform",
            "third party", "outsourcing", "saas procurement",
            "contract management", "vendor risk", "saas",  "contract lifecycle management"
        ],
        "keywords_exclude": ["crypto"],
        "geo": "global"
    },

    # 🔹 AI APPLICATA AL PROCUREMENT
    {
        "name": "Finextra AI",
        "url": "https://www.finextra.com/rss/channel.aspx?channel=ai",
        "category": "procurement",
        "sub_category": "AI in Procurement",
        "priority": "high",
        "signal_type": "trend",
        "keywords_include": [
            "ai procurement", "automation procurement",
            "contract ai", "supplier ai",
            "llm procurement", "vendor automation", "llm",  "agent"
        ],
        "keywords_exclude": ["crypto"],
        "geo": "global"
    },

    # =========================
    # 🔵 TECH
    # =========================
    {
        "name": "HackerNews",
        "url": "https://news.ycombinator.com/rss",
        "category": "tech",
        "sub_category": "Core Tech",
        "priority": "medium",
        "signal_type": "weak_signal",
        "keywords_include": ["ai", "llm", "automation", "platform", "vendor", "enterprise software"],
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
        "keywords_include": ["ai", "llm", "agent", "automation"],
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
        "keywords_include": [
            "b2b", "saas", "platform",
            "vendor", "enterprise software", "procurement technology", "procurement startup"
        ],
        "keywords_exclude": ["crypto"],
        "geo": "global"
    }
]

# ==============================================================================
# 🧠 GLOBAL FILTERING KEYWORDS
# ==============================================================================

GLOBAL_KEYWORDS_INCLUDE = [
    "procurement", "sourcing", "supplier", "vendor",
    "outsourcing", "third party", "tprm",
    "dora", "eba", "ict risk", "third party risk",
    "operating model", "procurement strategy",
    "governance", "transformation",
    "ai", "llm", "automation", "agentic",
    "contract management", "supplier platform", "vendor platform", "procurement platform"
]

GLOBAL_KEYWORDS_EXCLUDE = [
    "crypto", "retail banking", "consumer loans", "personal finance" 
]

# ==============================================================================
# 🧭 CATEGORY MAPPING (FIX C10: IL PROCUREMENT ORA VEDE ANCHE IL LEGAL)
# ==============================================================================

CATEGORY_MAPPING = {
    "procurement": ["procurement", "legal"],
    "legal": ["legal"],
    "tech": ["tech", "market"]
}