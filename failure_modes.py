"""
DRISHTI - ADVERSARIAL SELF-CRITICISM PROBE

Purpose: find where OUR OWN method is confidently wrong.

The correlation discount in fusion_benchmark.py estimates rho from observable
WEATHER. That covers only ONE source of correlated error - shared environment.
It does NOT cover a second, arguably worse source:

    MODEL CORRELATION. Every bus runs the SAME YOLO weights. If the model
    systematically misreads tar patches / shadows / manhole covers as potholes,
    then 40 buses agree, the sky is clear, our estimated rho = 0.15, N_eff stays
    high, and we escalate a non-defect with HIGH confidence.

This probe builds that adversary and measures whether DRISHTI survives it.
An honest system reports the conditions under which it fails.
"""

import random
import statistics
from fusion_benchmark import (Config, evaluate, spearman, m_detector_only,
                              m_naive_count, m_independent, m_context_only,
                              m_drishti, m_fl_drishti, _context_score)

CONFUSER_FRACTION = 0.10      # 10% of segments contain a systematic visual confuser
CONFUSER_BIAS = 0.70          # what the shared model reports on them
CONFUSER_SPREAD = 0.06        # tiny spread: the model is CONSISTENTLY wrong


def make_adversarial_world(policy, with_confusers=True):
    segments = []
    for _ in range(Config.NUM_SEGMENTS):
        is_confuser = with_confusers and random.random() < CONFUSER_FRACTION

        if is_confuser:
            severity = 0.0                     # NO real defect. Ever.
        else:
            r = random.random()
            severity = (random.uniform(0.75, 1.0) if r < 0.15 else
                        random.uniform(0.40, 0.74) if r < 0.50 else
                        random.uniform(0.15, 0.39) if r < 0.85 else 0.0)

        traffic = random.uniform(100, 2500)
        delay = min(random.expovariate(1 / 2.5 if severity > 0.4 else 1 / 0.5), 15.0)
        pedestrian = random.betavariate(2, 5)
        true_urgency = (policy["severity"] * severity
                        + policy["traffic"] * (traffic / 2500.0)
                        + policy["delay"] * (delay / 15.0)
                        + policy["pedestrian"] * pedestrian)

        # Confusers occur in CLEAR weather - so our weather-based rho says
        # "these observations are independent". They are not.
        is_rain = (not is_confuser) and random.random() < Config.RAIN_PROBABILITY
        shared = random.gauss(0, Config.SHARED_ENV_NOISE_SD) if is_rain else 0.0

        # FL weight divergence per segment (same simulation as fusion_benchmark).
        # For confuser segments: FL buses have WIDER spread because local fine-tuning
        # causes different buses to react differently to the same visual confuser.
        # This is the partial defence FL provides against the model-correlation attack.
        fl_divergence = min(1.0, random.betavariate(2, 3)
                            * Config.FL_ROUNDS / 10.0)

        obs = []
        for _ in range(random.randint(1, Config.MAX_PASSES)):
            indiv = random.gauss(0, Config.INDIV_NOISE_SD)
            if is_confuser:
                # Without FL: all buses share same weights -> same mistake, tiny spread.
                # With FL:    local fine-tuning widens spread per corridor.
                #             Some buses learn to suppress the confuser; others don't.
                fl_spread_boost = fl_divergence * 0.20
                adjusted_spread = CONFUSER_SPREAD + fl_spread_boost
                conf = min(0.98, max(0.0, CONFUSER_BIAS
                                     + random.gauss(0, adjusted_spread)))
            elif severity == 0.0 and is_rain:
                conf = min(0.98, max(0.0, 0.65 + 0.5 * shared + indiv))
            elif severity > 0:
                conf = min(0.99, max(0.10, severity
                                     + (shared if is_rain else 0.0) + indiv))
            else:
                conf = min(0.40, max(0.0, 0.5 * indiv))
            obs.append({"raw_conf": conf,
                        "camera_quality": random.uniform(0.70, 0.98),
                        "gps_accuracy": random.uniform(0.50, 0.95)})

        noisy = lambda v, sd: min(1.0, max(0.0, v + random.gauss(0, sd)))
        segments.append({
            "true_urgency": true_urgency,
            "is_confuser": is_confuser,
            "obs": obs,
            "obs_traffic": noisy(traffic / 2500.0, Config.TRAFFIC_OBS_SD),
            "obs_delay": noisy(delay / 15.0, Config.DELAY_OBS_SD),
            "obs_pedestrian": noisy(pedestrian, Config.PEDESTRIAN_OBS_SD),
            "obs_is_wet": is_rain,
            "obs_fl_divergence": fl_divergence,   # needed by m_fl_drishti
        })
    return segments


METHODS = [("Detector-only",                       m_detector_only),
           ("Naive count",                          m_naive_count),
           ("Reliability-wtd (independent)",        m_independent),
           ("Context only",                         m_context_only),
           ("DRISHTI (weather-corr-aware)",          m_drishti),
           ("DRISHTI + FL (weather + model corr)",  m_fl_drishti)]


def run(trials=100):
    stats = {n: {"confusers_in_top20": [], "P@20": []} for n, _ in METHODS}

    for t in range(trials):
        random.seed(5000 + t)
        policy = {k: v + random.gauss(0, Config.POLICY_JITTER)
                  for k, v in Config.POLICY.items()}
        world = make_adversarial_world(policy)
        truth = [s["true_urgency"] for s in world]

        for name, fn in METHODS:
            scores = [fn(s) for s in world]
            order = sorted(range(len(world)), key=lambda i: scores[i], reverse=True)
            # How many of the top-20 dispatches are chasing a phantom defect?
            stats[name]["confusers_in_top20"].append(
                sum(1 for i in order[:20] if world[i]["is_confuser"]))
            stats[name]["P@20"].append(evaluate(truth, scores)["P@20"])

    print("=" * 88)
    print(f"ADVERSARIAL PROBE - systematic MODEL error in CLEAR weather")
    print(f"{trials} trials x {Config.NUM_SEGMENTS} segments; "
          f"{int(CONFUSER_FRACTION*100)}% carry a visual confuser (no real defect)")
    print("=" * 88)
    print(f"{'Method':<40}{'P@20':>10}{'phantom dispatches /20':>26}")
    print("-" * 88)
    for name, _ in METHODS:
        p = statistics.mean(stats[name]["P@20"])
        c = statistics.mean(stats[name]["confusers_in_top20"])
        print(f"{name:<40}{p:>10.3f}{c:>20.2f}  ({100*c/20:.1f}%)")
    print("=" * 88)

    ind = statistics.mean(stats["Reliability-wtd (independent)"]["confusers_in_top20"])
    dri = statistics.mean(stats["DRISHTI (weather-corr-aware)"]["confusers_in_top20"])
    fl  = statistics.mean(stats["DRISHTI + FL (weather + model corr)"]["confusers_in_top20"])

    print(f"\nVERDICT")
    print(f"  Independent baseline sends  {ind:.2f}/20 crews to a phantom defect.")
    print(f"  DRISHTI (weather-only) sends {dri:.2f}/20.")
    print(f"  DRISHTI + FL sends           {fl:.2f}/20.")
    print(f"")
    print(f"  Weather discount improvement:  {ind - dri:+.2f} phantom dispatches avoided.")
    print(f"  FL model discount improvement: {dri - fl:+.2f} additional phantom dispatches avoided.")
    print(f"  Total improvement over naive:  {ind - fl:+.2f} phantom dispatches avoided.")

    if abs(ind - dri) < 0.5:
        print("\n  => WEATHER DISCOUNT ALONE does not defend against this attack.")
        print("     rho is estimated from weather. The error is from shared MODEL weights,")
        print("     not shared weather, so the weather discount never fires.")

    if dri - fl < 0.5:
        print("\n  => FL IMPROVEMENT IS MARGINAL on this adversary.")
        print("     FL widens confuser spread but confuser bias (0.70) still pulls")
        print("     high-pass buses into the top-20. More FL rounds or active")
        print("     hard-negative mining would be needed to fully close the gap.")
        print("     Documented limitation, not a solved problem.")
    else:
        print("\n  => FL PARTIALLY CLOSES THE MODEL-CORRELATION GAP.")
        print(f"     {dri - fl:.2f} fewer phantom dispatches per 20 with FL-diverged weights.")


if __name__ == "__main__":
    run()
