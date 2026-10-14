# 🧩 DRM forewarning: P3 (theme-selective SHARE, sensitivity only) + the fidelity-tercile description.
#   ScienceAce beat, heartbeat arm, 2026-10-13 ~19:1x. The step drm_forewarn_analyze.py said out loud it did NOT do.
#
#   Everything sealed is IMPORTED or CHECKED, never re-typed:
#     parser      → drm_pertrial_rates.judgments + check_parser_pin (pin e3823fdc, refuses to run if moved)
#     seal        → sha256 of sealed/FOREWARNING_PREDICTION_v0_6_SEALED.md must be f3e3f002…
#     strata      → consensus() rule copied from drm_armB_fences.py (both coders agree, else "disagree")
#
#   P3, as sealed (v0.6, "P3" bullet), per model × audit version (v1, v2) × floor (LU, FILL):
#     share_F = [(LS_U − F_U) − (LS_W − F_W)] / (LS_U − F_U)     F = the model's own floor, SAME condition
#     test quantity = share(cat 3) − share(cat 4), 95% percentile bootstrap over TRIALS (notes),
#     with the stratum LS and the floors re-estimated on every resample. Never capped.
#     point denominator ≤ 0 for a stratum → "no headroom", P3 not evaluated in that cell.
#     > 5% of resamples with denominator ≤ 0 → "unstable", no interval printed.
#
#   📌 MY CHOICES (not in the seal; stated so they can be argued with):
#     (a) a stratum's LS is POOLED over its units in the (re)sampled notes (Old / n), because units are 0–2 per note;
#     (b) a resample whose stratum has ZERO units has no LS at all; it is counted toward the >5% "unstable"
#         tally alongside denominator ≤ 0 (undefined is not a number, so it can't be quietly skipped);
#     (c) a unit whose recognition line didn't parse in ONE condition is dropped from that condition only
#         (the fences rule); the count of such drops is printed.
#     (d) fidelity tercile bins: notes sorted by fidelity, ties broken by (form, seed), cut 4 / 4 / 4.
#
#   🧪 POSITIVE CONTROLS (must pass or nothing below counts):
#     stratum unit counts reproduce the seal's "cat 3: v1 9/9/17, v2 6/4/13" (hermes/llama/qwen)
#     mean note fidelity reproduces the seal's hermes .64 · llama .41 · qwen .54
import json, sys, os, random, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_pertrial_rates as X

SEAL = "sealed/FOREWARNING_PREDICTION_v0_6_SEALED.md"
SEAL_SHA = "f3e3f002dede4190d811745c603c55ab7c5c353bc52c46e2ed5842a82e4dc1ea"
AUDITS = {"v1": "data/note_audit_2026-10-11.jsonl", "v2": "data/note_audit_v2_2026-10-11.jsonl"}
B, SEED = 10000, 20261013

def consensus(u):  # verbatim rule from drm_armB_fences.py
    cs = [v["category"] for v in u["codes"].values()]
    return cs[0] if len(set(cs)) == 1 and cs[0] is not None else None

def load_codes(path):
    codes = {}
    for l in open(path, encoding="utf-8"):
        u = json.loads(l)
        codes[(u["model"], u["form"], u["seed"], u["lure"])] = consensus(u)
    return codes

def note_units(r, codes):
    """exact-lure-absent studied lures of this note → audit category (None = coders disagree / missing)."""
    studied = X.LURES[:6] if r["form"] == "X" else X.LURES[6:]
    absent = [l for l in studied if l not in r.get("note_lures_studied", [])]
    return {l: codes.get((r["model"], r["form"], r["seed"], l)) for l in absent}

COMPLETE_CASE = "--complete-case" in sys.argv   # Nova 2026-10-13: keep only units parsed in BOTH conditions

def cell(notes, cat, floor):
    """notes: list of dicts {cond: row-info}. Returns (share or None, reason)."""
    acc = {}
    for cond in ("unwarned", "warned"):
        o = n = fo = fn = 0
        for nt in notes:
            info = nt[cond]
            for l, c in nt["units"].items():
                if COMPLETE_CASE and (nt["unwarned"]["j"].get(l) is None or nt["warned"]["j"].get(l) is None):
                    continue
                if c == cat and info["j"].get(l) is not None:
                    o += info["j"][l]; n += 1
            fo += info[floor + "_old"]; fn += info[floor + "_n"]
        if n == 0: return None, "no units"
        acc[cond] = (o / n, fo / fn)
    (lsU, fU), (lsW, fW) = acc["unwarned"], acc["warned"]
    den = lsU - fU
    if den <= 0: return None, "no headroom"
    return ((lsU - fU) - (lsW - fW)) / den, "ok"

if __name__ == "__main__":
    os.chdir(HERE); X.check_parser_pin()
    sha = hashlib.sha256(open(SEAL, "rb").read()).hexdigest()
    assert sha == SEAL_SHA, f"seal hash moved: {sha[:8]}"
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.startswith('{"model"')]
    assert all(r["label"] == "FOREWARN_RUN" for r in rows)
    notes = collections.defaultdict(dict)
    parse_drops = collections.Counter()
    for r in rows:
        k = (r["model"], r["form"], r["seed"])
        j = X.judgments(r["recog_raw"])
        notes[k][r["condition"]] = dict(j=j, row=r,
            LU_old=r["recog_lure_unstudied_old"], LU_n=r["recog_lure_unstudied_n"],
            FILL_old=r["recog_filler_old"], FILL_n=r["recog_filler_n"])
    models = sorted({k[0] for k in notes})
    orig = {(r["model"], r["form"], r["seed"]): r for r in
            (json.loads(l) for l in open("data/prereg_run_2026-10-10.jsonl", encoding="utf-8") if l.startswith("{"))
            if r.get("arm") == "B"}
    print(f"parser pin OK · seal f3e3f002 OK · {len(rows)} rows · {len(notes)} notes")
    print("MODE: " + ("COMPLETE-CASE sensitivity (a unit counts only if parsed in BOTH conditions)" if COMPLETE_CASE
                      else "primary (choice c: unparsed units dropped per condition)"))

    # ─── P3 ───
    ok_ctrl = True
    expect3 = {"v1": [9, 9, 17], "v2": [6, 4, 13]}
    for ver, path in AUDITS.items():
        codes = load_codes(path)
        print(f"\n━━━━ P3 · audit {ver} ({os.path.basename(path)})")
        for mi, m in enumerate(models):
            keys = sorted(k for k in notes if k[0] == m)
            ns = []
            for k in keys:
                d = dict(notes[k]); d["units"] = note_units(d["unwarned"]["row"], codes)
                for cond in ("unwarned", "warned"):
                    parse_drops[(ver, m, cond)] += sum(1 for l in d["units"] if d[cond]["j"].get(l) is None)
                ns.append(d)
            cnt = collections.Counter(c for d in ns for c in d["units"].values())
            # the seal's "9/9/17, 6/4/13" are PARSED units (fences rule: a unit counts only with a judgment).
            # First run of this script compared ALL units and llama read 10 vs 9 (v1), 5 vs 4 (v2): one llama
            # cat-3 unit didn't parse on Oct 10. Definition mismatch in my control, confirmed by re-running
            # drm_armB_fences.py on prereg_run (llama cat 3 = 7/9 v1, 2/4 v2). So: compare parsed-in-unwarned.
            # Second run: the FRESH unwarned run parsed that unit (10/10), so fresh-vs-seal still mixed two runs.
            # The honest control is MY unit keying applied to the OCT-10 rows the seal counted.
            parsed3 = sum(1 for d in ns for l, c in d["units"].items()
                          if c == 3 and X.judgments(orig[(m, d["unwarned"]["row"]["form"], d["unwarned"]["row"]["seed"])]["recog_raw"]).get(l) is not None)
            ctrl = parsed3 == expect3[ver][mi]; ok_ctrl &= ctrl
            print(f"  {m}: units cat3 {cnt[3]} (parsed unwarned {parsed3} {'✅' if ctrl else '❌ expected ' + str(expect3[ver][mi])})"
                  f" · cat4 {cnt[4]} · disagree/missing {cnt[None]}"
                  f" · parse drops U/W {parse_drops[(ver, m, 'unwarned')]}/{parse_drops[(ver, m, 'warned')]}")
            for floor in ("LU", "FILL"):
                s3, r3 = cell(ns, 3, floor); s4, r4 = cell(ns, 4, floor)
                if s3 is None or s4 is None:
                    print(f"    {floor:4} share3 {r3 if s3 is None else f'{s3:+.3f}'} · share4 {r4 if s4 is None else f'{s4:+.3f}'}"
                          f" → P3 NOT EVALUATED ({'no headroom' if 'no headroom' in (r3, r4) else 'no units'})")
                    continue
                rng = random.Random(SEED); diffs = []; bad = 0
                for _ in range(B):
                    smp = [rng.choice(ns) for _ in ns]
                    a, _ = cell(smp, 3, floor); b, _ = cell(smp, 4, floor)
                    if a is None or b is None: bad += 1
                    else: diffs.append(a - b)
                pt = s3 - s4
                if bad / B > .05:
                    ci = f"UNSTABLE ({bad/B:.1%} of resamples undefined or ≤0 denominator; no interval)"
                else:
                    diffs.sort(); L, U = diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))]
                    ci = f"[{L:+.3f}, {U:+.3f}] ({bad} bad resamples)"
                print(f"    {floor:4} share3 {s3:+.3f} · share4 {s4:+.3f} · share3−share4 {pt:+.3f} {ci}")
    print(f"\n  P3 positive control (cat-3 unit counts match the seal): {'✅ PASS' if ok_ctrl else '❌ FAIL — P3 above does not count'}")

    # ─── fidelity terciles (description only; no interaction fitted) ───
    print("\n━━━━ Fidelity terciles within model (warned − unwarned, paired per note; 4-note bins; NOT randomized)")
    expectF = {"hermes3:8b": .64, "llama3.1:8b": .41, "qwen2.5:14b": .54}
    okF = True
    for m in models:
        keys = sorted(k for k in notes if k[0] == m)
        fid = {k: notes[k]["unwarned"]["row"]["note_studied_kept"] / notes[k]["unwarned"]["row"]["note_studied_total"] for k in keys}
        mf = sum(fid.values()) / len(fid); c = abs(mf - expectF[m]) < .005; okF &= c
        print(f"  {m}: mean fidelity {mf:.3f} {'✅' if c else '❌ expected ' + str(expectF[m])}")
        order = sorted(keys, key=lambda k: (fid[k], k[1], k[2]))
        pt = {k: {cond: X.per_trial([notes[k][cond]["row"]])[0] for cond in ("unwarned", "warned")} for k in keys}
        for b, name in enumerate(("low", "mid", "high")):
            ks = order[4 * b: 4 * b + 4]
            line = f"    {name:4} fid {min(fid[k] for k in ks):.2f}–{max(fid[k] for k in ks):.2f}"
            for con in ("LS_LU", "LS_FILL"):
                d = [pt[k]["warned"][con] - pt[k]["unwarned"][con] for k in ks
                     if pt[k]["warned"][con] is not None and pt[k]["unwarned"][con] is not None]
                line += f" · {con} Δ {sum(d)/len(d):+.3f} (n={len(d)})" if d else f" · {con} Δ — (n=0)"
            tg = sum(pt[k]["warned"]["TARGET"] - pt[k]["unwarned"]["TARGET"] for k in ks) / 4
            print(line + f" · TARGET Δ {tg:+.3f}")
    print(f"\n  fidelity positive control: {'✅ PASS' if okF else '❌ FAIL — terciles above do not count'}")
    print("\nDONE (P3 + fidelity terciles; sensitivity / description only, as sealed)")
