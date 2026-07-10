"""PCAOB Form AP client: who audited which issuer, in which year.

Form AP (the auditor's report filing) names the audit firm and the issuer (with CIK) for every
issuer audit since ~2016. PCAOB publishes the whole dataset as one bulk zip, refreshed daily.
This client downloads and caches that zip (issuer-level data, so the cache lives under the
git-ignored data/ tree) and yields per-audit records. Extractors aggregate it; no issuer-level
row is ever published.
"""
import csv
import io
import os
import urllib.request
import zipfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CACHE_ZIP = os.path.join(_ROOT, "data", "_cache_pcaob_firmfilings.zip")
_URL = "https://assets.pcaobus.org/firm-filings/FirmFilings.zip"

# Big-4 = the four global network firms; everyone else is "non-Big-4" (the fraud-relevant tail,
# including the national mid-tier). Substring match on the Form AP firm name.
BIG4_MARKERS = ("deloitte", "pricewaterhousecoopers", "ernst & young", "kpmg")


def is_big4(firm_name):
    f = (firm_name or "").lower()
    return any(m in f for m in BIG4_MARKERS)


def firm_key(firm_name):
    """A stable identity for churn comparison. Big-4 network variants (e.g. 'Deloitte & Touche
    LLP' vs 'Deloitte LLP') collapse to one marker so they do not read as an auditor change;
    every other firm keys off its own normalized name."""
    f = (firm_name or "").strip().lower()
    for m in BIG4_MARKERS:
        if m in f:
            return m
    return f


class PcaobClient:
    def __init__(self, contact, cache_zip=_CACHE_ZIP, timeout=180):
        self.ua = {"User-Agent": f"AI Washing Research (HKS PAE) {contact}"}
        self.cache_zip = cache_zip
        self.timeout = timeout
        self.failures = []
        self._parsed = {}  # operating_only -> materialized records, so multiple extractors
        #                    (auditor_market, auditor_churn) share one parse of the 93MB CSV

    def _ensure(self):
        if os.path.exists(self.cache_zip):
            return True
        os.makedirs(os.path.dirname(self.cache_zip), exist_ok=True)
        try:
            req = urllib.request.Request(_URL, headers=self.ua)
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = r.read()
            tmp = self.cache_zip + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.replace(tmp, self.cache_zip)
            return True
        except Exception:
            self.failures.append(("pcaob", "FirmFilings.zip download"))
            return False

    # Form AP's three report types. Operating issuers carry the long label whose own text
    # contains "Investment Company" ("...other than ... or Investment Company"), so the
    # population must be selected positively, never by substring-excluding "investment company".
    OPERATING_ISSUER = "issuer, other than employee benefit plan or investment company"

    def audits(self, operating_only=True):
        """Yield (fiscal_year:int, firm_name:str, issuer_cik:int, report_type:str) for the
        latest Form AP filing of each audit. `operating_only` keeps only operating-company
        issuers (dropping Investment Company funds and Employee Benefit Plans), which are the
        fraud-relevant population. The parse is materialized and cached, so a second extractor
        over the same population does not re-read the file."""
        key = bool(operating_only)
        if key in self._parsed:
            yield from self._parsed[key]
            return
        if not self._ensure():
            return
        with zipfile.ZipFile(self.cache_zip) as z:
            name = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
            if not name:
                self.failures.append(("pcaob", "no CSV in FirmFilings.zip"))
                return
            text = z.read(name).decode("utf-8", "replace")
        recs = []
        for r in csv.DictReader(io.StringIO(text)):
            if r.get("Latest Form AP Filing") != "1":
                continue
            rtype = (r.get("Audit Report Type") or "").strip()
            if operating_only and rtype.lower() != self.OPERATING_ISSUER:
                continue
            cik = (r.get("Issuer CIK") or "").strip()
            fpe = (r.get("Fiscal Period End Date") or "").strip()  # "M/D/YYYY 12:00:00 AM"
            firm = (r.get("Firm Name") or "").strip()
            if not cik or not fpe:
                continue
            parts = fpe.split(" ")[0].split("/")
            if len(parts) != 3 or not parts[2].isdigit():
                continue
            try:
                recs.append((int(parts[2]), firm, int(cik), rtype))
            except ValueError:
                continue
        self._parsed[key] = recs
        yield from recs
