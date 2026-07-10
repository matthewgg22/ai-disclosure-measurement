"""One shared EDGAR client: throttled, cached full-text-search counts, plus the 10-K filer
denominator. Every extractor talks to this interface, so tests can pass a fake client and
run with no network.
"""
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_CACHE = os.path.join(_ROOT, "data", "_cache_screen_engine.json")
_DENOM_CSV = os.path.join(_ROOT, "data", "aggregates", "ai_prevalence.csv")
_FTS_URL = "https://efts.sec.gov/LATEST/search-index?"


class EdgarClient:
    """Live EDGAR full-text-search client. fts_count and denominator are the only surface the
    extractors depend on."""

    def __init__(self, contact, cache_path=_DEFAULT_CACHE, throttle=0.5, timeout=45):
        self.ua = {"User-Agent": f"AI Washing Research (HKS PAE) {contact}"}
        self.cache_path = cache_path
        self.throttle = throttle
        self.timeout = timeout
        self._last = 0.0
        self._cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
        self._denom = None

    def _sleep(self):
        dt = time.time() - self._last
        if dt < self.throttle:
            time.sleep(self.throttle - dt)
        self._last = time.time()

    def _save(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        json.dump(self._cache, open(self.cache_path, "w"))

    def fts_count(self, query, year, forms="10-K"):
        """Number of `forms` filings matching a full-text query in a calendar year. Cached.
        Space-separated quoted phrases are AND-ed by EDGAR FTS (gives co-occurrence counts)."""
        key = f"{forms}|{year}|{query}"
        if key in self._cache:
            return self._cache[key]
        self._sleep()
        params = {"q": query, "forms": forms,
                  "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
        url = _FTS_URL + urllib.parse.urlencode(params)
        for i in range(8):
            try:
                d = json.load(urllib.request.urlopen(
                    urllib.request.Request(url, headers=self.ua), timeout=self.timeout))
                n = d.get("hits", {}).get("total", {}).get("value", 0)
                self._cache[key] = n
                self._save()
                return n
            except Exception:
                time.sleep(2.0 * (i + 1))
        return None

    def xbrl_frames_instant(self, concept, year, unit="shares"):
        """A balance-sheet (instantaneous) XBRL concept as a {cik: value} map for the Q4
        instant frame CY{year}Q4I. `concept` may carry a taxonomy prefix ("dei:Foo");
        default taxonomy is us-gaap. Returns the Q4-end cross-section (not literally every
        filer; only those reporting as of that quarter-end). Cached to disk (issuer-level;
        lives under the git-ignored data/ tree)."""
        tax, name = ("dei", concept.split(":", 1)[1]) if concept.startswith("dei:") \
            else ("us-gaap", concept.split(":", 1)[-1])
        cache_key = f"frames|{tax}|{name}|{unit}|CY{year}Q4I"
        if cache_key in self._cache:
            return {int(k): v for k, v in self._cache[cache_key].items()}
        self._sleep()
        url = f"https://data.sec.gov/api/xbrl/frames/{tax}/{name}/{unit}/CY{year}Q4I.json"
        for i in range(6):
            try:
                d = json.load(urllib.request.urlopen(
                    urllib.request.Request(url, headers=self.ua), timeout=self.timeout))
                out = {int(x["cik"]): x["val"] for x in d.get("data", [])}
                self._cache[cache_key] = out
                self._save()
                return out
            except urllib.error.HTTPError as e:
                if e.code == 404:  # no such frame that quarter
                    self._cache[cache_key] = {}
                    self._save()
                    return {}
                time.sleep(2.0 * (i + 1))
            except Exception:
                time.sleep(2.0 * (i + 1))
        return {}

    def denominator(self, year):
        """Distinct 10-K filers in a year, from the committed aggregate (ai_prevalence.csv)."""
        if self._denom is None:
            self._denom = {}
            if os.path.exists(_DENOM_CSV):
                for r in csv.DictReader(open(_DENOM_CSV)):
                    self._denom[int(r["year"])] = int(r["n_10k_filers"])
        return self._denom.get(int(year))
