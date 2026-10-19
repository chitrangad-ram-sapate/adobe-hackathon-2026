"""Pre-screen candidate demo sites with the frozen engine (read-only, one run each)."""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "brand-ai-readiness-audit", "skills", "audit-orchestrator", "scripts", "run_audit.py")
OUT = os.path.join(HERE, "prescreen")
SITES = sys.argv[1:] or [
    "https://www.typeform.com", "https://www.calendly.com", "https://www.airtable.com",
    "https://www.duolingo.com", "https://www.glossier.com", "https://www.bombas.com",
    "https://www.loom.com", "https://www.grammarly.com",
]


def run(url):
    name = url.split("//")[1].replace("www.", "").strip("/").replace("/", "_")
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    t = time.time()
    p = subprocess.run([sys.executable, ENGINE, url, "--out", os.path.join(d, "report.json"),
                        "--markdown", os.path.join(d, "report.md"), "--cache", os.path.join(d, "cache"),
                        "--keep-cache"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t
    try:
        r = json.load(open(os.path.join(d, "report.json"), encoding="utf-8"))
    except Exception as e:
        return f"{url}: FAILED rc={p.returncode} {dt:.0f}s {p.stderr[-300:]}"
    fs = r["findings"]
    sev = {}
    for f in fs:
        sev[f["severity"]] = sev.get(f["severity"], 0) + 1
    prof = r.get("audit", {}).get("site_profile") or r.get("audit", {}).get("profile") or {}
    top = "; ".join(f"{f['check_id']}[{f['severity']}] {f['title'][:70]}" for f in fs[:8])
    return f"{url}: {dt:.0f}s {len(fs)} findings {sev} type={prof.get('site_type', '?') if isinstance(prof, dict) else prof}\n    {top}"


with ThreadPoolExecutor(4) as ex:
    for line in ex.map(run, SITES):
        print(line, flush=True)
