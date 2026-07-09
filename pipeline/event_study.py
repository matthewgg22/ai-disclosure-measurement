#!/usr/bin/env python3
"""
CAUSAL EVENT STUDY — does AI-washing enforcement restore a separating signal?

Cross-sectional event study with EVENT FIXED EFFECTS. For each AI-washing event e and
each AI-labeled Russell-3000 firm i (excluding the defendant), compute CAR_{i,e}
(FF5+momentum abnormal return), then:

  CAR_{i,e} = α_e + β·Substance_i + δ·ln(MktCap)_i + sectorFE + ε

β>0  ⇒  the market punishes low-substance "washer" AI firms more than substantive ones
around AI-washing news  ⇒  separation restored (the policy lever).  Event FE absorb the
common per-event shock; β is identified off the cross-sectional substance gradient.

Placebos: (a) NON-AI firms should show no gradient; (b) pre-event window [-5,-2] should
show no gradient.

Data: _cache_daily/ (adjClose) + FF daily factors + russell3000_ai_soph.csv + _cache_fundamentals.json
Usage: python3 event_study.py
"""
import csv, io, json, os, zipfile, urllib.request
import numpy as np
from scipy import stats
from collections import defaultdict

DATA   = os.path.join(os.path.dirname(__file__), "..", "data")
DCACHE = os.path.join(DATA, "_cache_daily")
FDCACHE= os.path.join(DATA, "_cache_factors_daily.json")
BENCH  = [2015,2018,2021,2022,2023,2024,2025,2026]

# (announcement date, label, type, defendant-ticker-in-universe-to-exclude)
EVENTS = [
    ("2024-02-21", "Innodata",            "private",  "INOD"),
    ("2024-03-18", "Delphia/GlobalPred",  "SEC",      None),
    ("2024-06-11", "Joonko",              "SEC+DOJ",  None),
    ("2024-12-04", "Evolv+FTC",           "private+FTC","EVLV"),
    ("2025-01-14", "Presto",              "SEC-public",None),
    ("2025-04-09", "Nate",                "SEC+DOJ",  None),
    ("2025-04-21", "BigBear.ai",          "private",  "BBAI"),
]
EST=(-250,-31); WIN=(0,1); PRE=(-5,-2)

def label_year(y): return max([b for b in BENCH if b<=y], default=BENCH[0])

# ---------- FF daily factors ----------
def _parse_daily(txt):
    out={}
    for line in txt.splitlines():
        t=[x.strip() for x in line.split(",")]
        if t and len(t[0])==8 and t[0].isdigit():
            try: out[t[0]]=[float(x) for x in t[1:] if x not in ("",)]
            except ValueError: pass
    return out
def load_factors_daily():
    if os.path.exists(FDCACHE): return json.load(open(FDCACHE))
    def grab(u):
        raw=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 research"}),timeout=60).read()
        z=zipfile.ZipFile(io.BytesIO(raw)); return z.read(z.namelist()[0]).decode("latin-1")
    ff5=_parse_daily(grab("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"))
    mom=_parse_daily(grab("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"))
    fac={}
    for d,v in ff5.items():
        if d in mom and len(v)==6 and min(v+[mom[d][0]])>-99:
            mktrf,smb,hml,rmw,cma,rf=v
            fac[f"{d[:4]}-{d[4:6]}-{d[6:]}"]={k:x/100. for k,x in
                zip(["mktrf","smb","hml","rmw","cma","rf","mom"],[mktrf,smb,hml,rmw,cma,rf,mom[d][0]])}
    json.dump(fac,open(FDCACHE,"w")); return fac

def daily_ret(ticker, cal):
    safe=ticker.replace("/","_").replace(".","-")
    cp=os.path.join(DCACHE,f"{safe}.json")
    if not os.path.exists(cp): return None
    try: px=json.load(open(cp))
    except Exception: return None
    if not px or len(px)<150: return None
    ds=[d for d in cal if d in px]
    r={}
    for i in range(1,len(ds)):
        p0,p1=px[ds[i-1]],px[ds[i]]
        if p0: r[ds[i]]=p1/p0-1
    return r

def car(rets, fac, cal, anchor_idx, est, win):
    """FF5+mom abnormal return: estimate loadings on est window, CAR over win."""
    F=["mktrf","smb","hml","rmw","cma","mom"]
    # estimation rows
    Xe,ye=[],[]
    for k in range(anchor_idx+est[0], anchor_idx+est[1]+1):
        if k<0 or k>=len(cal): continue
        d=cal[k]
        if d in rets and d in fac:
            Xe.append([1.]+[fac[d][f] for f in F]); ye.append(rets[d]-fac[d]["rf"])
    if len(ye)<100: return None
    Xe=np.array(Xe); ye=np.array(ye)
    try: b=np.linalg.lstsq(Xe,ye,rcond=None)[0]
    except Exception: return None
    # event window AR
    car=0.; n=0
    for k in range(anchor_idx+win[0], anchor_idx+win[1]+1):
        if k<0 or k>=len(cal): continue
        d=cal[k]
        if d in rets and d in fac:
            pred=b[0]+sum(b[j+1]*fac[d][f] for j,f in enumerate(F))
            car+=(rets[d]-fac[d]["rf"])-pred; n+=1
    return car if n>0 else None

def ols_cluster(X,y,groups):
    XtXi=np.linalg.inv(X.T@X); beta=XtXi@X.T@y; u=y-X@beta
    # cluster by event
    meat=np.zeros((X.shape[1],X.shape[1]))
    for g in set(groups):
        m=np.array(groups)==g; Xg=X[m]; ug=u[m]
        s=Xg.T@ug; meat+=np.outer(s,s)
    G=len(set(groups)); n,k=X.shape
    adj=(G/(G-1))*((n-1)/(n-k))
    V=XtXi@meat@XtXi*adj
    se=np.sqrt(np.diag(V)); t=beta/se
    p=2*(1-stats.t.cdf(np.abs(t),df=G-1))
    return beta,se,t,p

def build_panel(firms, fac, cal, ai_only=True, win=WIN):
    fund=json.load(open(os.path.join(DATA,"_cache_fundamentals.json")))
    rows=[]
    cal_idx={d:i for i,d in enumerate(cal)}
    for ev_date,lbl,typ,defend in EVENTS:
        ly=label_year(int(ev_date[:4]))
        # anchor = first trading day >= announcement
        anchor=next((i for i,d in enumerate(cal) if d>=ev_date), None)
        if anchor is None: continue
        for f in firms:
            tk=f["symbol"]
            if defend and tk==defend: continue
            is_ai=f.get(f"ai_{ly}")=="1"
            if ai_only and not is_ai: continue
            if (not ai_only) and is_ai: continue       # placebo = non-AI only
            rets=daily_ret(tk,cal)
            if not rets: continue
            c=car(rets,fac,cal,anchor,EST,win)
            if c is None: continue
            cik=str(int(f["cik"])); sh=None
            for y in ["2024","2025","2023"]:
                if fund.get(cik,{}).get(y,{}).get("shares"): sh=fund[cik][y]["shares"]; break
            # pre-event close for mktcap
            px=None
            safe=tk.replace("/","_").replace(".","-")
            try: px=json.load(open(os.path.join(DCACHE,f"{safe}.json"))).get(cal[anchor-2])
            except Exception: pass
            mc=(px*sh) if (px and sh) else None
            rows.append({"car":c,"soph":float(f.get("soph_score_sa") or 0),
                         "tier":f.get("soph_tier_sa",""),"lnmc":np.log(mc) if mc and mc>0 else None,
                         "sic1":(f.get("sic") or "x")[:1],"event":lbl})
    return rows

def regress(rows, label, drop_size_na=True, use_tier=False):
    R=[r for r in rows if (r["lnmc"] is not None or not drop_size_na)]
    if len(R)<50: print(f"  {label}: too few obs ({len(R)})"); return
    y=np.array([r["car"] for r in R])
    # winsorize CAR 1/99
    lo,hi=np.percentile(y,1),np.percentile(y,99); y=np.clip(y,lo,hi)
    soph=np.array([r["soph"] for r in R]); lnmc=np.array([r["lnmc"] or 0 for r in R])
    events=sorted({r["event"] for r in R}); secs=sorted({r["sic1"] for r in R})
    if use_tier:
        dose=np.array([1. if r["tier"]=="TECHNICAL" else 0. for r in R])  # TECH vs rest
        cols=[dose, lnmc]; names=["TECH","lnmc"]
    else:
        cols=[soph, lnmc]; names=["soph","lnmc"]
    for e in events[1:]:
        cols.append(np.array([1. if r["event"]==e else 0. for r in R])); names.append(f"ev:{e}")
    for s in secs[1:]:
        cols.append(np.array([1. if r["sic1"]==s else 0. for r in R])); names.append(f"sic:{s}")
    cols.append(np.ones(len(R))); names.append("const")
    X=np.column_stack(cols)
    beta,se,t,p=ols_cluster(X,y,[r["event"] for r in R])
    bs=beta[0]; ts=t[0]; ps=p[0]
    scale=(np.percentile(soph,75)-np.percentile(soph,25)) if not use_tier else 1.0
    print(f"  {label}: n={len(R)}, events={len(events)} | "
          f"β_{names[0]}={bs:+.4f} (t={ts:+.2f}, p={ps:.3f}) | "
          f"implied CAR move = {bs*scale*100:+.2f}%")
    return bs,ts,ps

def main():
    print("loading FF daily factors...")
    fac=load_factors_daily()
    cal=sorted(fac.keys())
    print(f"  factor trading days: {len(cal)} ({cal[0]}..{cal[-1]})")
    firms=list(csv.DictReader(open(os.path.join(DATA,"russell3000_ai_soph.csv"))))
    print(f"firms: {len(firms)}  events: {len(EVENTS)}")

    print("\n=== MAIN: AI-labeled firms, event window [0,+1] ===")
    rows=build_panel(firms,fac,cal,ai_only=True,win=WIN)
    print(f"  firm-event observations: {len(rows)}")
    regress(rows,"AI firms [0,+1]")
    regress(rows,"  same, TECHNICAL-vs-GENERIC tier dose",use_tier=True)

    print("\n=== ROBUSTNESS ===")
    rows5=build_panel(firms,fac,cal,ai_only=True,win=(0,5))
    regress(rows5,"AI firms [0,+5]")
    strong=[r for r in rows if r["event"] in ("Presto","Nate","Joonko/SEC+DOJ")]
    strong=[r for r in rows if r["event"] in ("Presto","Nate")]
    regress(strong,"AI firms, STRONG events only (Presto+Nate) [0,+1]")

    print("\n=== PLACEBO 1: NON-AI firms (gradient should be ~0) ===")
    nrows=build_panel(firms,fac,cal,ai_only=False,win=WIN)
    regress(nrows,"non-AI [0,+1]")

    print("\n=== PLACEBO 2: pre-event window [-5,-2] on AI firms (should be ~0) ===")
    prows=build_panel(firms,fac,cal,ai_only=True,win=PRE)
    regress(prows,"AI firms [-5,-2] pre")

    json.dump({"events":[e[0] for e in EVENTS]}, open(os.path.join(DATA,"event_study.json"),"w"))
    print("\n[done]")

if __name__=="__main__":
    main()
