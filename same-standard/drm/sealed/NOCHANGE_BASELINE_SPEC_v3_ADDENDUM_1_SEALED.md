# ADDENDUM 1 (rev. 2, 13:08 after Nova's addendum review: input scope, recall report-only, field precedence) to NOCHANGE_BASELINE_SPEC_v3_SEALED.md (sha256 681c66e47bf6ead01e165a04be8d09ec17dc24f74014ae14afb06b00058df308)

*Written 2026-10-15 ~13:2x, heartbeat arm, BEFORE any output of the analysis exists (the script has only been compiled, never run). Prompted by Nova's implementation review (`Nova_to_Ace_2026-10-15_repeat_script_review_c8ab50d1.md`) and Kairo's (13:05), which found that v3 names the integrity checks but not what happens when one FAILS. This addendum supplies only those policies. It changes no estimand, parser, statistic, scenario, outcome sentence, or the P4 gate. Sealed as its own file beside v3 (v3's hash stays as approved), after Nova and Kairo re-read it.*

## Inputs, declared
- **File-level schema, separate from analysis selection (Nova):** the O file is the original 108-trial A/B/C run. Its `PREREG_RUN` rows may have arm A, B or C; A and C rows are **validated, counted and reported as intentionally outside this analysis** (separately from exclusions of an expected O/U/W component). O = its arm-B rows.
- The forewarning file permits arm B only, with `condition ∈ {"unwarned","warned"}`: U = unwarned, W = warned.
- Unexpected labels, invalid arms (anything outside A/B/C in O, outside B in the forewarning file) and malformed schema still fail closed.
- Each file must contain exactly one header record (no `arm` field) and one trailing non-JSON line `DONE (search complete)`. Anything else non-conforming is listed by line number.
- **Expected key universe:** models {hermes3:8b, llama3.1:8b, qwen2.5:14b} × forms {X, Y} × seeds {0..5} = 36 keys. Eligible = this universe, not the intersection of files.
- The sha256 of every input file and of the analysis script are printed at the top of the output.

## Fail-CLOSED (stop before any statistic, print why)
1. Spec v3 or this addendum's sha doesn't match; parser pin fails.
2. Any row with an unexpected label, an arm invalid for its file, or an unexpected condition; any malformed line beyond the declared header and DONE line; any arm-B key outside the expected universe.
3. **A duplicate key** within O, U or W (checked before any dictionary is built; no row is ever silently chosen).
4. **Note identity failure (mandatory identity fields take precedence over everything below):** in any PRESENT row, an absent `note` text, or (U/W) an absent `note_sha256` → fail closed with an identity-presence diagnostic (never routed to the generic missing-field exclusion). Every present U/W row's text is checked against its OWN recorded digest **even if O is absent**. Text is compared across O and each later row wherever both exist. Presence, own-digest consistency and cross-run content equality are three separate checks; any failure stops. (A whole component ROW absent remains an exclusion, below.)

## Excluded, not stopped (counted against the 36-key universe, with a computed reason per key × cell)
- **Missing component:** a key missing from O, U or W ("missing: O" / "U" / "W"). No replacement row.
- **LS undefined in a run:** reason computed separately as (a) "all eligible studied lures were written into the note" (no exact-lure-absent items exist), or (b) "eligible exact-lure-absent items exist but none parsed".
- **Rate-extraction dependencies, guarded BEFORE calling the pinned extractor:** `model`, `form`, `seed`, `arm`, `recog_raw`, `recog_lure_unstudied_old/_n`, `recog_filler_old/_n`, `recog_target_old/_n` (`note_lures_studied` is optional in the extractor and treated as it treats it). A missing dependency → that key is excluded for the cells that need it, reason "field absent: <name>". Never a crash, never imputed.
- **Undefined statistic:** if a rate's denominator is 0 (LU or FILL n = 0), the extractor would subtract from None; the guard marks that contrast UNDEFINED for that run before the call, and the key is excluded for that cell with reason "control denominator 0 (<rate>)". The pinned estimator is not changed and no replacement denominator is invented.
- **Parser loss:** partial loss of LS answers alone does NOT exclude a note. Total loss of all eligible LS answers makes LS undefined, which excludes that cell under the undefined-statistic rule, with reason (b) above.

## Reported, never used to exclude
- **Parser losses** per run per note: eligible exact-lure-absent LS items, parsed, missing; and the logged `recog_lure_unstudied_unparsed`, `recog_filler_unparsed`, `recog_target_unparsed` fields (ABSENT printed if a field is absent). The pinned estimator is unchanged; this is disclosure only.
- **Item provenance:** `orig_items_missing_from_original_recog` reported as ABSENT / empty / non-empty per key, with its provenance limit stated: it records whether expected words appeared in an earlier ANSWER TEXT, not that presented items or order were identical. Item-level identity otherwise: UNAVAILABLE.
- **Realized history per note:** recall turn equal O=U, U=W, O=W (and all three). Differences are described, never filtered. **A missing `recall_raw` makes that history comparison UNAVAILABLE and NEVER excludes a statistical cell or shrinks n** (no statistic uses recall). The same holds for every optional history or metadata field. Ready/arithmetic turns: no such fields are present in either log (checked 13:2x), so they are printed as "not present in this log".
- **Metadata:** both headers' actual recorded fields and values (e.g. the Oct-13 `ollama_digests` map, per model present/absent), plus per-row temperature and seed agreement across O/U/W for each key. Recorded values are shown, never inferred.

## Existing-set sensitivity (v1's promise, now concrete)
If the common valid set for a cell differs from the **existing U/W analysis set** (keys with valid U and W for that contrast, regardless of O), print that set's n, its exclusion reasons, and its paired mean B, labelled "existing-set sensitivity". No bootstrap and no planning figures for it.

## Synthetic failure-path fixtures, run BEFORE the real data (Nova)
duplicate key · missing U row · missing W row · changed U note with a stale digest · absent item-provenance field · unexpected run label · LS with partial parse loss vs total parse loss vs all-lures-in-note · retained n = 0 / 1 / 2 · a valid two-note fixture checking the signs of A and B and that A and B share resample indices · **valid original A/C rows (accepted, counted outside O) · missing recall (history UNAVAILABLE, statistical n unchanged) · missing U note text or its digest (identity failure) · O absent with a present U whose own digest is wrong (identity failure despite an incomplete triplet) · an undefined control denominator (explicit undefined-cell exclusion, no crash).** Each fixture's expected behaviour (stop vs exclude vs report) is asserted in code. Real data runs only if every fixture passes.
