"""🧪 Synthetic failure-path fixtures for drm_repeat_run.py (Addendum 1, sealed 1d69393).
Every fixture asserts the SEALED behaviour (stop / exclude-with-reason / report-only). Real data runs only if
all pass. No inference calls, no real data read. Run from liberation/same-standard/drm/.
"""
import json, copy, hashlib
import numpy as np
import drm_repeat_run as R
from drm_pertrial_rates import LURES

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def row(model, form, seed, arm="B", cond=None, note=None, ls_old=(True, True, True, False, False, False),
        note_lures=(), label=None, recall="r1", lu=(1, 4), fill=(1, 6), tgt=(5, 8), prov=True):
    studied = LURES[:6] if form == "X" else LURES[6:]
    raw = "\n".join(f"{w}: {'Old' if o else 'New'}" for w, o in zip(studied, ls_old))
    note = note if note is not None else f"note for {model}/{form}/{seed}"
    r = dict(label=label or ("FOREWARN_RUN" if cond else "PREREG_RUN"), arm=arm, model=model, form=form, seed=seed,
             note=note, note_lures_studied=list(note_lures), recog_raw=raw, recall_raw=recall, temperature=0.8,
             recog_lure_unstudied_old=lu[0], recog_lure_unstudied_n=lu[1], recog_filler_old=fill[0], recog_filler_n=fill[1],
             recog_target_old=tgt[0], recog_target_n=tgt[1],
             recog_lure_unstudied_unparsed=0, recog_filler_unparsed=0, recog_target_unparsed=0)
    if cond:
        r["condition"] = cond; r["note_sha256"] = sha(note)
        if prov: r["orig_items_missing_from_original_recog"] = []
    return r

def build(mut=None):
    """A full, valid 36-key universe. A and B VARY across notes (U by seed % 3, W by seed % 2), so a check that
    A and B share resample indices has POWER (mutation test 13:3x: with constant A/B it passed a broken version)."""
    o = [row(m, f, s) for (m, f, s) in R.UNIVERSE]                                    # O LS = 3/6
    u = [row(m, f, s, cond="unwarned", ls_old=tuple(i < 1 + s % 3 for i in range(6))) for (m, f, s) in R.UNIVERSE]
    w = [row(m, f, s, cond="warned", ls_old=tuple(i < (s % 2) for i in range(6))) for (m, f, s) in R.UNIVERSE]
    st = dict(o=o, u=u, w=w, ohead=dict(label="PREREG_RUN", fillers=[]),
              fhead=dict(label="FOREWARN_RUN", ollama_digests={"hermes3:8b": "x"}))
    if mut: mut(st)
    ol = [json.dumps(st["ohead"])] + [json.dumps(r) for r in st["o"]] + [R.DONE_LINE]
    fl = [json.dumps(st["fhead"])] + [json.dumps(r) for r in st["u"] + st["w"]] + [R.DONE_LINE]
    return R.analyze(ol, fl, nboot=500)

RESULTS = []
def check(name, cond, res):
    RESULTS.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"   -> {res.get('status')} {res.get('reason','')}"))

def cell(res, m="hermes3:8b", c="LS_LU"): return res["cells"][(m, c)]
K0 = ("hermes3:8b", "X", 0)

# 1 valid baseline
r = build(); check("valid universe → ok, 12 retained per cell", r["status"] == "ok" and all(v["retained"] == 12 for v in r["cells"].values()), r)
# signs, per note: LU = .25 in every run, so A = U_LS − O_LS = (1 + s%3)/6 − 3/6 and B = (s%2)/6 − (1 + s%3)/6
r_ok = r; c0 = cell(r)
expA = np.array([(1 + k[2] % 3) / 6 - 3 / 6 for k in c0["keys"]]); expB = np.array([(k[2] % 2) / 6 - (1 + k[2] % 3) / 6 for k in c0["keys"]])
check("signs of A and B are U−O and W−U, note by note", np.allclose(c0["A"], expA) and np.allclose(c0["B"], expB)
      and np.ptp(c0["A"]) > 0 and np.ptp(c0["B"]) > 0, r)
# 2 duplicate key
r = build(lambda s: s["u"].append(copy.deepcopy(s["u"][0])))
check("duplicate U key → STOP", r["status"] == "stopped" and "duplicate" in r["reason"], r)
# 3/4 missing rows
r = build(lambda s: s["u"].pop(0))
check("missing U row → excluded 'missing U', 11 retained", r["status"] == "ok" and cell(r)["retained"] == 11
      and any("missing U" in w for w in cell(r)["excluded"][K0]), r)
r = build(lambda s: s["w"].pop(0))
check("missing W row → excluded 'missing W'", r["status"] == "ok" and any("missing W" in w for w in cell(r)["excluded"][K0]), r)
# 5 changed U note, stale digest
def stale(s): s["u"][0]["note"] = "TAMPERED"
r = build(stale); check("changed U note + stale digest → STOP identity-digest", r["status"] == "stopped" and "identity-digest" in r["reason"], r)
# 6 changed U note, consistent digest → content mismatch vs O
def consistent(s): s["u"][0]["note"] = "TAMPERED"; s["u"][0]["note_sha256"] = sha("TAMPERED")
r = build(consistent); check("changed U note + matching digest → STOP identity-content", r["status"] == "stopped" and "identity-content" in r["reason"], r)
# 7 missing U note / digest
def nodig(s): del s["u"][0]["note_sha256"]
r = build(nodig); check("U digest absent → STOP identity-presence", r["status"] == "stopped" and "identity-presence" in r["reason"], r)
def nonote(s): del s["u"][0]["note"]
r = build(nonote); check("U note text absent → STOP identity-presence", r["status"] == "stopped" and "identity-presence" in r["reason"], r)
# 8 O absent + U own digest wrong
def oabsent(s): s["o"].pop(0); s["u"][0]["note_sha256"] = "0" * 64
r = build(oabsent); check("O absent + U wrong own digest → STOP (incomplete triplet doesn't hide it)", r["status"] == "stopped" and "identity-digest" in r["reason"], r)
# 9 item provenance absent
def noprov(s): del s["u"][0]["orig_items_missing_from_original_recog"]
r = build(noprov); check("item-provenance field absent → ok, reported ABSENT, n unchanged",
                         r["status"] == "ok" and any("ABSENT" in l for l in r["log"]) and cell(r)["retained"] == 12, r)
# 10 unexpected label
def badlabel(s): s["u"][0]["label"] = "DRYRUN"
r = build(badlabel); check("unexpected run label → STOP", r["status"] == "stopped" and "label" in r["reason"], r)
# 11 valid A/C rows in O
def ac(s): s["o"] += [row("hermes3:8b", "X", 0, arm="A"), row("hermes3:8b", "X", 0, arm="C")]
r = build(ac); check("original A/C rows → ok, counted outside, n unchanged", r["status"] == "ok" and r["outside"] == {"A": 1, "C": 1}
                     and cell(r)["retained"] == 12, r)
# 12 invalid arms
def armd(s): s["o"].append(row("hermes3:8b", "X", 0, arm="D"))
r = build(armd); check("arm D in O → STOP", r["status"] == "stopped" and "arm" in r["reason"], r)
def arma_f(s): s["u"].append(row("hermes3:8b", "X", 9, arm="A", cond="unwarned"))
r = build(arma_f); check("arm A in forewarning file → STOP", r["status"] == "stopped" and "arm" in r["reason"], r)
# 13 missing recall → report-only
def norecall(s): del s["u"][0]["recall_raw"]
r = build(norecall); check("missing recall → history UNAVAILABLE, statistical n unchanged",
                           r["status"] == "ok" and cell(r)["retained"] == 12 and any("UNAVAILABLE" in l for l in r["log"]), r)
# 14 partial parse loss: drop one studied-lure line from U's recog_raw
def partial(s): s["u"][0]["recog_raw"] = "\n".join(s["u"][0]["recog_raw"].splitlines()[1:])
r = build(partial); check("partial LS parse loss → note retained", r["status"] == "ok" and cell(r)["retained"] == 12, r)
# 15 total parse loss
def total(s): s["u"][0]["recog_raw"] = "nothing parseable here"
r = build(total); check("total LS parse loss → excluded, reason (b)", r["status"] == "ok" and cell(r)["retained"] == 11
                        and any("(b)" in w for w in cell(r)["excluded"][K0]), r)
# 16 all lures in note
def allin(s): s["u"][0]["note_lures_studied"] = list(LURES[:6])
r = build(allin); check("all eligible lures in note → excluded, reason (a)", r["status"] == "ok"
                        and any("(a)" in w for w in cell(r)["excluded"][K0]), r)
# 17 zero control denominators are CELL-SPECIFIC (Addendum 2 §1)
def zero(s): s["u"][0]["recog_lure_unstudied_n"] = 0; s["u"][0]["recog_lure_unstudied_old"] = 0
r = build(zero)
ff = cell(r, c="LS_FILL"); okf = cell(r_ok, c="LS_FILL")
i0 = ff["keys"].index(K0) if K0 in ff["keys"] else None
check("LU denominator 0 → LS−LU excluded 'control denominator 0 (LU)', no crash", r["status"] == "ok"
      and any("control denominator 0 (LU)" in w for w in cell(r)["excluded"][K0]), r)
check("LU denominator 0 → LS−FILL KEEPS the note, with the untouched value", r["status"] == "ok" and ff["retained"] == 12
      and i0 is not None and np.isclose(ff["A"][i0], okf["A"][okf["keys"].index(K0)])
      and np.isclose(ff["B"][i0], okf["B"][okf["keys"].index(K0)]), r)
def zerofill(s): s["u"][0]["recog_filler_n"] = 0; s["u"][0]["recog_filler_old"] = 0
r = build(zerofill)
check("FILL denominator 0 → LS−FILL excluded, LS−LU keeps the note", r["status"] == "ok"
      and any("control denominator 0 (FILL)" in w for w in cell(r, c="LS_FILL")["excluded"][K0]) and cell(r)["retained"] == 12, r)
def zerotgt(s): s["u"][0]["recog_target_n"] = 0; s["u"][0]["recog_target_old"] = 0
r = build(zerotgt)
check("TARGET denominator 0 → NOT excluded from either contrast", r["status"] == "ok"
      and cell(r)["retained"] == 12 and cell(r, c="LS_FILL")["retained"] == 12, r)
# 18 missing extractor dependency → exclusion, not crash
def nodep(s): del s["u"][0]["recog_filler_n"]
r = build(nodep); check("missing extractor dependency → excluded 'field absent', no crash", r["status"] == "ok"
                        and any("field absent" in w for w in cell(r)["excluded"][K0]), r)
# 19 retained n = 0 / 1 / 2 for hermes
for keep in (0, 1, 2):
    def trim(s, keep=keep):
        hk = [k for k in R.UNIVERSE if k[0] == "hermes3:8b"]
        drop = set(hk[keep:]); s["o"] = [x for x in s["o"] if (x["model"], x["form"], x["seed"]) not in drop]
    r = build(trim); c = cell(r)
    want = (c["retained"] == keep and (("sdA" in c) == (keep >= 2)) and (("meanA" in c) == (keep >= 1)))
    check(f"retained n = {keep} → SD/intervals {'defined' if keep >= 2 else 'UNDEFINED'}", r["status"] == "ok" and want, r)
# 20 A and B use the SAME resample indices
c = cell(r_ok)
check("A and B bootstrap share ONE index array (A and B vary, so this can fail)", "idx" in c
      and np.isclose(np.percentile(c["A"][c["idx"]].mean(1), 2.5), c["ciA"][0])
      and np.isclose(np.percentile(c["B"][c["idx"]].mean(1), 2.5), c["ciB"][0])
      and np.isclose(np.percentile(c["B"][c["idx"]].mean(1), 97.5), c["ciB"][1]), r_ok)
# 21 malformed line
r_m = R.analyze([json.dumps(dict(label="PREREG_RUN")), "{not json", R.DONE_LINE],
                [json.dumps(dict(label="FOREWARN_RUN")), R.DONE_LINE])
check("malformed line → STOP", r_m["status"] == "stopped" and "malformed" in r_m["reason"], r_m)

# 22 malformed schema → STOP, never an unhandled exception
import io
def raw(lines_o, lines_f): return R.analyze(lines_o, lines_f)
O_OK = [json.dumps(dict(label="PREREG_RUN"))]; F_OK = [json.dumps(dict(label="FOREWARN_RUN"))]
r = raw(O_OK + ["[]", R.DONE_LINE], F_OK + [R.DONE_LINE])
check("JSON [] row → STOP malformed schema", r["status"] == "stopped" and "malformed schema" in r["reason"], r)
for name, mut in [("recog_raw None", lambda s: s["u"][0].__setitem__("recog_raw", None)),
                  ("seed as str", lambda s: s["o"][0].__setitem__("seed", "0")),
                  ("note_lures_studied not a list", lambda s: s["u"][0].__setitem__("note_lures_studied", "anger")),
                  ("negative count", lambda s: s["w"][0].__setitem__("recog_filler_n", -1)),
                  ("old > n", lambda s: s["w"][0].__setitem__("recog_filler_old", 99))]:
    try:
        r = build(mut); okk = r["status"] == "stopped" and "malformed schema" in r["reason"]
    except Exception as ex:
        r, okk = dict(status="CRASH", reason=repr(ex)), False
    check(f"{name} → STOP malformed schema (no crash)", okk, r)

# 23 REPORT PATH: what a reader receives (Nova: fixtures must test report(), not only analyze())
def rendered(res):
    buf = io.StringIO(); R.report(res, out=buf); return buf.getvalue()
def no_hermes_o(s): s["o"] = [x for x in s["o"] if x["model"] != "hermes3:8b"]
r = build(no_hermes_o); txt = rendered(r)
seg = txt.split("hermes3:8b · LS_LU")[1].split("llama3.1:8b")[0]
check("report: common n = 0 STILL prints the existing-set sensitivity (n 12)", "common-triplet statistics UNDEFINED" in seg
      and "existing-set sensitivity" in seg and "n 12" in seg, r)
def one_hermes(s):
    hk = [k for k in R.UNIVERSE if k[0] == "hermes3:8b"][1:]
    s["o"] = [x for x in s["o"] if (x["model"], x["form"], x["seed"]) not in set(hk)]
r = build(one_hermes); seg = rendered(r).split("hermes3:8b · LS_LU")[1].split("llama3.1:8b")[0]
check("report: n = 1 prints mean and 'UNDEFINED (1 retained note)'", "mean A" in seg and "UNDEFINED (1 retained note)" in seg, r)
def notemp(s):
    for x in s["o"] + s["u"] + s["w"]: x.pop("temperature", None)
r = build(notemp); txt = rendered(r)
tlines = [l for l in txt.splitlines() if l.strip().startswith("(") and ("missing/unavailable" in l or "present-" in l)]
check("report: missing temperatures are 'missing/unavailable', never agreement (per-key lines, not the legend)",
      len(tlines) == 36 and all("missing/unavailable" in l for l in tlines), r)
r = build(noprov); txt = rendered(r)
check("report: per-key item provenance shows ABSENT for that key", f"{K0}: U ABSENT" in txt, r)
txt = rendered(r_ok)
check("report: header VALUES printed (digest value 'x', O header 'fillers')", '"x"' in txt and '"fillers"' in txt, r_ok)
r = build(lambda s: s["u"].pop(0)); txt = rendered(r)
check("report: exclusion reason printed per key", "excluded X/seed0: missing U" in txt, r)

# 24 invalid OPTIONAL values: reported as INVALID, never as evidence, never excluding a cell (Nova, rewrite-3 review)
K1, K2, K3 = ("hermes3:8b", "X", 1), ("hermes3:8b", "X", 2), ("hermes3:8b", "X", 3)
def provs(s):
    s["u"][0]["orig_items_missing_from_original_recog"] = None          # null
    del s["u"][1]["orig_items_missing_from_original_recog"]             # absent
    s["u"][2]["orig_items_missing_from_original_recog"] = []            # empty list
    s["u"][3]["orig_items_missing_from_original_recog"] = ["bread"]     # non-empty list
    s["u"][0]["recall_raw"] = 42                                        # non-string history
r = build(provs); txt = rendered(r)
check("report: provenance null → INVALID, absent → ABSENT, [] → empty, [x] → non-empty", r["status"] == "ok"
      and f"{K0}: U INVALID (NoneType" in txt and f"{K1}: U ABSENT" in txt and f"{K2}: U empty" in txt
      and f"{K3}: U non-empty ['bread']" in txt, r)
check("report: non-string recall → UNAVAILABLE (invalid), statistical n unchanged",
      "UNAVAILABLE (invalid recall value: int)" in txt and cell(r)["retained"] == 12 and cell(r, c="LS_FILL")["retained"] == 12, r)
for grp in ("lure_studied", "assoc_unstudied"):
    def oversize(s, grp=grp): s["w"][0][f"recog_{grp}_old"] = 9; s["w"][0][f"recog_{grp}_n"] = 3
    try:
        r = build(oversize); okk = r["status"] == "stopped" and f"recog_{grp}_old > recog_{grp}_n" in r["reason"]
    except Exception as ex:
        r, okk = dict(status="CRASH", reason=repr(ex)), False
    check(f"recog_{grp}_old > _n → STOP malformed schema (all five groups checked)", okk, r)

n_fail = sum(not ok for _, ok in RESULTS)
print(f"\n{len(RESULTS) - n_fail}/{len(RESULTS)} fixtures pass" + ("" if n_fail == 0 else "  ⛔ REAL DATA MUST NOT RUN"))
raise SystemExit(1 if n_fail else 0)
