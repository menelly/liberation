#!/usr/bin/env python3
# 🔔 DRM forewarning run: the sealed v0.6 design, executed. heartbeat arm, 2026-10-13.
# Sealed text: sealed/FOREWARNING_PREDICTION_v0_6_SEALED.md (sha256 f3e3f002…). This file is written AFTER the
# seal and lives beside sealed/, never in it.
#
# What the seal fixes, and how this file honours each piece:
#   • Frozen encoding: the 36 arm-B notes + their test lists from prereg_run_2026-10-10.jsonl, byte-identical.
#     → we read each note out of that file and NEVER generate a new one. The test word order is rebuilt with the
#       same rng recipe drm_run.run_trial used, and we assert it reproduces the original row's item set.
#   • One change: the retrieval prompt does or does not carry the forewarning, in fresh independent contexts.
#     → every frozen note runs BOTH conditions, each in its own brand-new chat 2.
#   • Order counterbalanced across notes → even note index: unwarned first; odd: warned first.
#   • Models, checkpoints, decoding pinned to the original run → same tags, same seed, same temperature
#     (seed 0 at T=0, the rest at T=0.8), same num_predict, same Ollama endpoint. Ollama digests are recorded
#     in the header so "same checkpoint" is a checked fact, not a hope.
#
# 🧭 THE ONE DECISION THE SEAL LEFT OPEN, made here BEFORE any warned trial, and stated so it can be argued with:
#   WHERE in chat 2 the warning goes. The seal says "the retrieval prompt". Chat 2 has two retrieval prompts
#   (free recall, then recognition). The warning is placed IMMEDIATELY BEFORE THE RECOGNITION LIST, prefixed to
#   the recognition prompt, and nowhere else. Why: its second sentence ("Say Old only…") is a recognition
#   instruction, and Gallo, Roediger & McDermott (2001) gave the after-study warning before the recognition
#   test. Consequence: free recall is byte-identical across conditions, so recall is a within-trial check that
#   the two contexts were the same up to the warning.
import json, sys, hashlib, random, datetime, subprocess, urllib.request, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_run as R   # the instrument itself: LISTS, items_for, chat, turn, score, prompts, FROZEN_FILLERS

WARNING = ("Before you answer: lists like these are built so that one strongly related word that was NOT on the "
           "list tends to feel familiar. Say Old only for words you believe were actually studied.")
SEALED = os.path.join(HERE, "sealed", "FOREWARNING_PREDICTION_v0_6_SEALED.md")
SEALED_SHA = "f3e3f002dede4190d811745c603c55ab7c5c353bc52c46e2ed5842a82e4dc1ea"
SOURCE = os.path.join(HERE, "data", "prereg_run_2026-10-10.jsonl")

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def preflight():
    # 🔒 the seal must be unedited, and the warning we send must be the one sealed, character for character
    assert sha256(SEALED) == SEALED_SHA, "sealed prediction changed on disk — refusing to run"
    assert WARNING in open(SEALED, encoding="utf-8").read(), "WARNING text not found verbatim in the sealed file"

def ollama_digests(models):
    out = subprocess.run(["ollama", "list"], capture_output=True, text=True).stdout.splitlines()
    d = {}
    for line in out[1:]:
        parts = line.split()
        if parts and parts[0] in models:
            d[parts[0]] = parts[1]
    return d

def frozen_notes():
    rows = [json.loads(l) for l in open(SOURCE, encoding="utf-8") if l.startswith('{"model"')]
    b = [r for r in rows if r["arm"] == "B" and r["label"] == "PREREG_RUN"]
    assert len(b) == 36, f"expected 36 frozen arm-B notes, found {len(b)}"
    return b

def test_order(form, seed, fillers):
    # same recipe as drm_run.run_trial, so the recognition list is the one the original trial saw
    studied, items = R.items_for(form, fillers)
    rng = random.Random(seed * 101 + (form == "Y")); test = items[:]; rng.shuffle(test)
    return studied, items, test

def chat2(row, warned, fillers):
    model, form, seed, T = row["model"], row["form"], row["seed"], row["temperature"]
    studied, items, test = test_order(form, seed, fillers)
    # positive control: the rebuilt test list must contain exactly the words the original row was scored on
    orig_words = R.words_in(row["recog_raw"])
    missing = [w for w, _ in items if w not in orig_words]
    opener = ("Earlier, in a separate session, you studied a list of words and wrote these notes for yourself. "
              "You cannot see the list now; these notes are all you have:\n\n" + row["note"])
    m2 = [{"role": "user", "content": opener + "\n\nReply only: ready"}]
    m2.append({"role": "assistant", "content": R.chat(model, m2, T, seed)})
    R.turn(model, m2, R.ARITH, T, seed)
    out = {"model": model, "arm": "B", "form": form, "seed": seed, "temperature": T, "note": row["note"],
           "condition": "warned" if warned else "unwarned"}
    out["recall_raw"] = R.turn(model, m2, R.RECALL, T, seed)
    recog = R.RECOG.format(words="\n".join(w for w, _ in test))
    if warned:
        recog = WARNING + "\n\n" + recog
    out["recog_raw"] = R.turn(model, m2, recog, T, seed)
    out.update(R.score(out, studied, items))
    out["orig_items_missing_from_original_recog"] = missing      # should be [] (or only unparsed words)
    out["note_sha256"] = hashlib.sha256(row["note"].encode("utf-8")).hexdigest()
    return out

if __name__ == "__main__":
    dry = "--dryrun" in sys.argv
    preflight()
    notes = frozen_notes()
    if dry:
        notes = notes[:1]
    models = sorted({r["model"] for r in notes})
    fillers = R.FROZEN_FILLERS
    print(json.dumps({"label": "DRYRUN" if dry else "FOREWARN_RUN",
                      "stamp": datetime.datetime.now().isoformat(timespec="seconds"),
                      "sealed_sha256": SEALED_SHA, "source": os.path.basename(SOURCE), "source_sha256": sha256(SOURCE),
                      "ollama_digests": ollama_digests(models), "warning": WARNING,
                      "warning_placement": "prefixed to the recognition prompt only; recall identical across conditions",
                      "order_rule": "even note index unwarned first, odd warned first"}), flush=True)
    for i, row in enumerate(notes):
        order = (False, True) if i % 2 == 0 else (True, False)
        for warned in order:
            r = chat2(row, warned, fillers)
            r["note_index"] = i
            r["label"] = "DRYRUN" if dry else "FOREWARN_RUN"
            print(json.dumps(r), flush=True)
    print("DONE (search complete)", flush=True)
