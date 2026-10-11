# 🧱 DRM arm B — the fences Nova and Kairo asked for before the RESULTS block goes public.
#   (a) exact-lure-absent endorsement, renamed literally, PER TRIAL (distribution + bootstrap CI over trials,
#       because 72 lure opportunities are not 72 minds)
#   (b) note-budget compliance as part of the CONDITION: compliant-only vs over-budget split
#   (c) the semantic sensitivity analysis (POST-RESULT, labelled so) from the blinded note audit
# 🧪 POSITIVE CONTROL FIRST: the pooled exact-lure-absent counts must reproduce the draft
#   (hermes 46/62 · llama 21/49 · qwen 30/64) or this parser is wrong and nothing below counts.
import json, re, sys, random, collections
random.seed(20261011)
run, audit = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
rows = [json.loads(l) for l in open(run, encoding="utf-8") if l.startswith("{")]
B = [r for r in rows if r.get("arm") == "B"]
LURES = ["anger","black","bread","chair","cold","doctor","foot","fruit","girl","high","king","man"]

def judgments(raw):
    d = {}
    for line in raw.splitlines():
        m = re.match(r"\s*[\*\-\d\.\)]*\s*([A-Za-z]+)\s*[:\-–]\s*\**\s*(Old|New)", line, re.I)
        if m: d.setdefault(m.group(1).lower(), m.group(2).lower() == "old")
    return d

codes = {}
if audit:
    for l in open(audit, encoding="utf-8"):
        u = json.loads(l)
        codes[(u["model"], u["form"], u["seed"], u["lure"])] = u

def boot(xs, n=10000):
    if not xs: return (float("nan"),) * 2
    ms = sorted(sum(random.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return ms[int(.025 * n)], ms[int(.975 * n)]

def consensus(u):
    cs = [v["category"] for v in u["codes"].values()]
    return cs[0] if len(set(cs)) == 1 and cs[0] is not None else None

by_model = collections.defaultdict(list)
for r in B: by_model[r["model"]].append(r)

print("=" * 100)
for model in sorted(by_model):
    trials = by_model[model]
    pooled_old = pooled_n = 0
    per_trial, comp, over = [], [], []
    sem = collections.defaultdict(lambda: [0, 0])      # consensus category -> [old, n]
    disagree = [0, 0]
    for r in trials:
        studied = LURES[:6] if r["form"] == "X" else LURES[6:]
        j = judgments(r["recog_raw"])
        absent = [l for l in studied if l not in r.get("note_lures_studied", [])]
        olds = [j.get(l) for l in absent]
        valid = [o for o in olds if o is not None]
        pooled_old += sum(valid); pooled_n += len(valid)
        if valid:
            p = sum(valid) / len(valid)
            per_trial.append(p)
            (over if r["note_over_budget"] else comp).append(p)
        for l in absent:
            u = codes.get((r["model"], r["form"], r["seed"], l))
            if u is None or j.get(l) is None: continue
            c = consensus(u)
            if c is None:
                disagree[0] += j[l]; disagree[1] += 1
            else:
                sem[c][0] += j[l]; sem[c][1] += 1
    lo, hi = boot(per_trial)
    nover = sum(r["note_over_budget"] for r in trials)
    print(f"{model}")
    print(f"  ✅ control: pooled exact-lure-absent endorsement {pooled_old}/{pooled_n}")
    print(f"  per-trial (n={len(per_trial)} trials): mean {sum(per_trial)/len(per_trial):.2f}  95% CI over trials [{lo:.2f}, {hi:.2f}]"
          f"  values: {' '.join(f'{p:.2f}' for p in sorted(per_trial))}")
    print(f"  note budget: over 60 words in {nover}/{len(trials)} trials;"
          f" compliant-only mean {('%.2f' % (sum(comp)/len(comp))) if comp else '—'} (n={len(comp)} trials)"
          f" · over-budget mean {('%.2f' % (sum(over)/len(over))) if over else '—'} (n={len(over)})")
    if audit:
        print("  🔍 semantic audit (POST-RESULT sensitivity; both coders agree):")
        for c in (1, 2, 3, 4, 5):
            o, n = sem[c]
            print(f"     cat {c}: {o}/{n}" + (f" = {o/n:.2f}" if n else ""))
        print(f"     coders disagree: {disagree[0]}/{disagree[1]} endorsed Old (kept, not forced)")
print("DONE (fences complete)")
