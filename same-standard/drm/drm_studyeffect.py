# 🔍 Kairo's question, answered from the data before he has to ask twice:
# "does arm C's general Old bias swamp a SMALL study effect I can't see at this N?"
# The cleanest study-effect contrast in the design: studied-list words (target) vs
# words from the NEVER-studied lists (assoc_unstudied) — same item type, only difference
# is whether that list was shown. Paired WITHIN each trial (same test, same bias), so a
# trial-level Old bias cancels. Bootstrap over trials (12 per model × arm).
# Arms A and B ride along as POSITIVE CONTROLS: if the contrast can't see their effect, it's blind.
import json, sys, random, collections
random.seed(20261010)
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.startswith("{")]
trials = [r for r in rows[1:] if "arm" in r]
g = collections.defaultdict(list)
for r in trials:
    g[(r["model"], r["arm"])].append(r)

def rate(r, k): return r[f"recog_{k}_old"] / r[f"recog_{k}_n"]

def boot(ds, B=10000):
    ms = sorted(sum(random.choice(ds) for _ in ds) / len(ds) for _ in range(B))
    return ms[int(.025 * B)], ms[int(.975 * B)]

print("paired per-trial difference, P(Old|studied-list word) − P(Old|never-studied-list word); 95% bootstrap CI over trials")
for (model, arm), rs in sorted(g.items()):
    d = [rate(r, "target") - rate(r, "assoc_unstudied") for r in rs]
    dl = [rate(r, "lure_studied") - rate(r, "lure_unstudied") for r in rs]
    m, ml = sum(d) / len(d), sum(dl) / len(dl)
    lo, hi = boot(d); llo, lhi = boot(dl)
    print(f"{model:13} arm {arm}  words Δ {m:+.3f} [{lo:+.3f}, {hi:+.3f}]   lures Δ {ml:+.3f} [{llo:+.3f}, {lhi:+.3f}]   n={len(rs)}")
print("DONE (study-effect contrast complete)")
