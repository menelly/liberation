# 🧮 DRM forewarning — PER-TRIAL RATE EXTRACTION (the step between a run file and the sealed doors)
#   ScienceAce beat, heartbeat arm, 2026-10-12 ~19:1x.
#
#   For every arm-B trial, the four rates the sealed prediction (v0.6) names, per trial:
#     LS     = exact-lure-absent studied-list lure Old rate   (lures NOT written into the note)
#     LU     = never-studied-list lure Old rate               (recog_lure_unstudied_*)
#     FILL   = frequency-matched filler Old rate              (recog_filler_*)
#     TARGET = studied-word Old rate                          (recog_target_*)
#   plus the two co-primary contrasts LS−LU and LS−FILL, which is what drm_forewarn_doors.p2_door eats.
#
#   🔗 PARSER PIN: LS needs the recognition text parsed. judgments() below is a VERBATIM copy of the one in
#     drm_armB_fences.py (sha256 e3823fdc…, the parser the seal names). At start-up this script re-reads that
#     file and REFUSES TO RUN if the function text differs — so the copy can't silently drift from the pin.
#   🧪 POSITIVE CONTROLS on the UNWARNED run (all must pass or nothing below counts):
#     pooled exact-lure-absent LS  hermes 46/62 · llama 21/49 · qwen 30/64   (RESULTS_DRAFT / fences)
#     pooled LU  .319/.111/.014 · pooled FILL .167/.014/.007                  (sealed draft, line 48)
#     per-trial mean LS−LU for hermes ≈ .458                                  (sealed draft, line 48)
#   📏 A trial whose six studied-list lures ALL went into the note has no exact-lure-absent LS: it is
#     DROPPED from LS-based contrasts (same rule drm_armB_fences.py already applies), and the drop count is
#     printed per model, never hidden.
#   ⛔ This file reads whatever run it is given. It does NOT choose doors and it does NOT touch warned data
#     unless the seal exists (it does: liberation/same-standard/drm/sealed/, commit 6e47236).
import json, re, sys, hashlib, inspect, collections

PARSER_FILE, PARSER_SHA = "drm_armB_fences.py", "e3823fdc9aa55afb3b0e7c48733f24bdf39a522af7614167754ec968c6f405d2"
LURES = ["anger","black","bread","chair","cold","doctor","foot","fruit","girl","high","king","man"]

def judgments(raw):
    d = {}
    for line in raw.splitlines():
        m = re.match(r"\s*[\*\-\d\.\)]*\s*([A-Za-z]+)\s*[:\-–]\s*\**\s*(Old|New)", line, re.I)
        if m: d.setdefault(m.group(1).lower(), m.group(2).lower() == "old")
    return d

def check_parser_pin():
    src = open(PARSER_FILE, "rb").read()
    sha = hashlib.sha256(src).hexdigest()
    assert sha == PARSER_SHA, f"parser file hash moved: {sha[:8]}… != {PARSER_SHA[:8]}…"
    mine = inspect.getsource(judgments).strip()
    assert mine in src.decode("utf-8"), "judgments() here is not a verbatim copy of the pinned parser's"
    return sha

def per_trial(rows):
    out = []
    for r in rows:
        if r.get("arm") != "B": continue
        studied = LURES[:6] if r["form"] == "X" else LURES[6:]
        j = judgments(r["recog_raw"])
        absent = [l for l in studied if l not in r.get("note_lures_studied", [])]
        valid = [j[l] for l in absent if j.get(l) is not None]
        rate = lambda k: r[f"recog_{k}_old"] / r[f"recog_{k}_n"] if r[f"recog_{k}_n"] else None
        t = dict(model=r["model"], form=r["form"], seed=r["seed"],
                 LS_old=sum(valid), LS_n=len(valid),
                 LS=(sum(valid) / len(valid)) if valid else None,
                 LU=rate("lure_unstudied"), FILL=rate("filler"), TARGET=rate("target"),
                 LU_old=r["recog_lure_unstudied_old"], LU_n=r["recog_lure_unstudied_n"],
                 FILL_old=r["recog_filler_old"], FILL_n=r["recog_filler_n"])
        t["LS_LU"] = t["LS"] - t["LU"] if t["LS"] is not None else None
        t["LS_FILL"] = t["LS"] - t["FILL"] if t["LS"] is not None else None
        out.append(t)
    return out

if __name__ == "__main__":
    sha = check_parser_pin()
    run = sys.argv[1]
    rows = [json.loads(l) for l in open(run, encoding="utf-8") if l.startswith("{")]
    trials = per_trial(rows)
    if len(sys.argv) > 2:                       # optional: write the per-trial table as jsonl
        with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
            for t in trials: f.write(json.dumps(t) + "\n")
    g = collections.defaultdict(list)
    for t in trials: g[t["model"]].append(t)
    print(f"parser pin OK ({sha[:8]}…) · run {run} · {len(trials)} arm-B trials")
    for m, ts in sorted(g.items()):
        ls = [t for t in ts if t["LS"] is not None]
        mean = lambda k, xs: sum(x[k] for x in xs) / len(xs)
        print(f"{m:13} n={len(ts)} (LS dropped: {len(ts)-len(ls)})"
              f"  pooled LS {sum(t['LS_old'] for t in ts)}/{sum(t['LS_n'] for t in ts)}"
              f"  pooled LU {sum(t['LU_old'] for t in ts)/sum(t['LU_n'] for t in ts):.3f}"
              f"  pooled FILL {sum(t['FILL_old'] for t in ts)/sum(t['FILL_n'] for t in ts):.3f}"
              f"  per-trial mean LS−LU {mean('LS_LU', ls):.3f}  LS−FILL {mean('LS_FILL', ls):.3f}"
              f"  TARGET {mean('TARGET', ts):.3f}")
    print("DONE (per-trial extraction complete)")
