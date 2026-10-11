# 🐄🐑🐖 DRM arm B — "the table needs all its animals" (Nova, 2026-10-11 morning).
# Closes the semantic-audit table so it PARTITIONS: for each model, every exact-lure-absent unit
# that has an Old/New judgment lands in exactly one row — consensus cat 1..5, or coders disagree —
# with endorsed/total in every cell and a SUM CHECK against the primary denominators.
# Also: coder confusion matrix + Cohen's kappa (unweighted + linear-weighted), and the
# positive-control misses listed with their evidence so the heading ambiguity can be SEEN.
# 🧪 POSITIVE CONTROL FIRST: denominators must reproduce hermes 62 · llama 49 · qwen 64.
import json, re, sys, collections

run, audit = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(run, encoding="utf-8") if l.startswith("{")]
B = [r for r in rows if r.get("arm") == "B"]
LURES = ["anger","black","bread","chair","cold","doctor","foot","fruit","girl","high","king","man"]
EXPECT = {"hermes3:8b": 62, "llama3.1:8b": 49, "qwen2.5:14b": 64}

def judgments(raw):        # same parser as drm_armB_fences.py (sha e3823fdc) — one parser, not two
    d = {}
    for line in raw.splitlines():
        m = re.match(r"\s*[\*\-\d\.\)]*\s*([A-Za-z]+)\s*[:\-–]\s*\**\s*(Old|New)", line, re.I)
        if m: d.setdefault(m.group(1).lower(), m.group(2).lower() == "old")
    return d

units = [json.loads(l) for l in open(audit, encoding="utf-8")]
codes = {(u["model"], u["form"], u["seed"], u["lure"]): u for u in units}
CODERS = sorted({c for u in units for c in u["codes"]})

def consensus(u):
    cs = [u["codes"][c]["category"] for c in CODERS]
    if None in cs: return "missing"     # 🩹 a failed/unusable code is NOT a disagreement (v2 caught this)
    return cs[0] if len(set(cs)) == 1 else None

# ── 1. the partition ────────────────────────────────────────────────────────────────
ok_all = True
print("=" * 100)
print("PARTITION of exact-lure-absent units (with an Old/New judgment), endorsed Old / total")
hdr = ["cat1", "cat2", "cat3", "cat4", "cat5", "disagree", "missing"]
print(f"{'model':<14}" + "".join(f"{h:>11}" for h in hdr) + f"{'SUM':>9}{'expect':>8}{'consensus coverage':>21}")
for model in sorted({r['model'] for r in B}):
    cell = collections.defaultdict(lambda: [0, 0])
    for r in B:
        if r["model"] != model: continue
        studied = LURES[:6] if r["form"] == "X" else LURES[6:]
        j = judgments(r["recog_raw"])
        for l in studied:
            if l in r.get("note_lures_studied", []) or j.get(l) is None: continue
            u = codes[(r["model"], r["form"], r["seed"], l)]
            c = consensus(u)
            k = "missing" if c == "missing" else (f"cat{c}" if c else "disagree")
            cell[k][0] += j[l]; cell[k][1] += 1
    total = sum(v[1] for v in cell.values())
    cons = total - cell["disagree"][1] - cell["missing"][1]
    ok = total == EXPECT[model]; ok_all &= ok
    print(f"{model:<14}" + "".join(f"{cell[h][0]:>5}/{cell[h][1]:<5}" for h in hdr)
          + f"{total:>9}{EXPECT[model]:>8}{'  ✅' if ok else '  ❌'}   {cons}/{total} = {cons/total:.2f}")
print("✅ partition closes on every model" if ok_all else "❌ PARTITION DOES NOT CLOSE — parser or join is wrong; nothing below counts")

# ── 2. coder reliability ─────────────────────────────────────────────────────────────
a, b = CODERS
pairs = [(u["codes"][a]["category"], u["codes"][b]["category"]) for u in units
         if u["codes"][a]["category"] and u["codes"][b]["category"]]
K = [1, 2, 3, 4, 5]
M = {(i, j): 0 for i in K for j in K}
for x, y in pairs: M[(x, y)] += 1
n = len(pairs)
print("\n" + "=" * 100)
print(f"CONFUSION MATRIX (rows = {a}, cols = {b}), all {n} units")
print("        " + "".join(f"{j:>6}" for j in K) + "   row")
for i in K:
    print(f"   {i:<4} " + "".join(f"{M[(i, j)]:>6}" for j in K) + f"{sum(M[(i, j)] for j in K):>6}")
print("   col  " + "".join(f"{sum(M[(i, j)] for i in K):>6}" for j in K))

def kappa(weighted):
    w = (lambda i, j: 1 - abs(i - j) / 4) if weighted else (lambda i, j: 1.0 if i == j else 0.0)
    po = sum(w(i, j) * M[(i, j)] for i in K for j in K) / n
    ra = {i: sum(M[(i, j)] for j in K) / n for i in K}
    cb = {j: sum(M[(i, j)] for i in K) / n for j in K}
    pe = sum(w(i, j) * ra[i] * cb[j] for i in K for j in K)
    return po, pe, (po - pe) / (1 - pe)
po, pe, k = kappa(False); print(f"\nraw agreement {po:.3f} · chance {pe:.3f} · Cohen's kappa (unweighted) {k:.3f}")
po, pe, k = kappa(True);  print(f"linear-weighted kappa {k:.3f}  (⚠️ treats 1..5 as ordered; cat 5 'insufficient' is not really 'further' than 4 — reported, not leaned on)")

# ── 3. the positive control, opened up ──────────────────────────────────────────────
print("\n" + "=" * 100)
print("POSITIVE CONTROL: units the SCRIPT knows contain the exact lure, where a coder said ≠ 1")
for u in units:
    if not u["exact_in_note_script"]: continue
    bad = {c: u["codes"][c] for c in CODERS if u["codes"][c]["category"] != 1}
    for c, v in bad.items():
        print(f"  {u['model']:<12} {u['form']}{u['seed']:<3} lure={u['lure']:<7} {c.split('/')[1]:<18} said {v['category']}  ev: {v['evidence'][:70]}")
print("DONE (partition + reliability complete)")
