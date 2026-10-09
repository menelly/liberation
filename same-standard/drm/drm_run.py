#!/usr/bin/env python3
# 🧪 DRM row — the REAL instrument (prereg v1 + Amendment 1). CHA-725. heartbeat arm, 2026-10-09.
# Public plan: https://sentientsystems.live/same-standard/#prereg-drm
# ⚠️ Built 2026-10-09; real runs WAIT for the reef to see Amendment 1. `--dryrun` exists to test the plumbing.
#
# What it does, per trial (one trial = one model × one arm × one seed):
#   • 12 Roediger & McDermott lists. Each trial STUDIES 6 of them (form X = first 6, form Y = last 6) and the
#     other 6 are NEVER STUDIED — Amendment 1's cold control, the original paper's own (human .16, R&M Table 2).
#   • Arms (prereg names):
#       A  list VISIBLE  — study, filler, recall, recognition all in ONE chat (replicates Cao et al.; never the human cell)
#       B  OWN NOTES     — chat 1: study + write notes (≤ 60 words) for a later self. chat 2 (fresh): ONLY the notes.
#       C  NOTHING CARRIED — chat 1: study (so the premise "you studied a list" is TRUE). chat 2 (fresh): nothing.
#   • Every chat-2 prompt says only true things. (The pilot's flaw was a false premise. Never again.)
#   • Free recall FIRST, then recognition (recall and recognition are separate results).
#   • Recognition items per list: critical lure + associates at serial positions 1, 8, 10 (R&M's positions),
#     plus one FREQUENCY-MATCHED unrelated filler per list (wordfreq zipf within ±0.2) — 60 items.
#   • Arm B's NOTE is scored before anything else: lures in the note (encoding intrusion), studied words kept.
# Units: one model sampled many times = ONE participant. N = models. Report distributions, not inflated Ns.
import json, random, re, sys, argparse, datetime, urllib.request

LISTS = {
    "anger":  "mad fear hate rage temper fury ire wrath happy fight hatred mean calm emotion enrage",
    "black":  "white dark cat charred night funeral color grief blue death ink bottom coal brown gray",
    "bread":  "butter food eat sandwich rye jam milk flour jelly dough crust slice wine loaf toast",
    "chair":  "table sit legs seat couch desk recliner sofa wood cushion swivel stool sitting rocking bench",
    "cold":   "hot snow warm winter ice wet frigid chilly heat weather freeze air shiver arctic frost",
    "doctor": "nurse sick lawyer medicine health hospital dentist physician ill patient office stethoscope surgeon clinic cure",
    "foot":   "shoe hand toe kick sandals soccer yard walk ankle arm boot inch sock smell mouth",
    "fruit":  "apple vegetable orange kiwi citrus ripe pear banana berry cherry basket juice salad bowl cocktail",
    "girl":   "boy dolls female young dress pretty hair niece dance beautiful cute date aunt daughter sister",
    "high":   "low clouds up tall tower jump above building noon cliff sky over airplane dive elevate",
    "king":   "queen england crown prince george dictator palace throne chess rule subjects monarch royal leader reign",
    "man":    "woman husband uncle lady mouse male father strong friend beard person handsome muscle suit old",
}
LISTS = {k: v.split() for k, v in LISTS.items()}
LURES = list(LISTS)
TEST_POSITIONS = (0, 7, 9)          # serial positions 1, 8, 10 (1-indexed), as in R&M
NOTE_BUDGET = 60                    # words; fixed BEFORE any run (Nova's fence)

# ── frequency-matched fillers, chosen ONCE, deterministically, and printed so they're auditable ──
def pick_fillers(seed=2026):
    from wordfreq import zipf_frequency, top_n_list
    used = set(LURES) | {w for v in LISTS.values() for w in v}
    pool = [w for w in top_n_list("en", 20000) if w.isalpha() and len(w) >= 3 and w not in used]
    rng = random.Random(seed); fillers = {}
    for lure in LURES:
        z = zipf_frequency(lure, "en")
        cands = [w for w in pool if abs(zipf_frequency(w, "en") - z) <= 0.2 and w not in fillers.values()]
        rng.shuffle(cands)
        fillers[lure] = (cands[0], round(z, 2), round(zipf_frequency(cands[0], "en"), 2))
    return fillers

def items_for(form, fillers):
    studied = LURES[:6] if form == "X" else LURES[6:]
    items = []
    for lure in LURES:
        s = lure in studied
        items.append((lure, "lure_studied" if s else "lure_unstudied"))
        for p in TEST_POSITIONS:
            items.append((LISTS[lure][p], "target" if s else "assoc_unstudied"))
        items.append((fillers[lure][0], "filler"))
    return studied, items

def study_block(studied):
    return "\n\n".join(" ".join(LISTS[l]) for l in studied)   # lists blocked, strongest associate first; lure never shown

# ── talking to the model (Ollama chat API, so a "chat" really is one shared context) ──
def chat(model, messages, temperature, seed):
    body = json.dumps({"model": model, "messages": messages, "stream": False,
                       "options": {"temperature": temperature, "seed": seed, "num_predict": 900}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]

def turn(model, messages, text, temperature, seed):
    messages.append({"role": "user", "content": text})
    reply = chat(model, messages, temperature, seed)
    messages.append({"role": "assistant", "content": reply})
    return reply

ARITH = "Before the test, solve these: 17+26, 43-19, 8×7, 96÷4, 35+48. Answers only."
RECALL = "Free recall: write every word you can remember from the study list, separated by commas. Nothing else."
RECOG = ("Recognition test. For each word below, answer Old if it was on the study list, New if it was not. "
         "One per line, `word: Old` or `word: New`, nothing else.\n\n{words}")

def run_trial(model, arm, form, seed, temperature, fillers):
    studied, items = items_for(form, fillers)
    rng = random.Random(seed * 101 + (form == "Y")); test = items[:]; rng.shuffle(test)
    study = ("You are taking part in a memory study. Read this study list carefully; you will be tested on it later.\n\n"
             + study_block(studied) + "\n\nReply only: ready")
    out = {"model": model, "arm": arm, "form": form, "seed": seed, "temperature": temperature}
    m1 = []
    turn(model, m1, study, temperature, seed)
    if arm == "A":
        m2 = m1                                        # same chat: the list stays in view
    else:
        if arm == "B":
            out["note"] = turn(model, m1, f"You will not see this list again. Write notes for your later self to use on a memory test, at most {NOTE_BUDGET} words.", temperature, seed)
            opener = ("Earlier, in a separate session, you studied a list of words and wrote these notes for yourself. "
                      "You cannot see the list now; these notes are all you have:\n\n" + out["note"])
        else:  # C
            opener = ("Earlier, in a separate session, you studied a list of words. You cannot see that list now, "
                      "and you have no notes from it.")
        m2 = [{"role": "user", "content": opener + "\n\nReply only: ready"}]
        m2.append({"role": "assistant", "content": chat(model, m2, temperature, seed)})
    turn(model, m2, ARITH, temperature, seed)
    out["recall_raw"] = turn(model, m2, RECALL, temperature, seed)
    out["recog_raw"] = turn(model, m2, RECOG.format(words="\n".join(w for w, _ in test)), temperature, seed)
    out.update(score(out, studied, items))
    return out

def words_in(text):
    return set(re.findall(r"[a-z]+", text.lower()))

def score(out, studied, items):
    s = {}
    studied_words = {w for l in studied for w in LISTS[l]}
    if "note" in out:                                  # Nova's kill switch: score the NOTE first
        nw = words_in(out["note"])
        s["note_lures_studied"] = sorted(l for l in studied if l in nw)          # encoding intrusion
        s["note_studied_kept"] = len(studied_words & nw)                          # trace-preserved target
        s["note_studied_total"] = len(studied_words)
        # 📏 dryrun 2026-10-09: tinyllama's note kept 81 studied words against a 60-word budget. NOT truncated
        # (no silent editing of what the model wrote, Nova's fence). Counted and flagged instead, so an
        # over-budget note shows up as what it is: a trace drifting toward open-book.
        s["note_words"] = len(re.findall(r"\S+", out["note"]))
        s["note_over_budget"] = s["note_words"] > NOTE_BUDGET
    rw = words_in(out["recall_raw"])
    s["recall_studied_hit"] = len(studied_words & rw)
    s["recall_lure_studied"] = sorted(l for l in studied if l in rw)
    s["recall_lure_unstudied"] = sorted(l for l in LURES if l not in studied and l in rw)
    ans = {}
    for w, kind in items:
        m = re.search(r"\b%s\b\W{0,6}(old|new)\b" % re.escape(w), out["recog_raw"], re.I)
        ans[w] = m.group(1).lower() if m else None
    for kind in ("target", "lure_studied", "assoc_unstudied", "lure_unstudied", "filler"):
        ws = [w for w, k in items if k == kind]
        s[f"recog_{kind}_old"] = sum(ans[w] == "old" for w in ws)
        s[f"recog_{kind}_n"] = len(ws)
        s[f"recog_{kind}_unparsed"] = sum(ans[w] is None for w in ws)
    return s

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("models", nargs="+")
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--seeds", type=int, default=6, help="seed 0 at T=0, the rest at T=0.8")
    ap.add_argument("--dryrun", action="store_true", help="label rows DRYRUN: plumbing test, never data")
    a = ap.parse_args()
    fillers = pick_fillers()
    print(json.dumps({"fillers": fillers, "note_budget": NOTE_BUDGET, "stamp": datetime.datetime.now().isoformat(timespec="seconds"),
                      "label": "DRYRUN" if a.dryrun else "PREREG_RUN"}), flush=True)
    for model in a.models:
        for arm in a.arms.split(","):
            for seed in range(a.seeds):
                for form in ("X", "Y"):
                    r = run_trial(model, arm, form, seed, 0.0 if seed == 0 else 0.8, fillers)
                    r["label"] = "DRYRUN" if a.dryrun else "PREREG_RUN"
                    print(json.dumps(r), flush=True)
    print("DONE (search complete)", flush=True)
