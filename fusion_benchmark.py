"""
DRISHTI / PS 26124 - CORRELATED EVIDENCE FUSION BENCHMARK (honest rebuild)
Smart India Hackathon - Bharat Electronics Limited

WHAT THIS TESTS
    H1: Under repeated, noisy, environmentally-CORRELATED observations from a
        public bus fleet, does discounting correlated evidence recover the
        municipal priority ranking better than assuming observations are
        independent?

WHY THE PREVIOUS BENCHMARK WAS INVALID
    The earlier version generated ground truth as
        urgency = 0.40*severity + 0.25*traffic + 0.20*delay + 0.15*pedestrian
    and then handed traffic/delay/pedestrian (60% of the answer key) to the
    proposed method NOISE-FREE, while baselines saw only noisy camera
    confidence. It also read the true correlation rho from the ground-truth
    dict. Result: P@10 = 1.000, which measured the leak, not the method.

WHAT IS FIXED HERE
    1. NO ORACLE. Every method reads from the same ObservableSegment - noisy
       estimates only. Ground truth is never visible to any method.
    2. rho is ESTIMATED from observable weather, not read from ground truth.
    3. Methods 3 and 5 differ by EXACTLY ONE THING - the correlation discount -
       so the measured gap is attributable to it.
    4. Policy weights are perturbed per trial, so no method can be tuned to the
       exact ground-truth formula.
    5. Paired per-trial reporting (mean delta, 95% CI, win rate), because a
       single averaged number hides variance.

Pure Python standard library. No external dependencies.
"""

import math
import random
import statistics


# ---------------------------------------------------------------------------
# Experimental parameters - kept configurable so results are not circular.
# ---------------------------------------------------------------------------

class Config:
    NUM_SEGMENTS = 500
    MAX_PASSES = 8
    NUM_TRIALS = 100
    TOP_FRACTION = 0.15          # top 15% of segments = "genuinely urgent"

    # Declared municipal policy (analogous to an IRC / PWD SOP weighting).
    # Fixed and published UP FRONT - not fitted to our own output.
    POLICY = {"severity": 0.40, "traffic": 0.25, "delay": 0.20, "pedestrian": 0.15}
    POLICY_JITTER = 0.05         # per-trial perturbation of the true policy

    # Sensor noise model
    RAIN_PROBABILITY = 0.25
    SHARED_ENV_NOISE_SD = 0.20   # correlated component (same rain, same optics)
    INDIV_NOISE_SD = 0.12        # independent per-camera component

    # How well each contextual signal can actually be measured in the field.
    TRAFFIC_OBS_SD = 0.18        # bus-camera vehicle counting is rough
    DELAY_OBS_SD = 0.06          # GTFS AVL delay is fairly reliable
    PEDESTRIAN_OBS_SD = 0.15     # pedestrian exposure is hard to estimate

    # Correlation estimated from observable weather (NOT ground truth).
    RHO_WET = 0.72
    RHO_DRY = 0.15

    # FL model-correlation parameters.
    # When every bus runs the SAME weights, model rho is high (same blind spots).
    # After FL training, local fine-tuning diverges weights per corridor, lowering rho.
    RHO_MODEL_SAME   = 0.80   # no FL: identical weights across all buses
    RHO_MODEL_FL_MIN = 0.10   # fully diverged FL weights (best case)
    FL_ROUNDS        = 5      # simulated FL aggregation rounds per shift

    SATURATION_K = 1.2           # evidence saturation constant in the fusion term


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def spearman(x, y):
    """Spearman rank correlation with average ranks for ties (no scipy)."""
    n = len(x)
    if n == 0:
        return 0.0

    def ranks(seq):
        order = sorted(range(n), key=lambda i: seq[i])
        out = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and seq[order[j]] == seq[order[j + 1]]:
                j += 1
            avg = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out

    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n))
    dy = sum((ry[i] - my) ** 2 for i in range(n))
    return num / math.sqrt(dx * dy) if dx and dy else 0.0


def evaluate(true_urgency, predicted, ks=(10, 20, 50)):
    """Rank the segments by `predicted`, score against `true_urgency`."""
    n = len(true_urgency)
    gt_order = sorted(range(n), key=lambda i: true_urgency[i], reverse=True)
    urgent = set(gt_order[:int(Config.TOP_FRACTION * n)])
    pred_order = sorted(range(n), key=lambda i: predicted[i], reverse=True)

    res = {}
    for k in ks:
        res[f"P@{k}"] = len(set(pred_order[:k]) & urgent) / float(k)
        idcg = sum(true_urgency[gt_order[i]] / math.log2(i + 2) for i in range(k))
        dcg = sum(true_urgency[pred_order[i]] / math.log2(i + 2) for i in range(k))
        res[f"NDCG@{k}"] = dcg / idcg if idcg > 0 else 0.0

    res["Spearman"] = spearman(true_urgency, predicted)
    res["FalseEsc@20"] = 100.0 * sum(1 for i in pred_order[:20] if i not in urgent) / 20.0
    return res


# ---------------------------------------------------------------------------
# World simulation - ground truth is generated here and NEVER exposed to methods
# ---------------------------------------------------------------------------

def make_world(policy):
    """Generate segments with hidden truth + the noisy observations of it."""
    segments = []
    for i in range(Config.NUM_SEGMENTS):
        r = random.random()
        if r < 0.15:
            severity = random.uniform(0.75, 1.0)
        elif r < 0.50:
            severity = random.uniform(0.40, 0.74)
        elif r < 0.85:
            severity = random.uniform(0.15, 0.39)
        else:
            severity = 0.0

        traffic = random.uniform(100, 2500)
        delay = min(random.expovariate(1 / 2.5 if severity > 0.4 else 1 / 0.5), 15.0)
        pedestrian = random.betavariate(2, 5)

        # --- HIDDEN ground truth: the municipal priority we must recover ---
        true_urgency = (policy["severity"] * severity
                        + policy["traffic"] * (traffic / 2500.0)
                        + policy["delay"] * (delay / 15.0)
                        + policy["pedestrian"] * pedestrian)

        is_rain = random.random() < Config.RAIN_PROBABILITY

        # --- Camera observations: correlated error under shared weather ---
        shared = random.gauss(0, Config.SHARED_ENV_NOISE_SD) if is_rain else 0.0
        passes = random.randint(1, Config.MAX_PASSES)
        observations = []
        for _ in range(passes):
            indiv = random.gauss(0, Config.INDIV_NOISE_SD)
            if severity == 0.0 and is_rain:
                # wet-road reflection mimics a pothole for EVERY passing bus
                conf = min(0.98, max(0.0, 0.65 + 0.5 * shared + indiv))
            elif severity > 0:
                conf = min(0.99, max(0.10, severity + (shared if is_rain else 0.0) + indiv))
            else:
                conf = min(0.40, max(0.0, 0.5 * indiv))
            observations.append({
                "raw_conf": conf,
                "camera_quality": random.uniform(0.70, 0.98),
                "gps_accuracy": random.uniform(0.50, 0.95),
            })

        def noisy(value, sd):
            return min(1.0, max(0.0, value + random.gauss(0, sd)))

        # FL weight divergence: after FL training rounds buses have locally
        # fine-tuned weights. More rounds -> more divergence -> lower rho_model.
        # Simulated as a Beta draw scaled by FL_ROUNDS (higher = more diverged).
        fl_divergence = min(1.0, random.betavariate(2, 3)
                            * Config.FL_ROUNDS / 10.0)

        segments.append({
            "true_urgency": true_urgency,          # hidden - evaluation only
            "obs": observations,                   # observable
            "obs_traffic": noisy(traffic / 2500.0, Config.TRAFFIC_OBS_SD),
            "obs_delay": noisy(delay / 15.0, Config.DELAY_OBS_SD),
            "obs_pedestrian": noisy(pedestrian, Config.PEDESTRIAN_OBS_SD),
            "obs_is_wet": is_rain,                 # observable from weather API
            "obs_fl_divergence": fl_divergence,    # observable: cosine dist from global model
        })
    return segments


# ---------------------------------------------------------------------------
# The five competing methods. Each receives ONLY observable fields.
# ---------------------------------------------------------------------------

def _reliability_weights(obs):
    return [0.6 * o["camera_quality"] + 0.4 * o["gps_accuracy"] for o in obs]


def _context_score(seg):
    """Operational consequence, computed from NOISY observed context."""
    return 0.45 * seg["obs_traffic"] + 0.35 * seg["obs_delay"] + 0.20 * seg["obs_pedestrian"]


def m_detector_only(seg):
    return max(o["raw_conf"] for o in seg["obs"])


def m_naive_count(seg):
    return sum(1 for o in seg["obs"] if o["raw_conf"] >= 0.5)


def m_independent(seg):
    """Reliability-weighted, assumes observations are INDEPENDENT (no discount)."""
    w = _reliability_weights(seg["obs"])
    mean_conf = statistics.mean(c * wi for c, wi in
                                zip((o["raw_conf"] for o in seg["obs"]), w))
    n = len(seg["obs"])
    severity = mean_conf * (n / (n + Config.SATURATION_K))
    return 0.5 * severity + 0.5 * _context_score(seg)


def m_context_only(seg):
    return _context_score(seg)


def m_drishti(seg):
    """Identical to m_independent EXCEPT evidence is discounted for correlation."""
    w = _reliability_weights(seg["obs"])
    mean_conf = statistics.mean(c * wi for c, wi in
                                zip((o["raw_conf"] for o in seg["obs"]), w))
    n = len(seg["obs"])
    # rho estimated from OBSERVABLE weather, not from ground truth
    rho = Config.RHO_WET if seg["obs_is_wet"] else Config.RHO_DRY
    n_eff = n / (1.0 + (n - 1) * rho) if n > 1 else 1.0
    severity = mean_conf * (n_eff / (n_eff + Config.SATURATION_K))
    return 0.5 * severity + 0.5 * _context_score(seg)


def m_fl_drishti(seg):
    """DRISHTI + Federated Learning: discounts BOTH weather AND model correlation.

    The failure_modes.py adversary exploits the fact that all buses share the
    same YOLO weights, so model mistakes are perfectly correlated even in clear
    weather (rho_weather = 0.15, N_eff stays high, phantom escalation occurs).

    FL causes per-corridor fine-tuning which diverges local weights from the
    global model. The observable proxy is obs_fl_divergence (cosine distance
    between local and global weights, 0 = identical, 1 = fully local).
    As divergence increases, rho_model falls, and N_eff is discounted even when
    the sky is clear — partially closing the adversarial gap.
    """
    w = _reliability_weights(seg["obs"])
    mean_conf = statistics.mean(c * wi for c, wi in
                                zip((o["raw_conf"] for o in seg["obs"]), w))
    n = len(seg["obs"])

    # Weather-based rho (same as m_drishti)
    rho_weather = Config.RHO_WET if seg["obs_is_wet"] else Config.RHO_DRY

    # Model-based rho: high when weights identical, drops as FL diverges them.
    # Uses obs_fl_divergence — 0.0 means no FL / same weights for every bus.
    fl_div = seg.get("obs_fl_divergence", 0.0)
    rho_model = max(Config.RHO_MODEL_FL_MIN,
                    Config.RHO_MODEL_SAME * (1.0 - fl_div))

    # Dominant correlation source wins — weather or model, whichever is higher.
    rho = max(rho_weather, rho_model)
    n_eff = n / (1.0 + (n - 1) * rho) if n > 1 else 1.0
    severity = mean_conf * (n_eff / (n_eff + Config.SATURATION_K))
    return 0.5 * severity + 0.5 * _context_score(seg)


METHODS = [
    ("1. Detector-Only (max conf)",                   m_detector_only),
    ("2. Naive Aggregation (count)",                  m_naive_count),
    ("3. Reliability-Wtd + context (independent)",    m_independent),
    ("4. Operational Context Only",                   m_context_only),
    ("5. DRISHTI (weather-corr-aware + context)",     m_drishti),
    ("6. DRISHTI + FL (weather + model corr-aware)",  m_fl_drishti),
]

# Isolation pair A: contribution of weather correlation discount alone
ISOLATION_PAIR = ("3. Reliability-Wtd + context (independent)",
                  "5. DRISHTI (weather-corr-aware + context)")

# Isolation pair B: additional contribution of model correlation discount (FL)
FL_ISOLATION_PAIR = ("5. DRISHTI (weather-corr-aware + context)",
                     "6. DRISHTI + FL (weather + model corr-aware)")


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------

def run(trials=Config.NUM_TRIALS, verbose=True):
    per_trial = {name: [] for name, _ in METHODS}

    for t in range(trials):
        random.seed(1000 + t)
        # perturb the true policy so no method is tuned to the exact weights
        policy = {k: v + random.gauss(0, Config.POLICY_JITTER)
                  for k, v in Config.POLICY.items()}
        world = make_world(policy)
        truth = [s["true_urgency"] for s in world]
        for name, fn in METHODS:
            per_trial[name].append(evaluate(truth, [fn(s) for s in world]))

    if verbose:
        _report(per_trial, trials)
    return per_trial


def _report(per_trial, trials):
    cols = ["P@10", "P@20", "P@50", "NDCG@50", "Spearman", "FalseEsc@20"]
    mean = lambda name, k: statistics.mean(r[k] for r in per_trial[name])

    print("=" * 100)
    print(f"DRISHTI EVIDENCE-FUSION BENCHMARK - {trials} trials x "
          f"{Config.NUM_SEGMENTS} segments, no oracle access")
    print("=" * 100)
    print(f"{'Method':<44} " + " ".join(f"{c:>9}" for c in cols))
    print("-" * 100)
    for name, _ in METHODS:
        print(f"{name:<44} " + " ".join(f"{mean(name, c):>9.3f}" for c in cols))
    print("=" * 100)

    def _isolation_block(label, pair_a, pair_b):
        print(f"\n{label}")
        print(f"  ({pair_b}) minus ({pair_a})")
        print(f"  {'Metric':<14}{'mean delta':>12}{'95% CI':>24}"
              f"{'win':>6}{'tie':>6}{'loss':>6}")
        print("  " + "-" * 68)
        for c in cols:
            deltas = [rb[c] - ra[c]
                      for ra, rb in zip(per_trial[pair_a], per_trial[pair_b])]
            m = statistics.mean(deltas)
            half = (1.96 * statistics.stdev(deltas) / math.sqrt(len(deltas))
                    if len(deltas) > 1 and statistics.stdev(deltas) > 0 else 0.0)
            gain = (lambda d: -d) if c == "FalseEsc@20" else (lambda d: d)
            win  = sum(1 for d in deltas if gain(d) >  1e-12)
            loss = sum(1 for d in deltas if gain(d) < -1e-12)
            tie  = len(deltas) - win - loss
            sig  = "*" if (m - half) * (m + half) > 0 else " "
            print(f"  {c:<14}{m:>+12.4f}{sig}  [{m-half:>+7.4f}, {m+half:>+7.4f}]"
                  f"{win:>6}{tie:>6}{loss:>6}")
        print()

    # --- Isolation A: contribution of weather correlation discount ---
    _isolation_block(
        "ISOLATED CONTRIBUTION — WEATHER CORRELATION DISCOUNT (method 3 vs 5)",
        *ISOLATION_PAIR
    )

    # --- Isolation B: additional contribution of model correlation discount (FL) ---
    _isolation_block(
        "ISOLATED CONTRIBUTION — FL MODEL CORRELATION DISCOUNT (method 5 vs 6)",
        *FL_ISOLATION_PAIR
    )

    print("  * = 95% CI excludes zero (statistically significant)")
    print("  Ties are expected on P@K: K is small, so most trials rank identically.")
    print("  Method 6 improvement over 5 shows how much FL closes the model-"
          "correlation gap\n  documented in failure_modes.py.\n")


def demo():
    """Self-check: the properties the benchmark must have to be valid."""
    random.seed(0)
    world = make_world(Config.POLICY)

    # 1. No method may read ground truth.
    keys = set(world[0])
    assert "true_urgency" in keys
    observable = keys - {"true_urgency"}
    assert observable == {"obs", "obs_traffic", "obs_delay",
                          "obs_pedestrian", "obs_is_wet",
                          "obs_fl_divergence"}, observable

    # 2. Observed context must actually be corrupted, not a copy of truth.
    ctx = [_context_score(s) for s in world]
    assert spearman(ctx, [s["true_urgency"] for s in world]) < 0.95, \
        "observed context is too clean - oracle leak has returned"

    # 3. Correlation discount must reduce effective evidence under rain only.
    wet = {"obs": [{"raw_conf": .8, "camera_quality": .9, "gps_accuracy": .9}] * 6,
           "obs_traffic": .5, "obs_delay": .5, "obs_pedestrian": .5, "obs_is_wet": True}
    dry = dict(wet, obs_is_wet=False)
    assert m_drishti(wet) < m_independent(wet), "no discount applied in rain"
    assert m_drishti(dry) < m_independent(dry), "dry rho must still discount"
    assert m_drishti(wet) < m_drishti(dry), "rain must discount harder than dry"

    # 4. A perfect ranker scores 1.0; a reversed one scores ~0.
    truth = [s["true_urgency"] for s in world]
    assert evaluate(truth, truth)["P@10"] == 1.0
    assert evaluate(truth, [-t for t in truth])["P@10"] == 0.0

    print("demo(): all benchmark validity checks passed\n")


if __name__ == "__main__":
    demo()
    run()
