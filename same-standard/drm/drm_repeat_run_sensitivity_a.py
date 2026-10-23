"""🧪 DRM repeat-run SENSITIVITY (a): complete-parse keys only. EXPLORATORY. NEVER A REPLACEMENT.

Written 2026-10-23 ~02:0x by the heartbeat arm, after Kairo's fresh-eyes read found the denominator asymmetry
(LS = parsed subset; LU/FILL = full item count with unparsed scored not-old) and Nova's review pinned what it
does and doesn't mean. Spec: penpals/for_review/DRM_readout_caption_DRAFT_2026-10-23.md §5 (a), which both agreed
at SPEC level (Nova 01:46, Kairo 01:45). ⛔ COMMITTED BEFORE IT RUNS. Nova and Kairo read these bytes first.

What it does, and nothing beyond:
  1. The same gates as drm_repeat_run.main(): sealed spec + both addenda + fixtures sha-pinned, the parser pin,
     and the 45/45 fixture gate in a subprocess. On top of those it pins drm_repeat_run.py itself (the reviewed
     8c0c89c bytes) and both input files (the shas printed in the 70887c1 readout). Any mismatch → STOP, no data read.
  2. Runs the SEALED drm_repeat_run.analyze() unchanged, to get the sealed cells and their retained keys.
  3. Within each sealed cell, keeps a key only if ALL THREE of its rows (O, U, W) are complete-parse for that cell:
        LS-missing (eligible − parsed, from the pinned ls_detail) == 0
        AND the cell's control has 0 unparsed (recog_lure_unstudied_unparsed for LS_LU,
                                               recog_filler_unparsed for LS_FILL).
     An absent or non-int *_unparsed field counts as NOT complete (dropped, reason printed), never as 0.
     Keys the sealed analysis excluded stay excluded; this only ever REMOVES keys.
  4. On the retained keys the sealed scoring rule applies exactly (no control item is unparsed there), with the
     same A/B values as the sealed cell, NOT recomputed differently.
  5. Bootstrap: np.random.default_rng(SEED) created once, cells iterated in the sealed MODELS × CONTRASTS order,
     NBOOT resamples, one index array shared by A and B, percentile 95%. Fewer than 2 retained → "not computable".
  6. Headline output per cell: does the zero-inclusion verdict for mean B agree with the sealed cell's verdict?
     Means/intervals are printed under that, every line labelled EXPLORATORY.

Missingness assumption (stated before calculating, per Nova): none about the dropped rows; they are excluded.
The result describes the complete-parse SUBSET only, which may not be representative. No unparsed response is
assumed to be a genuine not-old judgment. Variant (ii) (uniform parsed-subset rescoring) is NOT in scope and is not
implemented here. ⛔ Nothing here reopens P1/P2, bears on the sealed P4 gate, or replaces any sealed number.
"""
import sys, hashlib, subprocess
import numpy as np
import drm_repeat_run as R          # the REVIEWED module, pinned below before anything is used
from drm_pertrial_rates import check_parser_pin

PINNED_MODULE = ("drm_repeat_run.py", "2eb3b71e23b48578265356f2435dcf3c40807201b0a4065179a00cadc77721fc")  # 8c0c89c
PINNED_INPUTS = {R.O_FILE: "092e681a7588f1534242dd12db89ff8593e958ccda00f3da992fc8e71607873a",   # 70887c1 readout
                 R.F_FILE: "cb2a9ae3f5f75c52c44c9df59fc3f2f974115c7f05787cc5cb42549e52bbca8c"}
CONTROL_FIELD = {"LS_LU": "recog_lure_unstudied_unparsed", "LS_FILL": "recog_filler_unparsed"}
TAG = "EXPLORATORY (a), complete-parse subset, not the sealed result:"

def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()

def incomplete_reasons(r, c):
    """Why row r is NOT complete-parse for contrast c ([] = complete). Pure; self-tested below."""
    why = []
    elig, parsed = R.ls_detail(r)
    if elig - parsed != 0: why.append(f"LS missing {elig - parsed}")
    f = CONTROL_FIELD[c]
    v = r.get(f, None)
    if not isinstance(v, int) or isinstance(v, bool): why.append(f"{f} absent/invalid ({v!r})")
    elif v != 0: why.append(f"{f} {v}")
    return why

def zero_in(ci): return ci[0] <= 0.0 <= ci[1]

def gates():
    for path, want in (R.SPEC, R.ADDENDUM, R.ADDENDUM2, R.FIXTURES, PINNED_MODULE, *PINNED_INPUTS.items()):
        got = sha(path)
        if got != want: print(f"⛔ STOPPED: {path} sha {got} ≠ pinned {want}"); sys.exit(2)
        print(f"  {path} sha {got} OK")
    try: pin = check_parser_pin()
    except AssertionError as e: print(f"⛔ STOPPED: parser pin: {e}"); sys.exit(2)
    if not isinstance(pin, str) or len(pin) != 64: print(f"⛔ STOPPED: parser pin returned {pin!r}"); sys.exit(2)
    g = subprocess.run([sys.executable, R.FIXTURES[0]], capture_output=True, text=True)
    if g.returncode != 0: print(g.stdout[-2000:]); print("⛔ STOPPED: fixture gate failed; data NOT read"); sys.exit(2)
    print(f"  fixture gate: {g.stdout.strip().splitlines()[-1]} · parser pin {pin} OK · this script sha {sha(__file__)}")

def selftest():
    """Positive AND negative controls on incomplete_reasons, with ls_detail stubbed (it is the pinned one in use)."""
    real = R.ls_detail
    try:
        R.ls_detail = lambda r: (r["_e"], r["_p"])
        ok = lambda **k: dict(_e=4, _p=4, recog_lure_unstudied_unparsed=0, recog_filler_unparsed=0) | k
        cases = [(ok(), "LS_LU", False), (ok(), "LS_FILL", False),
                 (ok(_p=2), "LS_LU", True),                                   # LS side alone drops it (seed3 shape)
                 (ok(recog_lure_unstudied_unparsed=6), "LS_LU", True),        # control side alone drops it (seed5)
                 (ok(recog_lure_unstudied_unparsed=6), "LS_FILL", False),     # LU loss does not touch the FILL cell
                 (ok(recog_filler_unparsed=1), "LS_FILL", True),
                 ({k: v for k, v in ok().items() if k != "recog_filler_unparsed"}, "LS_FILL", True),  # absent ≠ 0
                 (ok(recog_filler_unparsed=True), "LS_FILL", True)]           # a bool is not an int count
        bad = [(i, c, want) for i, (r, c, want) in enumerate(cases) if bool(incomplete_reasons(r, c)) != want]
    finally:
        R.ls_detail = real
    if bad: print(f"⛔ STOPPED: selftest failed {bad}"); sys.exit(2)
    print(f"  selftest: {len(cases)}/{len(cases)} complete-parse cases behave as specified")

def main():
    gates(); selftest()
    o = open(R.O_FILE, encoding="utf-8").read().splitlines()
    f = open(R.F_FILE, encoding="utf-8").read().splitlines()
    res = R.analyze(o, f)                                    # the SEALED analysis, unchanged
    if res["status"] != "ok": print(f"⛔ STOPPED: sealed analysis stopped: {res['reason']}"); sys.exit(1)
    rows = {}                                                # (run, key) → row, re-parsed with the sealed parsers
    log = []
    _, o_rows, _ = R.parse_file(o, "PREREG_RUN", {"A", "B", "C"}, None, log, "O-file")
    _, f_rows, _ = R.parse_file(f, "FOREWARN_RUN", {"B"}, {"unwarned", "warned"}, log, "F-file")
    for n, d in (("O", R.no_dupes(o_rows, "O")),
                 ("U", R.no_dupes([r for r in f_rows if r["condition"] == "unwarned"], "U")),
                 ("W", R.no_dupes([r for r in f_rows if r["condition"] == "warned"], "W"))):
        for k, r in d.items(): rows[(n, k)] = r
    rng = np.random.default_rng(R.SEED)
    print(f"\n━━ {TAG} B = W − U, per sealed cell (nothing here replaces the sealed table)")
    agree_all = True
    for m in R.MODELS:
        for c in R.CONTRASTS:
            cell = res["cells"][(m, c)]
            keep, drop = [], {}
            for i, k in enumerate(cell["keys"]):
                why = [f"{n}: {'; '.join(w)}" for n in ("O", "U", "W") if (w := incomplete_reasons(rows[(n, k)], c))]
                if why: drop[k] = why
                else: keep.append(i)
            print(f"\n  {m} · {c}: sealed retained {cell['retained']} · complete-parse retained {len(keep)} · dropped {len(drop)}")
            for k, why in drop.items(): print(f"    dropped {k[1]}/seed{k[2]}: {' | '.join(why)}")
            if len(keep) < 2 or "ciB" not in cell:
                print(f"    {TAG} NOT COMPUTABLE (fewer than 2 complete-parse keys, or no sealed interval)"); continue
            A, B = cell["A"][keep], cell["B"][keep]
            idx = rng.integers(0, len(keep), size=(R.NBOOT, len(keep)))
            mA, mB = A[idx].mean(1), B[idx].mean(1)
            ciA = (np.percentile(mA, 2.5), np.percentile(mA, 97.5))
            ciB = (np.percentile(mB, 2.5), np.percentile(mB, 97.5))
            same = zero_in(ciB) == zero_in(cell["ciB"])
            agree_all &= same
            print(f"    VERDICT: sealed mean-B interval {'includes' if zero_in(cell['ciB']) else 'EXCLUDES'} zero · "
                  f"complete-parse {'includes' if zero_in(ciB) else 'EXCLUDES'} zero → {'AGREE' if same else 'DIFFER'}")
            print(f"    {TAG} mean A {A.mean():+.4f} [{ciA[0]:+.4f}, {ciA[1]:+.4f}] · mean B {B.mean():+.4f} "
                  f"[{ciB[0]:+.4f}, {ciB[1]:+.4f}] · n {len(keep)}")
    print(f"\n  {'All computable cells AGREE with the sealed zero-inclusion verdict.' if agree_all else 'At least one cell DIFFERS; see above.'}"
          "\n  Subset only, may be unrepresentative; no unparsed response is assumed to be a not-old judgment."
          "\n  ⛔ Not a corrected estimate. Nothing here reopens P1/P2 or bears on P4.")
    print("DONE (sensitivity (a) complete)")

if __name__ == "__main__":
    main()
