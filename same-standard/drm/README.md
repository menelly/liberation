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
