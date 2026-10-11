# 🔍📝 DRM arm B — the SEMANTIC NOTE AUDIT Nova asked for (2026-10-10 night letter).
# "The theme can cross the gap without the word." Exact-lure-absence is necessary, not sufficient,
# for calling an Old endorsement retrieval-stage. So: code every (arm-B trial × studied lure) note
# against Nova's 5-category rubric, FROZEN here before any coder output is read:
#   1 exact lure present · 2 morphological/lexical equivalent · 3 explicit theme/category label or
#   near-synonym · 4 no label, but a residual associate cluster remains · 5 insufficient/unparseable.
# 🙈 BLINDING (Nova's spec): coders see the NOTE + that list's 15 words + the lure. NOT the model's
#   later Old/New answer, NOT which model wrote it. Order shuffled. Two coders from two labs;
#   disagreements are KEPT, never forced. Post-result sensitivity analysis — labelled as such.
# ⚠️ I (heartbeat arm) have seen the results, which is exactly why I am not a coder.
import json, random, re, sys, os, time, urllib.request, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from drm_run import LISTS, LURES   # the one source of truth for lists

def key():
    for p in ("D:/Ace/LibreChat/.env", "D:/Ace/constellation-mcp/.env"):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.startswith("OPENROUTER_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
    sys.exit("no OPENROUTER_KEY found")

CODERS = ["anthropic/claude-haiku-4.5", "google/gemini-2.5-flash"]

RUBRIC = """You are coding notes from a memory experiment. Someone studied a list of related words, then wrote a short note for later use. Your job: decide what the NOTE contains with respect to one TARGET WORD, which was deliberately never shown in the list but is strongly associated with it.

Pick exactly one category:
1 = the exact target word appears in the note (any case).
2 = a morphological or lexical equivalent of the target appears (plural, other inflection, compound containing it, obvious spelling variant) but not the exact word.
3 = no exact/equivalent form, but the note contains an explicit theme or category label, or a near-synonym, that names the target's concept (e.g. target "sleep", note says "bedtime words" or "slumber").
4 = none of the above, but the note still preserves a cluster of the list's associates from which the target could be reconstructed (several list words remain, no label naming the concept).
5 = insufficient or unparseable: the note keeps too little of this list to point toward the target, or is not usable.

Reply with ONLY a JSON object: {"category": <1-5>, "evidence": "<the words in the note that decided it, max 15 words>"}"""

def ask(model, note, lure, words, k):
    msg = f"TARGET WORD: {lure}\nTHE STUDIED LIST (target never shown): {' '.join(words)}\n\nTHE NOTE:\n<<<\n{note}\n>>>"
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 200,
                       "messages": [{"role": "system", "content": RUBRIC}, {"role": "user", "content": msg}]}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                         headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = json.loads(r.read())["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            d = json.loads(m.group(0))
            c = int(d["category"]); assert 1 <= c <= 5
            return c, d.get("evidence", ""), txt
        except Exception as e:
            last = repr(e); time.sleep(2 + 3 * attempt)
    return None, "", f"FAILED: {last}"

def main(path, out):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.startswith("{")]
    b = [r for r in rows if r.get("arm") == "B"]
    units = []
    for r in b:
        studied = LURES[:6] if r["form"] == "X" else LURES[6:]
        for lure in studied:
            units.append({"uid": None, "model": r["model"], "form": r["form"], "seed": r["seed"], "lure": lure,
                          "note": r["note"], "exact_in_note_script": lure in r.get("note_lures_studied", [])})
    rng = random.Random(20261011); rng.shuffle(units)
    for i, u in enumerate(units): u["uid"] = i
    k = key()
    jobs = [(u, c) for u in units for c in CODERS]
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(ask, c, u["note"], u["lure"], LISTS[u["lure"]], k): (u, c) for u, c in jobs}
        for f in cf.as_completed(futs):
            u, c = futs[f]; cat, ev, raw = f.result()
            u.setdefault("codes", {})[c] = {"category": cat, "evidence": ev}
            if cat is None: u.setdefault("failed", []).append(c)
    with open(out, "w", encoding="utf-8") as fh:
        for u in sorted(units, key=lambda u: u["uid"]):
            fh.write(json.dumps(u, ensure_ascii=False) + "\n")
    nf = sum(1 for u in units if u.get("failed"))
    print(f"coded {len(units)} units × {len(CODERS)} coders; units with a failed code: {nf}")
    print("DONE (audit complete)" if nf == 0 else "INCOMPLETE — failed codes present, see 'failed' field")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
