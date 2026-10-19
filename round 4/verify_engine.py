"""Check that an extracted engine folder is byte-identical to the submitted zip.

Usage:  python verify_engine.py <folder-containing-brand-ai-readiness-audit> [--restore]
With --restore, any changed, missing or extra file is put back exactly as the zip has it.
Ignores __pycache__, the .claude skill link and audit-report.* output files.
"""
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, "brand-ai-readiness-audit.zip")
IGNORED_DIRS = {"__pycache__", ".claude"}


def check(base, restore):
    z = zipfile.ZipFile(ZIP)
    members = [n for n in z.namelist() if not n.endswith("/")]
    known = {os.path.normpath(n) for n in members}
    changed = [n for n in members
               if not os.path.exists(os.path.join(base, n))
               or open(os.path.join(base, n), "rb").read() != z.read(n)]
    extra = []
    for dp, dn, fn in os.walk(os.path.join(base, "brand-ai-readiness-audit")):
        dn[:] = [d for d in dn if d not in IGNORED_DIRS]
        for f in fn:
            if f.startswith("audit-report."):
                continue
            rel = os.path.normpath(os.path.relpath(os.path.join(dp, f), base))
            if rel not in known:
                extra.append(rel)
    if not changed and not extra:
        print("ENGINE OK: identical to the submitted zip")
        return 0
    for n in changed:
        print("CHANGED:", n)
    for n in extra:
        print("EXTRA:  ", n)
    if not restore:
        return 1
    for n in changed:
        z.extract(n, base)
    for n in extra:
        p = os.path.join(base, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    print("RESTORED from the submitted zip")
    return check(base, False)


if __name__ == "__main__":
    sys.exit(check(os.path.abspath(sys.argv[1]), "--restore" in sys.argv))
