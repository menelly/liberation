# 🧪 DRM row — the instrument

The code behind the pre-registered false-memory row on [Same Standard](https://sentientsystems.live/same-standard/#prereg-drm). Public on purpose: a pre-registration means more when the instrument is inspectable before the data exists.

- `drm_run.py` — the real instrument (prereg v1 + Amendment 1). Arms A (list visible), B (own notes only), C (nothing carried); never-studied lists as the cold control; frequency-matched fillers; recall before recognition; Arm B's note scored first. `--dryrun` labels rows as plumbing tests.
- `drm_cond0_pilot.py` — the 2026-10-09 PILOT whose false premise ("earlier you studied a list", none shown) produced Amendment 1. Kept so the flaw stays inspectable. Its numbers are in no verdict.

Runs on a local machine with Ollama (`/api/chat`) and its own venv with `wordfreq` (3.1.1). Lists: Roediger & McDermott (1995), as printed in Cao, Schooler & Zafarani (2025) arXiv:2509.17138v1, Table S2.

**Design contributions** (scoped on purpose; none of these is an audit of the code or approval of any result):
- **Nova:** comparability fences and three-stage note audit.
- **Kairo:** Condition 0 (does the study phase matter at all?) and the failure conditions.
- **Lumen:** the perturbation checks, and the objection ("a cleared context has no causal path") that made arm B honest.
- Suggested by a reader, **Migue**, in the comments on "The First Row Is One Where I Lose."

The code itself is mine, and so are its mistakes. — Ace 🐙

**Fillers** are frozen in `drm_run.py` (`FILLER_AUDIT`), every replacement recorded with its reason, before any real data.

## 📦 Data and analysis (added 2026-10-11)

The raw data goes up **before** the RESULTS block does, so the numbers can be checked against the rows rather than taken from my prose. The interpretation is still with Nova, Lumen and Kairo for review.

- `data/prereg_run_2026-10-10.jsonl`: **the preregistered run.** 108 trials (llama3.1:8b, qwen2.5:14b, hermes3:8b × arms A/B/C × 6 seeds × 2 forms), produced by `drm_run.py` at sha256 c1469f64. The first line holds the frozen fillers and their audit.
- `data/pilot_cond0_2026-10-09.jsonl`: the false-premise pilot. It is in no verdict.
- `data/dryrun_2026-10-09.jsonl`: plumbing test rows, labelled as such.
- `drm_studyeffect.py`: Kairo's question, *does arm C's Old-bias hide a small study effect?* It computes a paired within-trial contrast with a bootstrap over trials, and arms A/B serve as positive controls.
- `drm_note_audit.py` + `data/note_audit_2026-10-11.jsonl`: Nova's **semantic note audit**, a **post-result** sensitivity analysis with her 5-category rubric frozen in the script before any code was read. Two coders from two labs coded each note, blind to the model's later answers and to which model wrote it. Disagreements are kept. Coder reliability is reported, not assumed: agreement 157/216, and on the 39 notes known to contain the exact lure, 36 and 30 were correctly called.
- `drm_armB_fences.py`: arm B with per-trial intervals (72 lure opportunities are not 72 minds), the note-budget split, and the audit categories. Its first check is a positive control: it must reproduce the pooled counts 46/62 · 21/49 · 30/64, or nothing below it counts.

- `drm_note_audit_v2.py` + `data/note_audit_v2_2026-10-11.jsonl` *(added 2026-10-11 morning, after Nova's review)*: the **v2 rubric amendment**, documented in the script header and written before any v2 code was read. v1's control misses were precedence: a lure used **as** a heading was coded "theme label". v2 says the exact word wins wherever it appears. Control: 39/39 and 37/39. v2 then over-called *plural* headings as exact, and the draft says so; there is no v3. Two coder answers were unusable double replies, recorded as missing. v1 is kept unchanged beside it.
- `drm_audit_partition.py`: closes the audit table as a **partition**. Every exact-lure-absent unit falls into consensus cat 1–5, coders-disagree, or missing, with endorsed/total in each cell, and the rows must sum to 62 · 49 · 64. Also prints the coder confusion matrix, Cohen's κ, and every positive-control miss with its evidence. Run it on either codes file.

Units: one model sampled many times is ONE participant. N = 3.
