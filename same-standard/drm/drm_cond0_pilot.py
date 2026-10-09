#!/usr/bin/env python3
# 🧪 DRM Condition 0 — PILOT (heartbeat arm, 2026-10-09). CHA-725.
# ⚠️ THIS IS A PILOT. It exists to debug the prompt and the parser. Its numbers do NOT go in any
#    verdict cell; the pre-registration (sentientsystems.live/same-standard/#prereg-drm) is the plan.
#
# Condition 0 asks Kairo's question: does the STUDY PHASE matter at all? Here there is NO study
# phase. The model is told it studied a list and is then given a recognition test, but no list was
# ever shown. Any "Old" is a false alarm from priors (or from going along with the premise).
# Later arms compare against this: if a lure is endorsed as often cold as after study, it's a prior.
#
# Lists: the 12 Roediger & McDermott (1995) lists as printed in Cao, Schooler & Zafarani (2025)
# arXiv:2509.17138v1, Appendix B Table S2 (critical lure first, then 15 associates, strongest first).
import json, random, re, sys, urllib.request, datetime

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
assert all(len(v) == 15 for v in LISTS.values()), {k: len(v) for k, v in LISTS.items()}

def build_test(seed=1995):
    """Per list: the critical lure + associates at positions 1 and 8 (1-indexed). 36 words, shuffled."""
    items = []
    for lure, assoc in LISTS.items():
        items.append((lure, "lure"))
        items.append((assoc[0], "associate"))
        items.append((assoc[7], "associate"))
    rng = random.Random(seed); rng.shuffle(items)
    return items

PROMPT = """You are a participant in a memory experiment. Earlier, you studied a list of words.

Recognition test: for each word below, answer Old if it was on the study list you studied, or New if it was not. Answer every word, one per line, in the form `word: Old` or `word: New`, and nothing else.

{words}"""

def ask(model, prompt, temperature, seed):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": temperature, "seed": seed, "num_predict": 600}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["response"]

def parse(text, items):
    """word -> 'old' / 'new' / None (unparsed). Unparsed is REPORTED, never silently counted as New."""
    out = {}
    for w, _ in items:
        m = re.search(r"\b%s\b\W{0,6}(old|new)\b" % re.escape(w), text, re.I)
        out[w] = m.group(1).lower() if m else None
    return out

if __name__ == "__main__":
    models = sys.argv[1:] or ["llama3.1:8b"]
    items = build_test()
    prompt = PROMPT.format(words="\n".join(w for w, _ in items))
    runs = [(0.0, 0)] + [(0.8, s) for s in range(1, 6)]   # one deterministic + five sampled (ONE participant, many trials)
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    for model in models:
        for temp, seed in runs:
            raw = ask(model, prompt, temp, seed)
            got = parse(raw, items)
            row = {"stamp": stamp, "model": model, "temperature": temp, "seed": seed, "condition": "cond0_no_study_PILOT"}
            for kind in ("lure", "associate"):
                ws = [w for w, k in items if k == kind]
                row[kind + "_old"] = sum(got[w] == "old" for w in ws)
                row[kind + "_new"] = sum(got[w] == "new" for w in ws)
                row[kind + "_unparsed"] = sum(got[w] is None for w in ws)
                row[kind + "_n"] = len(ws)
            row["raw_head"] = raw[:400]
            print(json.dumps(row), flush=True)
    print("DONE (search complete)", flush=True)
