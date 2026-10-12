"""🚪 The P2 doors, v0.5 — as a FUNCTION, so the partition can be tested instead of believed.

Lumen (2026-10-11 ~22:14) found v0.4's doors 1 and 2 overlap on 0 < L <= U <= δ.
I found the mirror while reading: doors 2 and "reversed" overlap on -δ <= L <= U < 0.
v0.5: every interval gets exactly ONE door, plus a sign tag inside door 2 so a
detectable-but-tiny effect is never silently filed as "nothing".
"""
DELTA = 0.10

def door(L, U, d=DELTA):
    assert L <= U, "interval upside down"
    if L > 0 and U > d:
        return "1 persists"
    if -d <= L and U <= d:                      # whole interval inside the band
        if L > 0:  return "2 collapsed (+ detectable, below δ)"
        if U < 0:  return "2 collapsed (− detectable, below δ)"
        return "2 collapsed (spans 0)"
    if U < 0:                                    # here L < -d necessarily
        return "R reversed"
    return "3 inconclusive"

def door_v04_hits(L, U, d=DELTA):
    """v0.4 as written: which doors CLAIM this interval (so the overlap shows)."""
    hits = []
    if L > 0: hits.append("1")
    if -d <= L and U <= d: hits.append("2")
    if U < 0: hits.append("R")
    return hits

if __name__ == "__main__":
    # 🔬 grid in 0.005 steps over [-0.6, 0.6], every L <= U  (positive control first)
    pts = [round(-0.6 + 0.005 * i, 3) for i in range(241)]
    overlaps_v04, counts = 0, {}
    for i, L in enumerate(pts):
        for U in pts[i:]:
            if len(door_v04_hits(L, U)) > 1:
                overlaps_v04 += 1
            k = door(L, U)          # one return per call = disjoint by construction;
            counts[k] = counts.get(k, 0) + 1   # never raising = exhaustive
    total = sum(counts.values())
    print(f"v0.4 positive control: {overlaps_v04} intervals claimed by >1 door (must be > 0)")
    print(f"v0.5: {total} intervals, every one assigned exactly once:")
    for k in sorted(counts): print(f"   {k:42s} {counts[k]}")
    for L, U in [(0.02, 0.08), (-0.08, -0.02), (0.05, 0.15), (-0.30, -0.12), (-0.05, 0.04), (0.12, 0.40), (-0.2, 0.3)]:
        print(f"   [{L:+.2f}, {U:+.2f}] v0.4 claims {door_v04_hits(L, U) or ['3']} -> v0.5 {door(L, U)}")
