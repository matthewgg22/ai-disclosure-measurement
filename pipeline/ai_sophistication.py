#!/usr/bin/env python3
# Usage: python3 pipeline/ai_sophistication.py [input.csv]   # default input russell3000_ai.csv; writes to ../data/
"""
AI vocabulary sophistication classifier.

The binary AI-mention flag (ai_2015..ai_2024) treats a company that wrote one sentence
about "AI-powered search" the same as a company describing fine-tuning LLMs on proprietary
training data. This script adds a third dimension: WHAT KIND of AI language is used.

Two-tier taxonomy:
  GENERIC  — terms any non-technical executive could copy from a headline. No operational
             specificity. Present in real AI companies AND in washers equally.
  TECHNICAL — terms that require actual familiarity with how AI systems are built and run.
             Hard to use correctly in context without genuine exposure. More discriminating.

Scores each company:
  generic_hits  : count of generic-tier matches in the 10-K text
  tech_hits     : count of technical-tier matches
  total_hits    : generic + tech
  soph_score    : tech / total  (0.0 = all generic, 1.0 = all technical)
  tier          : NONE / GENERIC / MIXED / TECHNICAL  (based on thresholds)

Downloads the most recent 10-K for each ticker via EDGAR.
Caches raw filing text to data/_cache_filings/{cik}.txt so re-runs are free.
Outputs data/russell3000_soph.csv  (symbol, cik, generic_hits, tech_hits, soph_score, tier)
"""
import csv, json, os, re, sys, time, urllib.request, urllib.error, html

DATA   = os.path.join(os.path.dirname(__file__), "..", "data")
FCACHE = os.path.join(DATA, "_cache_filings")
UA     = {"User-Agent": "AI Washing Research (HKS PAE) matthewgreergentis@gmail.com"}

# ── vocabulary taxonomy ──────────────────────────────────────────────────────

# Any exec can google these and paste them in with zero technical understanding.
GENERIC = [
    r'\bartificial intelligence\b',
    r'\bAI[-\s]powered\b',
    r'\bAI[-\s]driven\b',
    r'\bAI[-\s]enabled\b',
    r'\bAI[-\s]based\b',
    r'\bleverages?\s+AI\b',
    r'\butiliz(?:e|ing|es)\s+AI\b',
    r'\bmachine\s+learning\b',
    r'\bML\b(?!\s*\d)',          # ML but not "ML 2.0" etc
    r'\bautomation\b',
    r'\bautomate[sd]?\b',
    r'\balgorithm(?:s|ic)?\b',
    r'\bdata[-\s]driven\b',
    r'\bpredictive\s+analytics\b',
    r'\bpredictive\s+model(?:ing|s)?\b',
    r'\bintelligent\s+(?:system|platform|solution|tool)',
    r'\bcognitive\s+(?:computing|AI|technology)',
    r'\bsmart\s+(?:system|platform|solution|technology)',
    r'\banalytics?\b',           # very generic; counts but low weight
    r'\bdeep\s+learning\b',      # real term but widely cargo-culted
    r'\bnatural\s+language\s+processing\b',
    r'\bNLP\b',
    r'\bcomputer\s+vision\b',
]

# Require actual operational exposure to use correctly in context.
TECHNICAL = [
    # Architecture / model classes
    r'\blarge\s+language\s+model(?:s)?\b',
    r'\bLLM(?:s)?\b',
    r'\bgenerative\s+AI\b',
    r'\bGenAI\b',
    r'\bfoundation\s+model(?:s)?\b',
    r'\bbase\s+model(?:s)?\b',
    r'\btransformer(?:s)?\b',
    r'\battention\s+mechanism(?:s)?\b',
    r'\bneural\s+network(?:s)?\b',
    r'\bdiffusion\s+model(?:s)?\b',
    r'\bmultimodal\b',

    # Named models (can't fake knowing these)
    r'\bGPT[-\s]?\d',
    r'\bClaude\b',
    r'\bGemini\b',
    r'\bLlama\b',
    r'\bMistral\b',
    r'\bStable\s+Diffusion\b',
    r'\bDALL[-\s]?E\b',

    # Training / data pipeline
    r'\btraining\s+data\b',
    r'\blabeled?\s+data\b',
    r'\bground\s+truth\b',
    r'\bdata\s+labeling\b',
    r'\bfine[-\s]tun(?:e|ing|ed)\b',
    r'\binstruction\s+tun(?:e|ing|ed)\b',
    r'\bRLHF\b',
    r'\breinforcement\s+learning\s+from\s+human\s+feedback\b',
    r'\bpre[-\s]train(?:ing|ed)?\b',
    r'\bmodel\s+train(?:ing)?\b',

    # Inference / deployment
    r'\binference\b',
    r'\blatency\b(?=.{0,40}model)',   # latency near model context
    r'\btoken(?:s|ization|izer)?\b',
    r'\bcontext\s+window\b',
    r'\bprompt\s+engineer(?:ing)?\b',
    r'\bsystem\s+prompt\b',
    r'\bhallucination(?:s)?\b',       # companies fighting this know it
    r'\bRAG\b',
    r'\bretrieval[-\s]augmented\b',
    r'\bvector\s+(?:database|store|search|embedding)',
    r'\bembedding(?:s)?\b',
    r'\bsemanticmodel\b',

    # Compute / infrastructure
    r'\bGPU(?:s)?\b',
    r'\bTPU(?:s)?\b',
    r'\bNVIDIA\b',
    r'\bcuda\b',
    r'\bcompute\s+(?:cluster|resource|cost|infra)',
    r'\binference\s+cost(?:s)?\b',
    r'\bmodel\s+parameter(?:s)?\b',
    r'\bparameter(?:s)?\s+(?:billion|million|B|M)\b',   # "70B parameters"
    r'\bweights?\b(?=.{0,30}model)',  # "model weights"

    # Evaluation / safety
    r'\bbenchmark(?:s|ing)?\b(?=.{0,50}(?:model|AI|LLM))',
    r'\beval(?:uation)?\s+(?:set|metric|benchmark)',
    r'\bbias\s+(?:in|detection|mitigation)',
    r'\bAI\s+safety\b',
    r'\bresponsible\s+AI\b',
    r'\bexplainability\b',
    r'\bAI\s+governance\b',
]

# Compile all patterns
_G = [re.compile(p, re.IGNORECASE) for p in GENERIC]
_T = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in TECHNICAL]

# ── sector-aware context rules ───────────────────────────────────────────────
# Problem: pharma companies say "neural network" about drug-molecule modeling;
# finance firms say "model parameters" about actuarial reserves; mining says
# "training data" about geological formation models.  For each problematic
# 2-digit SIC group, define EXCLUDE patterns (invalidates a tech hit in a ±300-
# char window) and CONFIRM patterns (override exclusion — definitely AI product).

WINDOW = 300    # characters either side of a match to check for context

_SECTOR_RULES = {
    # Pharma / biotech / life sciences
    "28": {
        "exclude": re.compile(
            r'\b(?:clinical\s+trial|patient|drug\s+(?:candidate|compound|product)|'
            r'therapeutic|pharmacok|pharmacody|molecule|protein\s+(?:structure|fold)|'
            r'antibod|tumor|cancer|oncol|disease|FDA|IND\b|NDA\b|BLA\b|Phase\s+[123I]|'
            r'endpoint|biomarker|assay|preclinical|in\s+vitro|in\s+vivo|genomic|'
            r'sequenc|mutation|variant|compound\s+library|ADME|PK/PD|tox(?:ic|ology))\b',
            re.IGNORECASE),
        "confirm": re.compile(
            r'\b(?:SaaS|platform\s+(?:revenue|customer)|subscription|healthcare\s+provider|'
            r'electronic\s+health\s+record|EHR|claims\s+data|medical\s+imaging|'
            r'diagnostic\s+(?:tool|platform|product)|workflow\s+automation|'
            r'deploy(?:ed|ment|ing)|customer\s+(?:facing|experience|engagement)|'
            r'hospital\s+(?:system|network)|payer|revenue\s+cycle)\b',
            re.IGNORECASE),
    },
    # Finance / insurance / real estate (broad SIC 60-69)
    "60": {
        "exclude": re.compile(
            r'\b(?:actuarial|underwriting|reserve\s+(?:requirement|level)|'
            r'capital\s+(?:adequacy|requirement|ratio)|stress\s+test|'
            r'credit\s+risk|market\s+risk|operational\s+risk|'
            r'value.at.risk|VaR\b|Basel|Solvency\s+II|investment\s+portfolio|'
            r'fixed\s+income|equity\s+portfolio|mortgage-backed|'
            r'loan\s+(?:loss|reserve)|allowance\s+for\s+(?:credit|loan)|'
            r'internal\s+(?:ratings?|model)|DFAST|CCAR)\b',
            re.IGNORECASE),
        "confirm": re.compile(
            r'\b(?:fraud\s+detection|anti.money\s+launder|AML\b|'
            r'customer\s+(?:experience|segmentation|service|churn)|'
            r'chatbot|virtual\s+assistant|robo.advis|recommendation\s+engine|'
            r'document\s+(?:processing|classification|extraction)|'
            r'know\s+your\s+customer|KYC\b|transaction\s+monitoring|'
            r'natural\s+language|conversational\s+AI)\b',
            re.IGNORECASE),
    },
    # Mining / oil & gas / extraction (SIC 10-14, 29)
    "10": {
        "exclude": re.compile(
            r'\b(?:seismic|geological|reservoir|subsurface|formation|'
            r'exploration\s+(?:well|data|program)|well\s+log|borehole|'
            r'ore\s+(?:body|grade|reserve)|mineral\s+(?:resource|reserve)|'
            r'hydrocarbon|geophysic|stratigraph|litholog|'
            r'basin\s+model|petroleum\s+system)\b',
            re.IGNORECASE),
        "confirm": re.compile(
            r'\b(?:predictive\s+maintenance|safety\s+(?:monitoring|alert)|'
            r'supply\s+chain|customer|workforce\s+(?:planning|optim)|'
            r'energy\s+trading|demand\s+forecast|emissions\s+optim)\b',
            re.IGNORECASE),
    },
    # Utilities / electric / gas (SIC 49xx)
    "49": {
        "exclude": re.compile(
            r'\b(?:load\s+forecast|grid\s+(?:management|stability|operation)|'
            r'demand\s+response|transmission\s+(?:line|system|planning)|'
            r'distribution\s+(?:system|network|grid)|'
            r'renewable\s+energy\s+forecast|solar\s+irradiance|wind\s+(?:speed|forecast)|'
            r'outage\s+(?:prediction|management)|power\s+flow)\b',
            re.IGNORECASE),
        "confirm": re.compile(
            r'\b(?:customer\s+(?:experience|service|portal|engagement)|'
            r'chatbot|virtual\s+assistant|document\s+(?:process|extract)|'
            r'workforce|field\s+service|smart\s+meter\s+analytic|'
            r'billing\s+(?:optim|predict)|call\s+center)\b',
            re.IGNORECASE),
    },
}
# SIC prefixes that map to each rule key (rules keyed by first-2-digit group leader)
_SIC_MAP = {
    "28": "28",
    "29": "10",   # petroleum refining — same geological exclusions
    "60": "60", "61": "60", "62": "60", "63": "60",
    "64": "60", "65": "60", "66": "60", "67": "60", "68": "60", "69": "60",
    "10": "10", "11": "10", "12": "10", "13": "10", "14": "10",
    "49": "49",
}

def _sector_key(sic):
    """Return the rule-set key for a 2-digit SIC prefix, or None if no sector rule."""
    return _SIC_MAP.get((sic or "")[:2])

def _tech_hits_sector(text, sic):
    """
    Count valid technical hits, filtering out context-invalidated matches.
    For each technical pattern match: extract ±WINDOW chars, apply sector rules.
    A hit is VALID if:
      - no sector rule applies, OR
      - no exclusion pattern fires in the window, OR
      - a confirmation pattern fires (overrides the exclusion).
    """
    rule_key = _sector_key(sic)
    rules = _SECTOR_RULES.get(rule_key) if rule_key else None
    valid = 0
    for pat in _T:
        for m in pat.finditer(text):
            if rules is None:
                valid += 1          # no sector rule: always count
                break               # count pattern once even if it matches many times
            window = text[max(0, m.start() - WINDOW): m.end() + WINDOW]
            excluded  = bool(rules["exclude"].search(window))
            confirmed = bool(rules["confirm"].search(window))
            if not excluded or confirmed:
                valid += 1
                break               # count this pattern once
    return valid

def score_text(text):
    """Original (sector-unaware) scorer — used for backward compat / quick runs."""
    g = sum(1 for p in _G if p.search(text))
    t = sum(1 for p in _T if p.search(text))
    total = g + t
    soph = t / total if total else 0.0
    if total == 0:   tier = "NONE"
    elif t == 0:     tier = "GENERIC"
    elif soph < 0.3: tier = "GENERIC-LEANING"
    elif soph < 0.6: tier = "MIXED"
    else:            tier = "TECHNICAL"
    return g, t, total, round(soph, 3), tier


# ── EDGAR fetching ────────────────────────────────────────────────────────────

def raw_get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    except Exception:
        return None

def strip_html(txt):
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = html.unescape(txt)
    return re.sub(r'\s+', ' ', txt)

def get_10k_text(cik10):
    cik_int = str(int(cik10))
    cp = os.path.join(FCACHE, f"{cik10}.txt")
    if os.path.exists(cp):
        return open(cp).read()
    # latest annual filing
    sub = raw_get(f"https://data.sec.gov/submissions/CIK{cik10}.json")
    if not sub:
        return None
    sub = json.loads(sub)
    filings = sub.get("filings", {}).get("recent", {})
    forms  = filings.get("form", [])
    accs   = filings.get("accessionNumber", [])
    docs   = filings.get("primaryDocument", [])
    target = next(((accs[i], docs[i]) for i, f in enumerate(forms)
                   if f in ("10-K", "10-K/A")), None)
    if not target:
        return None
    acc, doc = target
    acc_path = acc.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_path}/{doc}"
    raw = raw_get(url)
    if not raw:
        return None
    text = strip_html(raw)[:500_000]     # 500k chars is plenty for vocab scoring
    open(cp, "w").write(text)
    return text


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(FCACHE, exist_ok=True)
    inp = sys.argv[1] if len(sys.argv) > 1 else "russell3000_ai.csv"
    firms = list(csv.DictReader(open(os.path.join(DATA, inp))))
    # only process AI-mentioners (saves ~half the calls; non-mentioners score NONE by definition)
    ai_firms = [f for f in firms if any(f.get(f"ai_{y}") == "1" for y in [2015,2018,2021,2024,2025,2026])]
    print(f"universe: {inp}  total={len(firms)}  AI-mentioners to score={len(ai_firms)}")

    results = {}
    for i, f in enumerate(ai_firms):
        cik  = str(f["cik"]).zfill(10)
        sic  = f.get("sic", "")
        text = get_10k_text(cik)
        if not text:
            results[f["symbol"]] = (0, 0, 0, 0, 0.0, 0.0, "NO-FILING", "NO-FILING")
            if (i+1) % 100 == 0: print(f"  ...{i+1}/{len(ai_firms)} scored", flush=True)
            continue
        g, t, tot, soph, tier       = score_text(text)
        t_sa                         = _tech_hits_sector(text, sic)
        tot_sa                       = g + t_sa
        soph_sa                      = t_sa / tot_sa if tot_sa else 0.0
        if tot_sa == 0:    tier_sa = "NONE"
        elif t_sa == 0:    tier_sa = "GENERIC"
        elif soph_sa < 0.3: tier_sa = "GENERIC-LEANING"
        elif soph_sa < 0.6: tier_sa = "MIXED"
        else:               tier_sa = "TECHNICAL"
        results[f["symbol"]] = (g, t, tot, t_sa, round(soph,3), round(soph_sa,3), tier, tier_sa)
        if (i+1) % 100 == 0:
            print(f"  ...{i+1}/{len(ai_firms)} scored  "
                  f"(last: {f['symbol']} sic={sic} t={t}→{t_sa} "
                  f"tier={tier}→{tier_sa})", flush=True)
        time.sleep(0.07)

    # write output — all firms (non-mentioners get NONE)
    out_path = os.path.join(DATA, inp.replace(".csv", "_soph.csv"))
    extra = ["generic_hits","tech_hits","total_hits","tech_hits_sa",
             "soph_score","soph_score_sa","soph_tier","soph_tier_sa"]
    cols = list(firms[0].keys()) + extra
    with open(out_path, "w") as f_out:
        f_out.write(",".join(cols) + "\n")
        for f in firms:
            row = results.get(f["symbol"], (0, 0, 0, 0, 0.0, 0.0, "NONE", "NONE"))
            f_out.write(",".join([str(f.get(c,"")) for c in firms[0].keys()]
                                 + [str(x) for x in row]) + "\n")
    print(f"\n[saved] {out_path}")

    from collections import Counter
    print("\nOriginal tier distribution:")
    tiers = [v[6] for v in results.values()]
    for tier, n in sorted(Counter(tiers).items(), key=lambda x: -x[1]):
        print(f"  {tier:<22} {n:>4} ({100*n/len(tiers):.0f}%)")
    print("\nSector-aware tier distribution:")
    tiers_sa = [v[7] for v in results.values()]
    for tier, n in sorted(Counter(tiers_sa).items(), key=lambda x: -x[1]):
        print(f"  {tier:<22} {n:>4} ({100*n/len(tiers_sa):.0f}%)")
    # show firms that changed tier
    changed = [(sym, v[6], v[7]) for sym, v in results.items() if v[6] != v[7]]
    print(f"\nFirms that changed tier after sector filtering: {len(changed)}")
    for sym, old, new in sorted(changed, key=lambda x: x[1]):
        print(f"  {sym:<8}  {old} → {new}")

if __name__ == "__main__":
    main()
