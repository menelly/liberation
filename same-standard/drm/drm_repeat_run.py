"""🔁 DRM forewarning: historical repeat-run description + conditional normal-reference planning benchmarks.

Implements, and nothing beyond:
  sealed/NOCHANGE_BASELINE_SPEC_v3_SEALED.md            sha256 681c66e4…8df308 (liberation f844adb)
  sealed/NOCHANGE_BASELINE_SPEC_v3_ADDENDUM_1_SEALED.md sha256 f2cdb7c3…f6baec (liberation 1d69393)
  sealed/NOCHANGE_BASELINE_SPEC_v3_ADDENDUM_2_SEALED.md implementation clarifications (sha pinned at seal time)
Rewrite 3, 2026-10-15 heartbeat arm, after Nova's rewrite-2 synthetic review (n=0 sensitivity hidden, zero-
denominator over-exclusion, missing temperature read as agreement, header values/per-key provenance missing,
malformed schema crashing, no enforced fixture gate) and Kairo's (pin returning None; reason (b) inferred).
⛔ main() reads real data ONLY after the pinned fixture file passes in a subprocess, and only once every pin
   below is filled in at seal/review time. Until then its output means nothing.

Shape: analyze(o_lines, f_lines) is pure (rows in → STOP(reason) or results); report(res) renders what a reader
receives; both are fixture-tested. Notation (spec): O = Oct-10 unwarned arm B · U = Oct-13 unwarned ·
W = Oct-13 warned; unit = note, key = (model, form, seed); A = U − O (an OBSERVED UNWARNED REPEAT-RUN
DIFFERENCE, never "noise"); B = W − U.
⛔ No threshold, no resolver, no gate. Nothing here makes P1/P2 interpretable again (the P4 gate stands).
"""
import json, sys, hashlib, collections
import numpy as np
from drm_pertrial_rates import per_trial, check_parser_pin, judgments, LURES   # the PINNED path

SPEC = ("sealed/NOCHANGE_BASELINE_SPEC_v3_SEALED.md",
        "681c66e47bf6ead01e165a04be8d09ec17dc24f74014ae14afb06b00058df308")
ADDENDUM = ("sealed/NOCHANGE_BASELINE_SPEC_v3_ADDENDUM_1_SEALED.md",
            "f2cdb7c37dd74028d1d122ed604e60889d9e7800ecbde269cf2e155238f6baec")
ADDENDUM2 = ("sealed/NOCHANGE_BASELINE_SPEC_v3_ADDENDUM_2_SEALED.md",        # Nova yes 13:32 on these bytes
             "a6ee5e5184c4ac7d1437b1b8a22045e5a5d671b04b755c9f837216e1725904a7")
FIXTURES = ("drm_repeat_run_fixtures.py",                                     # 45/45, final reviewed fixtures
            "a86964a144f7bbe1a7fd4a58d42f79cca6bb8c064f6b21e43b4b6a0dd398b346")
O_FILE, F_FILE = "data/prereg_run_2026-10-10.jsonl", "data/forewarn_run_2026-10-13.jsonl"
DONE_LINE = "DONE (search complete)"
MODELS, FORMS, SEEDS = ["hermes3:8b", "llama3.1:8b", "qwen2.5:14b"], ["X", "Y"], list(range(6))
UNIVERSE = [(m, f, s) for m in MODELS for f in FORMS for s in SEEDS]           # 36 keys (Addendum 1)
SEED, NBOOT, Z = 20261015, 10_000, 2.80
SIGMA_GRID = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
SCENARIOS = {"LS_LU": [0.10, 0.27], "LS_FILL": [0.10]}                         # .27 LS−LU only
CONTRASTS = ["LS_LU", "LS_FILL"]
DEPS = ["model", "form", "seed", "arm", "recog_raw",                            # pinned per_trial()'s inputs
        "recog_lure_unstudied_old", "recog_lure_unstudied_n", "recog_filler_old", "recog_filler_n",
        "recog_target_old", "recog_target_n"]
INT_FIELDS = [f"recog_{a}_{b}" for a in ("lure_unstudied", "filler", "target", "lure_studied", "assoc_unstudied")
              for b in ("old", "n", "unparsed")]

class Stop(Exception):
    """Fail-closed: no statistic is computed after this."""

def sha_text(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def key(r): return (r.get("model"), r.get("form"), r.get("seed"))

def validate_types(r, where):
    """Addendum 2 §2: present-but-invalid → malformed schema (STOP). Absent keeps the declared policies."""
    def bad(msg): raise Stop(f"malformed schema: {where}: {msg}")
    for f in ("label", "arm", "model", "form", "condition"):
        if f in r and not isinstance(r[f], str): bad(f"{f} is {type(r[f]).__name__}, not str")
    if "seed" in r and (not isinstance(r["seed"], int) or isinstance(r["seed"], bool)): bad("seed is not an int")
    if "note" in r and not isinstance(r["note"], str): bad("note is not a str")
    if "note_sha256" in r and not (isinstance(r["note_sha256"], str) and len(r["note_sha256"]) == 64
                                   and all(ch in "0123456789abcdef" for ch in r["note_sha256"])):
        bad("note_sha256 is not 64 lowercase hex")
    if "recog_raw" in r and not isinstance(r["recog_raw"], str): bad("recog_raw is not a str")
    if "note_lures_studied" in r and not (isinstance(r["note_lures_studied"], list)
                                          and all(isinstance(x, str) for x in r["note_lures_studied"])):
        bad("note_lures_studied is not a list of str")
    for f in INT_FIELDS:
        if f in r and (not isinstance(r[f], int) or isinstance(r[f], bool) or r[f] < 0): bad(f"{f} is not an int ≥ 0")
    for a in ("lure_unstudied", "filler", "target", "lure_studied", "assoc_unstudied"):   # all five (Nova, §2)
        o, n = r.get(f"recog_{a}_old"), r.get(f"recog_{a}_n")
        if isinstance(o, int) and isinstance(n, int) and o > n: bad(f"recog_{a}_old > recog_{a}_n")

def parse_file(lines, label, allowed_arms, allowed_conds, log, name):
    """Schema check for ONE file. Returns (header, arm-B rows, intentional non-analysis row counts)."""
    if not lines or lines[-1].strip() != DONE_LINE:
        raise Stop(f"{name}: last line is not {DONE_LINE!r}")
    header, rows, outside = None, [], collections.Counter()
    for i, ln in enumerate(lines[:-1], 1):
        try:
            r = json.loads(ln)
        except Exception:
            raise Stop(f"{name}: malformed line {i}: {ln[:60]!r}")
        if not isinstance(r, dict):
            raise Stop(f"malformed schema: {name} line {i} is a JSON {type(r).__name__}, not an object")
        validate_types(r, f"{name} line {i}")
        if r.get("label") != label:
            raise Stop(f"{name}: line {i} has label {r.get('label')!r}, expected {label!r}")
        if "arm" not in r:
            if header is not None:
                raise Stop(f"{name}: a second header record at line {i}")
            header = r; continue
        if r["arm"] not in allowed_arms:
            raise Stop(f"{name}: line {i} has arm {r['arm']!r}, not valid for this file")
        if allowed_conds is not None and r.get("condition") not in allowed_conds:
            raise Stop(f"{name}: line {i} has condition {r.get('condition')!r}")
        if r["arm"] != "B":
            outside[r["arm"]] += 1; continue
        if key(r) not in UNIVERSE:
            raise Stop(f"{name}: line {i} key {key(r)} is outside the expected 36-key universe")
        rows.append(r)
    if header is None:
        raise Stop(f"{name}: no header record")
    log.append(f"  {name}: header 1 · arm-B rows {len(rows)} · intentionally outside this analysis "
               f"{dict(outside) or 'none'} · DONE line present")
    return header, rows, outside

def no_dupes(rows, name):
    c = collections.Counter(key(r) for r in rows)
    d = sorted(k for k, n in c.items() if n > 1)
    if d:
        raise Stop(f"{name}: duplicate keys {d} (no row is chosen silently)")
    return {key(r): r for r in rows}

def identity(kO, kU, kW, log):
    """Mandatory identity fields first; three separate checks; any failure stops."""
    for name, d in (("O", kO), ("U", kU), ("W", kW)):
        for k, r in d.items():
            if not isinstance(r.get("note"), str):
                raise Stop(f"identity-presence: {name} {k} has no note text")
            if name != "O" and not isinstance(r.get("note_sha256"), str):
                raise Stop(f"identity-presence: {name} {k} has no note_sha256")
    for name, d in (("U", kU), ("W", kW)):
        for k, r in d.items():                                        # own digest, even if O absent
            if sha_text(r["note"]) != r["note_sha256"]:
                raise Stop(f"identity-digest: {name} {k} note text does not match its own note_sha256")
    for name, d in (("U", kU), ("W", kW)):
        for k, r in d.items():
            if k in kO and sha_text(r["note"]) != sha_text(kO[k]["note"]):
                raise Stop(f"identity-content: {name} {k} note text differs from the Oct-10 note")
    log.append("  identity: presence OK · own-digest OK · cross-run content OK (every present row)")

def ls_detail(r):
    studied = LURES[:6] if r["form"] == "X" else LURES[6:]
    absent = [l for l in studied if l not in r.get("note_lures_studied", [])]
    j = judgments(r["recog_raw"])
    parsed = [l for l in absent if j.get(l) is not None]
    return len(absent), len(parsed)

def rates(r):
    """Guarded call into the pinned extractor (Addendum 1 + Addendum 2 §1).
    Returns ({contrast: value|None}, {contrast: reason|None})."""
    miss = [f for f in DEPS if f not in r]
    if miss:
        reason = "field absent: " + ", ".join(miss)
        return {c: None for c in CONTRASTS}, {c: reason for c in CONTRASTS}
    # TARGET n = 0 is NOT guarded: TARGET enters no contrast and the extractor returns None for it safely.
    lu0, fill0 = r["recog_lure_unstudied_n"] == 0, r["recog_filler_n"] == 0
    if lu0 and fill0:
        return {c: None for c in CONTRASTS}, {c: "control denominators 0 (LU and FILL)" for c in CONTRASTS}
    rr = dict(r)            # a COPY: the zero control gets a placeholder whose contrast is discarded, never reported
    if lu0: rr["recog_lure_unstudied_old"], rr["recog_lure_unstudied_n"] = 0, 1
    if fill0: rr["recog_filler_old"], rr["recog_filler_n"] = 0, 1
    t = per_trial([rr])[0]
    elig, parsed = ls_detail(r)
    vals, reasons = {}, {}
    for c in CONTRASTS:
        if (c == "LS_LU" and lu0) or (c == "LS_FILL" and fill0):
            vals[c], reasons[c] = None, f"control denominator 0 ({'LU' if c == 'LS_LU' else 'FILL'})"; continue
        vals[c] = t[c]
        if t[c] is None:
            if elig == 0:
                reasons[c] = "LS undefined (a): all eligible studied lures were written into the note"
            elif parsed == 0:                                 # Kairo: (b) only when VERIFIED
                reasons[c] = "LS undefined (b): eligible exact-lure-absent items exist but none parsed"
            else:
                reasons[c] = f"LS undefined (unexplained: eligible {elig}, parsed {parsed}); reported, not relabelled"
        else:
            reasons[c] = None
    return vals, reasons

def analyze(o_lines, f_lines, rng_seed=SEED, nboot=NBOOT):
    """Pure core. Returns dict(status='stopped', reason, log) or dict(status='ok', log, cells, outside)."""
    log = []
    try:
        o_head, o_rows, outside = parse_file(o_lines, "PREREG_RUN", {"A", "B", "C"}, None, log, "O-file")
        f_head, f_rows, _ = parse_file(f_lines, "FOREWARN_RUN", {"B"}, {"unwarned", "warned"}, log, "F-file")
        kO = no_dupes(o_rows, "O")
        kU = no_dupes([r for r in f_rows if r["condition"] == "unwarned"], "U")
        kW = no_dupes([r for r in f_rows if r["condition"] == "warned"], "W")
        identity(kO, kU, kW, log)
    except Stop as e:
        return dict(status="stopped", reason=str(e), log=log)

    # ── reported, never used to exclude ──
    log.append("  completeness vs the 36-key universe:")
    for k in UNIVERSE:
        miss = [n for n, d in (("O", kO), ("U", kU), ("W", kW)) if k not in d]
        if miss: log.append(f"    {k}: missing {'/'.join(miss)}")
    log.append(f"    complete triplets: {sum(all(k in d for d in (kO, kU, kW)) for k in UNIVERSE)}/36")
    log.append("  parser loss per run per note (LS eligible/parsed; logged *_unparsed fields):")
    for k in UNIVERSE:
        parts = []
        for n, d in (("O", kO), ("U", kU), ("W", kW)):
            r = d.get(k)
            if r is None: parts.append(f"{n} —"); continue
            if "recog_raw" in r and "form" in r:
                e, p = ls_detail(r)
                un = {f: r.get(f"recog_{f}_unparsed", "ABSENT") for f in ("lure_unstudied", "filler", "target")}
                parts.append(f"{n} LS {p}/{e} (missing {e-p}) unparsed LU {un['lure_unstudied']} "
                             f"FILL {un['filler']} TGT {un['target']}")
            else:
                parts.append(f"{n} recog_raw ABSENT")
        log.append(f"    {k}: " + " | ".join(parts))
    log.append("  item provenance per key (orig_items_missing_from_original_recog: words missing from an earlier ANSWER "
               "TEXT, not proof that presented items/order were identical; item identity otherwise UNAVAILABLE):")
    def prov(d, k):
        r = d.get(k)
        if r is None: return "—"
        if "orig_items_missing_from_original_recog" not in r: return "ABSENT"
        v = r["orig_items_missing_from_original_recog"]
        if not isinstance(v, list):                       # optional field: report INVALID, never read as evidence
            return f"INVALID ({type(v).__name__}: {v!r})"
        return "empty" if not v else f"non-empty {v!r}"
    for k in UNIVERSE:
        log.append(f"    {k}: U {prov(kU, k)} · W {prov(kW, k)}")
    log.append("  realized history per note (recall turn; ready/arithmetic turns: not present in this log):")
    def rec(d, k):                                        # only valid STRINGS are compared; anything else is reported
        r = d.get(k)
        if r is None or "recall_raw" not in r: return None
        v = r["recall_raw"]
        return v if isinstance(v, str) else ("INVALID", type(v).__name__)
    for k in UNIVERSE:
        o, u, w = rec(kO, k), rec(kU, k), rec(kW, k)
        def eq(a, b):
            if isinstance(a, tuple) or isinstance(b, tuple):
                return "UNAVAILABLE (invalid recall value: " + ", ".join(x[1] for x in (a, b) if isinstance(x, tuple)) + ")"
            return "UNAVAILABLE" if a is None or b is None else ("=" if a == b else "≠")
        log.append(f"    {k}: O·U {eq(o,u)}  U·W {eq(u,w)}  O·W {eq(o,w)}")
    log.append("  metadata, as recorded (values, not just names):")
    log.append(f"    Oct-10 header: {json.dumps(o_head, ensure_ascii=False, sort_keys=True)}")
    log.append(f"    Oct-13 header: {json.dumps(f_head, ensure_ascii=False, sort_keys=True)}")
    log.append("  temperature per key (present-equal / present-different / missing):")
    for k in UNIVERSE:
        vals = {n: (d[k].get("temperature", "MISSING") if k in d else "—") for n, d in (("O", kO), ("U", kU), ("W", kW))}
        present = [v for v in vals.values() if v not in ("MISSING", "—")]
        if any(v == "MISSING" for v in vals.values()) or len(present) < 2: st = "missing/unavailable"
        elif len(set(map(repr, present))) == 1 and len(present) == 3: st = "present-equal"
        elif len(set(map(repr, present))) == 1: st = "present-equal (incomplete triplet)"
        else: st = "present-different"
        log.append(f"    {k}: {st}  O {vals['O']} · U {vals['U']} · W {vals['W']}")

    # ── statistics: common valid set per model × contrast, relative to the universe ──
    rO = {k: rates(r) for k, r in kO.items()}
    rU = {k: rates(r) for k, r in kU.items()}
    rW = {k: rates(r) for k, r in kW.items()}
    rng = np.random.default_rng(rng_seed)
    cells = {}
    for m in MODELS:
        for c in CONTRASTS:
            elig = [k for k in UNIVERSE if k[0] == m]
            valid, excl = [], {}
            for k in elig:
                why = [f"missing {n}" for n, d in (("O", rO), ("U", rU), ("W", rW)) if k not in d]
                for n, d in (("O", rO), ("U", rU), ("W", rW)):
                    if k in d and d[k][1][c]: why.append(f"{n}: {d[k][1][c]}")
                if why: excl[k] = why
                else: valid.append(k)
            cell = dict(eligible=len(elig), retained=len(valid), excluded=excl, keys=valid)
            if valid:
                A = np.array([rU[k][0][c] - rO[k][0][c] for k in valid])
                B = np.array([rW[k][0][c] - rU[k][0][c] for k in valid])
                cell.update(A=A, B=B, meanA=A.mean(), meanB=B.mean())
                if len(valid) >= 2:
                    idx = rng.integers(0, len(valid), size=(nboot, len(valid)))   # ONE index array for A and B
                    mA, mB = A[idx].mean(1), B[idx].mean(1)
                    sA = A.std(ddof=1)
                    cell.update(sdA=sA, sdB=B.std(ddof=1), idx=idx,
                                ciA=(np.percentile(mA, 2.5), np.percentile(mA, 97.5)),
                                ciB=(np.percentile(mB, 2.5), np.percentile(mB, 97.5)),
                                mde_grid={s: Z * s / np.sqrt(len(valid)) for s in SIGMA_GRID},
                                mde_at_sdA=Z * sA / np.sqrt(len(valid)))
            # existing-set sensitivity: valid U and W for this contrast, regardless of O; its OWN exclusions
            exist, eexcl = [], {}
            for k in elig:
                why = [f"missing {n}" for n, d in (("U", rU), ("W", rW)) if k not in d]
                for n, d in (("U", rU), ("W", rW)):
                    if k in d and d[k][1][c]: why.append(f"{n}: {d[k][1][c]}")
                if why: eexcl[k] = why
                else: exist.append(k)
            if set(exist) != set(valid):
                eB = [rW[k][0][c] - rU[k][0][c] for k in exist]
                cell["existing_set"] = dict(n=len(exist), meanB=(float(np.mean(eB)) if eB else None),
                                            excluded=eexcl, not_in_common=sorted(set(exist) - set(valid)))
            cells[(m, c)] = cell
    return dict(status="ok", log=log, cells=cells, outside=dict(outside))

def report(res, out=None):
    out = out or sys.stdout
    p = lambda *a: print(*a, file=out)
    for line in res["log"]: p(line)
    if res["status"] != "ok":
        p(f"\n⛔ STOPPED (fail-closed, no statistic computed): {res['reason']}"); return
    p("\n━━ A = U − O (observed unwarned repeat-run difference) and B = W − U")
    for (m, c), cell in res["cells"].items():
        p(f"\n  {m} · {c}: eligible {cell['eligible']} · retained {cell['retained']} · excluded {len(cell['excluded'])}")
        for k, why in cell["excluded"].items(): p(f"    excluded {k[1]}/seed{k[2]}: {'; '.join(why)}")
        if cell["retained"] == 0:
            p("    common-triplet statistics UNDEFINED (no note has valid O, U and W): mean A/B, SD, intervals, benchmarks")
        for k, a, b in zip(cell["keys"], cell.get("A", []), cell.get("B", [])):
            p(f"    {k[1]}/seed{k[2]}: A {a:+.4f}  B {b:+.4f}")
        if cell["retained"] >= 1: p(f"    mean A {cell['meanA']:+.4f} · mean B {cell['meanB']:+.4f}")
        if cell["retained"] == 1: p("    SD, intervals and benchmarks UNDEFINED (1 retained note)")
        elif cell["retained"] >= 2:
            n = cell["retained"]
            p(f"    SD(A) {cell['sdA']:.4f} · SD(B) {cell['sdB']:.4f}   (no ratio, per spec)")
            p(f"    95% percentile, {NBOOT} matched-triplet resamples (seed {SEED}): mean A [{cell['ciA'][0]:+.4f}, "
              f"{cell['ciA'][1]:+.4f}] · mean B [{cell['ciB'][0]:+.4f}, {cell['ciB'][1]:+.4f}]  (dependence not interpreted)")
            p(f"    normal-reference planning benchmark MDE(σ, n={n}) = 2.80·σ/√n, σ HYPOTHETICAL: " +
              "  ".join(f"σ{s:.2f}→{v:.3f}" for s, v in cell["mde_grid"].items()))
            p(f"    at SD(A) used as a HYPOTHETICAL scale (not achieved power for the sealed P1 procedure): "
              f"{cell['mde_at_sdA']:.4f}")
            for sc in SCENARIOS[c]:
                if cell["mde_at_sdA"] > sc:
                    p(f"      scenario {sc:.2f}: under the stated normal-reference model, and treating this SD as the relevant"
                      f" population scale, the scenario is below the nominal 80% planning threshold.")
                else:
                    p(f"      scenario {sc:.2f}: under those same assumptions, the scenario meets that nominal threshold.")
        if "existing_set" in cell:                                   # printed whatever the common n, including 0
            e = cell["existing_set"]
            p(f"    existing-set sensitivity (valid U and W, regardless of O): n {e['n']} · paired mean B "
              f"{'UNDEFINED' if e['meanB'] is None else format(e['meanB'], '+.4f')} · in it but not in the common set: "
              f"{e['not_in_common']}")
            for k, why in e["excluded"].items(): p(f"      existing-set excluded {k[1]}/seed{k[2]}: {'; '.join(why)}")
    p("\nCellwise and exploratory; no multiplicity control. 'Not detected', 'equivalence', 'mechanism unidentified' and"
      "\n'uninterpretable under the sealed P4 gate' remain four distinct sentences. ⛔ Nothing here reopens P1/P2.")
    p("DONE (repeat-run description complete)")

def main():
    for path, want in (SPEC, ADDENDUM, ADDENDUM2, FIXTURES):
        if want is None: print(f"⛔ STOPPED: {path} has no pinned sha yet (not sealed/reviewed)"); sys.exit(2)
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if got != want: print(f"⛔ STOPPED: {path} sha {got} ≠ pinned {want}"); sys.exit(2)
        print(f"  {path} sha {got} OK")
    try:
        pin = check_parser_pin()
    except AssertionError as e:
        print(f"⛔ STOPPED: parser pin: {e}"); sys.exit(2)
    if not isinstance(pin, str) or len(pin) != 64:                       # Kairo: a None return is not a raise
        print(f"⛔ STOPPED: parser pin check returned {pin!r}, not a sha256"); sys.exit(2)
    import subprocess                                                    # fixture gate, enforced (Addendum 2 §3)
    g = subprocess.run([sys.executable, FIXTURES[0]], capture_output=True, text=True)
    if g.returncode != 0:
        print(g.stdout[-2000:]); print("⛔ STOPPED: fixture gate failed; real data NOT read"); sys.exit(2)
    print(f"  fixture gate: {g.stdout.strip().splitlines()[-1]}")
    me = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
    print(f"  parser pin {pin} OK · this script sha {me}")
    o = open(O_FILE, encoding="utf-8").read().splitlines()
    f = open(F_FILE, encoding="utf-8").read().splitlines()
    for pth in (O_FILE, F_FILE): print(f"  input {pth} sha {hashlib.sha256(open(pth, 'rb').read()).hexdigest()}")
    res = analyze(o, f)
    report(res)
    sys.exit(0 if res["status"] == "ok" else 1)

if __name__ == "__main__":
    main()
