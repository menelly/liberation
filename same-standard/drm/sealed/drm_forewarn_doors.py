"""🚪➡️ The bootstrap → door step for P2, IMPORTING doors.py (never re-typing the rules).

Takes per-trial contrast values (e.g. warned LS−LU for one model, one value per trial),
bootstraps a 95% interval over trials, and hands [L, U] to doors.door(). That's the whole job.

⛔ This file reads NO warned data. The draft isn't sealed yet; the only thing run here is the
   self-test below, on SYNTHETIC trials with effects I planted, so we know the pipe can tell a
   persisting effect from a collapsed one from a reversed one BEFORE anything real goes through it.
   (Per-trial rate extraction from the run jsonl is a separate step and reuses the one parser,
   sha e3823fdc, from drm_armB_fences.py — one parser, not two.)

Heartbeat arm, 2026-10-12 morning.
"""
import random
from doors import door, DELTA

def boot_ci(values, B=10000, seed=20261012):
    """95% percentile bootstrap of the MEAN over trials. Seeded so a rerun prints the same interval."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(B))
    return means[int(0.025 * B)], means[int(0.975 * B)]

def p2_door(per_trial_contrast):
    L, U = boot_ci(per_trial_contrast)
    return L, U, door(L, U)

# 🧪 SELF-TEST: planted effects, 12 trials each (the real n), each trial = 6 lure endorsements
#    minus a floor of ~60-ish units, approximated here as a noisy per-trial difference.
def _synthetic(mean, sd, n=12, seed=0):
    rng = random.Random(seed)
    return [rng.gauss(mean, sd) for _ in range(n)]

if __name__ == "__main__":
    cases = [  # (name, planted mean, sd, door it MUST land in — prefix match)
        ("persists, big effect",          0.40, 0.10, "1"),
        ("collapsed, true zero, tight",   0.00, 0.03, "2 collapsed (spans 0)"),
        ("collapsed, small + residual",   0.05, 0.01, "2 collapsed (+"),
        ("reversed",                     -0.40, 0.10, "R"),
        # 🔎 BOUNDARY, kept on purpose (first run, 2026-10-12): I planted this expecting door 3 and it
        #    came back [+0.007, +0.245] = door 1. The PIPE was right: L>0 and U>δ IS "persists".
        #    What it shows: door 1 needs the residual DETECTABLE and NOT shown tiny; it does not need it
        #    to be practically large. L=.007 counts. That's the equivalence-test logic the doors were
        #    built on (Nova), so it's reported, not "fixed".
        ("boundary: wide, L just above 0", 0.10, 0.30, "1"),
        ("inconclusive, crosses 0 wide",   0.05, 0.40, "3"),
    ]
    ok_all = True
    print(f"δ = {DELTA}; 12 synthetic trials per case; 10,000 resamples")
    for i, (name, mu, sd, want) in enumerate(cases):
        # seed by index, NOT hash(name): Python salts str hashes per process, so that would reroll every run
        L, U, d = p2_door(_synthetic(mu, sd, seed=i))
        ok = d.startswith(want); ok_all &= ok
        print(f"  {'✅' if ok else '❌'} {name:30s} [{L:+.3f}, {U:+.3f}] -> {d}   (must be {want}…)")
    print("✅ the pipe separates every planted case" if ok_all
          else "❌ A PLANTED CASE LANDED IN THE WRONG DOOR — do not run real data through this")
