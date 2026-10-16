"""Positive control for the fixtures (rewrite 3). Each mutation breaks ONE sealed policy in a throwaway copy, in a
dedicated temp directory restored/removed in `finally`. DETECTION IS THE GATE (Kairo, Nova): a mutation counts as
caught only if its NAMED fixture fails, or (where declared) the expected crash signature appears. Any mutation not
caught → exit 1. Scope: shows THESE breaks are caught; not a proof of every property (e.g. of the bootstrap).
History kept on purpose: the rewrite-2 harness's first run let 'A/B independent indices' through (constant A/B).
Run from liberation/same-standard/drm/."""
import subprocess, shutil, tempfile, os, sys
FILES = ["drm_repeat_run.py", "drm_repeat_run_fixtures.py", "drm_pertrial_rates.py", "drm_armB_fences.py"]
MUTS = {   # name: (anchor, replacement, fixture-name substring that must FAIL, or None, expected crash substring or None)
    "duplicates allowed": ("    if d:\n        raise Stop(f\"{name}: duplicate keys", "    if False:\n        raise Stop(f\"{name}: duplicate keys",
                           "duplicate U key", None),
    "own-digest check skipped": ('if sha_text(r["note"]) != r["note_sha256"]:', "if False:", "stale digest", None),
    "zero-LU placeholder removed": ('    if lu0: rr["recog_lure_unstudied_old"], rr["recog_lure_unstudied_n"] = 0, 1\n', "",
                                    None, "unsupported operand type"),
    "TARGET zero over-excluded": ("    lu0, fill0 = r[\"recog_lure_unstudied_n\"] == 0, r[\"recog_filler_n\"] == 0\n",
                                  "    lu0, fill0 = r[\"recog_lure_unstudied_n\"] == 0 or r[\"recog_target_n\"] == 0, r[\"recog_filler_n\"] == 0\n",
                                  "TARGET denominator 0", None),
    "recall used to exclude": ("                if why: excl[k] = why",
                               "                why += ['recall'] if (k in kU and 'recall_raw' not in kU[k]) else []\n                if why: excl[k] = why",
                               "missing recall", None),
    "A/B independent indices": ("mA, mB = A[idx].mean(1), B[idx].mean(1)",
                                "mA, mB = A[idx].mean(1), B[rng.integers(0, len(valid), size=idx.shape)].mean(1)",
                                "share ONE index array", None),
    "A/C rows made fatal": ('{"A", "B", "C"}, None, log, "O-file"', '{"B"}, None, log, "O-file"', "original A/C rows", None),
    "schema check removed": ('        validate_types(r, f"{name} line {i}")\n', "", "STOP malformed schema", None),
    "n=0 hides sensitivity": ('        if "existing_set" in cell:', '        if "existing_set" in cell and cell["retained"] > 0:',
                              "common n = 0 STILL prints", None),
    "missing temp read as equal": ('        if any(v == "MISSING" for v in vals.values()) or len(present) < 2: st = "missing/unavailable"',
                                   '        if len(present) < 0: st = "missing/unavailable"', "missing temperatures", None),
}
src_dir = os.getcwd()
undetected = []
for name, (a, b, fixture, crash) in MUTS.items():
    tmp = tempfile.mkdtemp(prefix="drm_mut_")
    try:
        for f in FILES: shutil.copy(os.path.join(src_dir, f), tmp)
        orig = open(os.path.join(tmp, "drm_repeat_run.py"), encoding="utf-8").read()
        assert a in orig, f"mutation anchor missing: {name}"
        open(os.path.join(tmp, "drm_repeat_run.py"), "w", encoding="utf-8").write(orig.replace(a, b, 1))
        p = subprocess.run([sys.executable, "drm_repeat_run_fixtures.py"], cwd=tmp, capture_output=True, text=True)
        fails = [l for l in p.stdout.splitlines() if l.startswith("FAIL")]
        caught_by_fixture = fixture is not None and any(fixture in l for l in fails)
        caught_by_crash = crash is not None and crash in p.stderr
        unrelated_crash = "Traceback" in p.stderr and not caught_by_crash
        ok = caught_by_fixture or caught_by_crash
        how = ("named fixture FAILED" if caught_by_fixture else "expected crash" if caught_by_crash else "NOT CAUGHT")
        print(f"{'CAUGHT ' if ok else 'MISSED '} {name:28} → {how}" + ("  (+ unrelated crash, reported)" if unrelated_crash else ""))
        if not ok: undetected.append(name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
assert open(os.path.join(src_dir, "drm_repeat_run.py"), encoding="utf-8").read(), "source unreadable"
print(f"\n{len(MUTS) - len(undetected)}/{len(MUTS)} mutations caught" + (f"  ⛔ MISSED: {undetected}" if undetected else ""))
sys.exit(1 if undetected else 0)
