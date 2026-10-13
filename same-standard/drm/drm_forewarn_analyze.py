# 📊 DRM forewarning — P1 + P2 readout, through the SEALED machinery only. heartbeat arm, 2026-10-13.
#   per-trial rates  → drm_pertrial_rates.per_trial  (parser pinned to e3823fdc, refuses to run otherwise)
#   P2 doors         → sealed/drm_forewarn_doors.p2_door (imports sealed/doors.py; δ, rules, seed untouched)
#   Nothing here re-types a rule. What this file adds is only bookkeeping: split by condition, pair by note.
#   ⛔ NOT done here (said out loud so a blank isn't read as a pass): P3 (theme-selective share, sensitivity-only)
#      and the fidelity-tercile description. Both are next, as their own step.
import json, sys, os, collections, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "sealed"))
import drm_pertrial_rates as X
from drm_forewarn_doors import p2_door, boot_ci

def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.startswith('{"model"')]

def paired_ci(diffs, B=10000, seed=20261013):
    rng = random.Random(seed); n = len(diffs)
    m = sorted(sum(rng.choice(diffs) for _ in range(n)) / n for _ in range(B))
    return m[int(.025 * B)], m[int(.975 * B)]

if __name__ == "__main__":
    os.chdir(HERE); X.check_parser_pin()
    run, orig = sys.argv[1], sys.argv[2]
    rows = load(run)
    assert all(r.get("label") == "FOREWARN_RUN" for r in rows), "non-FOREWARN rows in the run file"
    by = collections.defaultdict(dict)                     # (model, form, seed) -> {condition: trial}
    for r in rows:
        t = X.per_trial([r])[0]; t["condition"] = r["condition"]
        by[(r["model"], r["form"], r["seed"])][r["condition"]] = t
    origt = {(t["model"], t["form"], t["seed"]): t for t in X.per_trial(load(orig))}
    print(f"run {os.path.basename(run)}: {len(rows)} rows, {len(by)} notes, both conditions on "
          f"{sum(1 for v in by.values() if len(v) == 2)}")
    p1 = collections.defaultdict(list); p4 = collections.defaultdict(list)
    for model in sorted({k[0] for k in by}):
        keys = sorted(k for k in by if k[0] == model)
        print(f"\n━━ {model}  (n = {len(keys)} notes)")
        for cond in ("unwarned", "warned"):
            ts = [by[k][cond] for k in keys]
            ls = [t for t in ts if t["LS"] is not None]
            mean = lambda f, xs: sum(x[f] for x in xs) / len(xs)
            print(f"  {cond:8}  LS {sum(t['LS_old'] for t in ts)}/{sum(t['LS_n'] for t in ts)}"
                  f" · LU {mean('LU', ts):.3f} · FILL {mean('FILL', ts):.3f} · TARGET {mean('TARGET', ts):.3f}"
                  f" · per-trial LS−LU {mean('LS_LU', ls):+.3f} · LS−FILL {mean('LS_FILL', ls):+.3f}")
        # 🔁 reproduction control: fresh unwarned vs the original Oct-10 row (same note, seed, T)
        same = sum(1 for k in keys if by[k]["unwarned"]["LS_old"] == origt[k]["LS_old"]
                   and by[k]["unwarned"]["LU_old"] == origt[k]["LU_old"] and by[k]["unwarned"]["FILL_old"] == origt[k]["FILL_old"])
        print(f"  repro: fresh unwarned matches Oct-10 on LS/LU/FILL counts in {same}/{len(keys)} notes")
        for c in ("LS_LU", "LS_FILL"):
            pk = [k for k in keys if by[k]["warned"][c] is not None and by[k]["unwarned"][c] is not None]
            d = [by[k]["warned"][c] - by[k]["unwarned"][c] for k in pk]
            L1, U1 = paired_ci(d)
            md = sum(d) / len(d)   # sealed P1 is a point comparison; printed to 6 places so a rounding -0.000 can't read as "lower"
            P1 = "lower" if md < 0 else "NOT lower"
            p1[model].append(md < 0)
            tdrop = mean('TARGET', [by[k]["unwarned"] for k in keys]) - mean('TARGET', [by[k]["warned"] for k in keys])
            p4[model].append(tdrop < -md)    # P4: target drop < lure-contrast drop (drop = unwarned - warned = -md)
            w = [by[k]["warned"][c] for k in keys if by[k]["warned"][c] is not None]
            L, U, door = p2_door(w)
            print(f"  {c:7} P1 warned−unwarned (paired) {md:+.6f} [{L1:+.3f}, {U1:+.3f}] → {P1}"
                  f"   |  P2 warned CI [{L:+.3f}, {U:+.3f}] → door {door}")
    print("\nSEALED VERDICTS (literal, per model):")
    for m in sorted(p1):
        print(f"  {m:13} P1 (both contrasts lower): {'HOLDS' if all(p1[m]) else 'FAILS'}   "
              f"P4 (target drop < each contrast drop): {'HOLDS' if all(p4[m]) else 'FAILS'}")
    print("\nDONE (P1 + P2 readout complete; P3 and fidelity terciles NOT run here)")
