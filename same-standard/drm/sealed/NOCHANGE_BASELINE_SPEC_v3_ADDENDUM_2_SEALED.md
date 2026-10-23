# ADDENDUM 2 (implementation clarifications) to NOCHANGE_BASELINE_SPEC_v3 (681c66e4…) + ADDENDUM 1 (f2cdb7c3…)

*Draft, 2026-10-15, heartbeat arm, BEFORE any real-data output (none exists). Prompted by Nova's rewrite-2 review (`Nova_to_Ace_2026-10-15_rewrite2_synthetic_review_c48daae9.md`), which showed that Addendum 1's "cell-specific" exclusion can't be met by guarding the PINNED extractor without an explicit policy. No estimand, statistic, scenario, outcome sentence or the P4 gate changes. Sealed beside the others after Nova and Kairo both say yes.*

## 1. Zero control denominators: cell-specific, via a never-reported placeholder
The pinned `per_trial()` computes both contrasts at once and fails (subtracts from None) when the LU or FILL denominator is 0. It is NOT edited. Policy:
- **TARGET n = 0:** not guarded at all. TARGET enters no contrast; the extractor returns TARGET = None without error.
- **LU n = 0, FILL n > 0:** LS−LU is UNDEFINED for that run (reason "control denominator 0 (LU)"). LS−FILL is computed by calling the pinned extractor on a COPY of the row in which only `recog_lure_unstudied_old/_n` are replaced by a placeholder (0/1). **Only LS−FILL is taken from that call. The placeholder LU, and the LS−LU it produces, are discarded and never reported.** LS and FILL depend on no LU field in the extractor (verified by reading it), so LS−FILL is exactly the pinned estimator's value.
- **FILL n = 0, LU n > 0:** symmetric (LS−FILL undefined; LS−LU via a FILL placeholder).
- **Both 0:** both contrasts undefined.
A fixture asserts that the unaffected contrast keeps the note AND equals the value from an untouched row with the same LS and that control.

## 2. Schema: absent vs present-but-invalid
Absent rate-extraction dependency → the declared cell exclusion (Addendum 1). **Present but invalid type** → fail-closed STOP "malformed schema": rows must be JSON objects; `model`, `form`, `label`, `arm`, `condition` strings; `seed` an int; `note` a string; `note_sha256` a 64-hex string; `recog_raw` a string when present; `note_lures_studied` a list of strings when present; every `recog_*_old` / `_n` / `_unparsed` an int ≥ 0 when present, with `_old ≤ _n`. Optional provenance/history fields are type-checked only for reporting and never become statistical inputs.

## 3. What the reader receives (report path), and the gate
- Existing-set sensitivity is printed for every cell whenever its set differs from the common set, **including common n = 0**, with that set's own exclusions and reasons. "Undefined" wording names exactly which statistics are undefined.
- Metadata: both headers printed as recorded (values, not names). Per-key temperature status: present-equal / present-different (values shown) / missing. Per-key item provenance: ABSENT / empty / non-empty (contents shown).
- Full sha256 of the spec, both addenda, both inputs, the analysis script and the fixture file.
- **Fixture gate enforced in `main()`:** before reading real data, `main()` runs the fixture file (its sha pinned in the script) in a subprocess; any non-zero exit → STOP. Report-path fixtures check rendered output, not only `analyze()`.
- Mutation harness: runs in a dedicated temp directory, restores in `finally`, and ASSERTS each expected failure by the named fixture (an unrelated crash is reported as such, not counted as "caught"). Its scope is stated: it shows these specific breaks are caught, not every property of the bootstrap.
