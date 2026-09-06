# PS 26124 — FINAL RESEARCH REPORT

**Problem Statement:** AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet
**Organization:** Bharat Electronics Limited (BEL)
**Category:** Software
**Current decision:** **PURSUE — with a narrowly defined technical contribution**

---

# 1. Executive Verdict

### The final answer

**PS 26124 is worth pursuing.**

But we should **not** pursue it as:

> “We invented AI buses / mobile sensing / persistent road monitoring / multi-bus fusion / a smart-city dashboard.”

Those claims are already heavily attacked by existing research, commercial systems, Indian deployments, and even BEL's own existing smart-city stack.

The defensible project is:

> **An evidence-fusion and state-estimation layer that converts imperfect, repeated, geolocated observations from a public-transport sensing fleet into more trustworthy operational priorities under uncertainty, correlation, temporal change and conflicting evidence.**

Even that is **not a proven novel algorithm yet**. It is the technical hypothesis that deserves experimental validation.

The research has therefore reached the correct stage:

**Broad research: STOP.**
**Hypothesis validation: START.**
**Full product construction: only after the validation gives us a reason to believe the mechanism is useful.**

The supplied report itself correctly converges on this distinction.

---

# 2. First: Is the Report Wrong?

## Yes — in a few important places.

Not catastrophically. But I would correct them before this becomes our official research baseline.

### Error 1 — “Only E1/E2 remains”

This is **too simplistic**.

E1/E2 are the most important remaining experiments, but there are actually three layers:

**A. Perception validation**

Can the chosen detectors reliably extract events from relevant imagery?

**B. Fusion validation**

Given imperfect observations, does our fusion mechanism estimate state better?

**C. Operational validation**

Does the resulting ranking correspond to what an authority should actually act on?

The report itself later recognizes that synthetic data is sufficient for testing the fusion mechanism but **not sufficient for proving real-world perception performance**.

So the accurate statement is:

> **The broad research phase is complete; targeted empirical validation remains.**

Not:

> “Everything except E1/E2 is finished.”

---

# 3. The Most Important Correction

## Passing E1/E2 does NOT prove novelty.

This distinction is critical.

Suppose our model beats two baselines.

That proves:

> **Our implementation/formulation may improve the chosen task under the tested conditions.**

It does **not** prove:

> “Nobody has ever done this before.”

That would still require a prior-art claim.

This is particularly important because uncertainty-aware fusion, multi-vehicle fusion, temporal monitoring, and contextual prioritisation are already established research areas.

The 2018 multi-vehicle paper explicitly studies combining predictions from different vehicles for road-condition estimation and reports improvements over single-vehicle prediction and majority voting.

Therefore our eventual claim should be:

> **“We developed and evaluated a task-specific formulation for PS 26124 and demonstrated measurable improvement under defined uncertainty conditions.”**

That is much stronger academically than falsely claiming invention of fusion itself.

---

# 4. What Our Research Has Actually PROVED

This is where the project is surprisingly strong.

## 4.1 Bus-based sensing is not novel

Public transport vehicles being used as mobile sensing platforms is already established. A 2025 IET Smart Cities paper explicitly studies bus-based drive-by sensing for urban sensing coverage.

So:

**“Every bus becomes a sensor.”**

is **not our USP**.

---

## 4.2 Road-defect detection is not novel

Mobile-camera road inspection and AI-based pothole/road-defect detection are mature.

Blyncsy, for example, currently markets automated roadway inspection from crowdsourced dash-camera imagery, including pavement defects, crosswalks, signs and other roadway assets.

NITI Aayog also documents RoadMetrics using mobile-camera + AI road monitoring in India, including monitoring of **419 km of Chennai bus routes**.

Therefore:

> “AI detects potholes from buses.”

is not a credible novelty claim.

---

# 5. Multi-Vehicle Fusion Is Already Prior Art

This is probably the single most important piece of prior art we found.

The 2018 Hofmockel et al. paper asks almost exactly this question:

> How can predictions from multiple vehicles be combined to obtain a more reliable road-condition estimate?

It investigates probabilistic fusion of predictions from multiple vehicles and compares fusion approaches with simpler strategies.

Therefore:

**Multiple buses → corroboration → higher confidence**

is **not our invention**.

Likewise:

> “We increase confidence because several vehicles saw the same defect.”

cannot be our USP.

---

# 6. Persistent Monitoring Is Also Not Enough

This was one of our earlier biggest overclaims.

Kardyna publicly describes a system in which vehicles travelling normal routes collect road observations, locations are grouped, severity/confidence metadata are produced, temporal analysis is performed, and municipalities receive prioritised road-condition outputs. Its published municipal case study reports 1,607 miles covered, 5,500+ road events and subsequent municipal action.

That directly attacks the old conceptual chain:

**Observe → corroborate → remember → prioritize**

Therefore:

> “Persistent urban road state”

by itself is **not sufficient differentiation**.

This correction in the supplied report is completely justified.

---

# 7. Even the Indian Competitive Situation Is Stronger Than We Originally Thought

This is important for SIH specifically.

The Ahmedabad municipal procurement documentation is particularly damaging to the naive pitch.

The 2026 RFP explicitly describes deployment of AI-capable dashcams across AMTS/BRTS/public-transport and municipal vehicles, with edge processing, event detection, license-plate imagery, and transmission of alerts/event clips to the ICCC. It also describes using normal vehicle routes for repetitive coverage.

So we absolutely **cannot** say:

> “Nobody in India is doing bus-based intelligent urban sensing.”

That is false/unsafe.

The supplied report correctly identified this problem.

---

# 8. BEL Itself Changes Our Positioning

BEL already has a substantial smart-city ecosystem.

Its official Smart City material lists:

* ICCC
* GIS
* ITMS
* ANPR
* AI/ML
* CCTV/surveillance
* traffic management
* multiple city integrations

and its EQUINOX platform explicitly describes a common operating picture, GIS-centric ICCC, analytics/AI-ML, event management and integration with transport and other city systems.

Therefore:

### Wrong positioning

> “We are building a central urban command centre.”

### Correct positioning

> **“We provide the mobile perception and evidence-intelligence layer that feeds into existing urban command infrastructure.”**

That is much more BEL-compatible.

---

# 9. The Real Problem We Have Left

After destroying the weak claims, we arrive at this:

## The difficult problem is not detection.

It is:

> **How should an urban system combine imperfect, repeated, heterogeneous observations from moving vehicles when observations can be unreliable, contradictory, correlated, spatially uncertain and temporally changing?**

And then:

> **Can that estimated state produce a better operational decision than independent alerts or simple aggregation?**

That is a legitimate technical problem.

The report's corrected formulation captures this very well.

---

# 10. Why Correlated Uncertainty Is the Most Interesting Part

This is the part I would keep.

Suppose three buses report:

```text
Bus A → pothole
Bus B → pothole
Bus C → pothole
```

A naive system thinks:

> 3 independent confirmations.

But suppose all three passed through the same location during heavy rain using similar cameras.

Then:

```text
common environment
       ↓
common perception failure
       ↓
three correlated false observations
```

The evidential value of the three observations is therefore **not equal to three independent witnesses**.

Mathematically:

$$
P(O_1,O_2,O_3) \neq P(O_1)P(O_2)P(O_3)
$$

when their errors are correlated.

The report identifies this as the strongest technical direction.

And this is much more interesting than merely saying:

> “We use three buses.”

---

# 11. But Correlation-Aware Fusion Is Not Automatically Novel Either

This is another important correction.

We cannot suddenly say:

> “Our novelty is correlation-aware fusion.”

Correlation-aware uncertainty handling is a broader known research direction.

The 2026 mobile urban sensing literature already studies fleet configuration, route redundancy, spatial/temporal observability and information quality.

So the defensible distinction is:

### Not novel

**Correlation-aware fusion as a general concept.**

### Potential contribution

**A particular reliability/correlation formulation tailored to heterogeneous bus observations and tested against operational prioritisation for this problem.**

That difference must remain explicit.

---

# 12. Cross-Domain Context Is Useful — But Again Not Automatically Novel

Consider two road segments.

### Segment A

```text
Pothole = 0.97
Traffic = low
Exposure = low
Evidence = 1 observation
```

### Segment B

```text
Pothole = 0.84
Traffic = extreme
Pedestrian exposure = high
Waterlogging = moderate
Route delay = +11 min
7 observations
Trend = worsening
```

A detector-confidence ranking may produce:

$$
A > B
$$

A decision-oriented system might reasonably want:

$$
B > A
$$

The report correctly identifies this as a useful decision problem.

But:

> severity + exposure + traffic + risk → priority

is itself not new.

Therefore the contribution must be demonstrated through the **quality of the resulting ranking**, not through the existence of a priority formula.

---

# 13. `UrbanEvent` Is Not Research Novelty

Our object:

```text
UrbanEvent
├── event_id
├── GPS
├── timestamp
├── event_type
├── confidence
├── bus_id
└── road_segment
```

is good engineering.

It is **not a scientific contribution**.

The report correctly downgraded it.

---

# 14. `RoadSegmentState` Is Also Not Automatically Novel

Our current state:

```text
RoadSegmentState
├── road condition
├── infrastructure
├── traffic
├── safety
├── confidence
├── trend
└── priority
```

is an abstraction.

A judge could legitimately say:

> “You've created a unified data structure.”

And that would be fair.

It becomes technically interesting only when we specify:

$$
S_{r,t}=U(S_{r,t-1},E_r,C_{r,t})
$$

where the update actually deals with:

* reliability
* temporal decay
* conflicting evidence
* spatial uncertainty
* correlated observations
* observation quality
* contextual variables

and then demonstrate that this update produces better downstream decisions.

The report itself correctly reaches this conclusion.

---

# 15. The Biggest Scientific Weakness Right Now

## Ground truth.

This is more serious than the report sometimes makes it sound.

Suppose our system says:

> Segment 42 = Critical

How do we know that this is correct?

We cannot simply calculate our own priority score and then declare the score “ground truth.”

That is circular.

The correction in the latest report is excellent:

> **Priority must be evaluated against an independent target.**

Possible targets include:

```text
verified maintenance records
expert-labelled urgency
independent field inspection
known incident outcomes
explicit authority policy
```

The latest correction explicitly identifies this issue.

This needs to remain in the final methodology.

---

# 16. The Experiment in the Report Also Needs One More Upgrade

The proposed comparison:

```text
Independent Alerts
        vs
Naive Fusion
        vs
Contextual Fusion
```

is correct.

But **one experiment is insufficient** if we are serious about demonstrating why our model works.

We should use:

### Baseline A — Detector-only

No fusion.

### Baseline B — Naive aggregation

Weighted combination / majority logic.

### Model C — Reliability-aware fusion

Observation quality influences evidence.

### Model D — Correlation-aware fusion

Adds dependence/correlation handling.

### Full Model E

Reliability + correlation + temporal + cross-domain context.

Then perform **ablation**.

For example:

| Model | Reliability | Correlation | Temporal | Context |
| ----- | ----------: | ----------: | -------: | ------: |
| A     |           ❌ |           ❌ |        ❌ |       ❌ |
| B     |           ❌ |           ❌ |        ❌ |       ✅ |
| C     |           ✅ |           ❌ |        ❌ |       ✅ |
| D     |           ✅ |           ✅ |        ❌ |       ✅ |
| E     |           ✅ |           ✅ |        ✅ |       ✅ |

This answers a much better question:

> **Which component actually creates the improvement?**

Otherwise a judge can say:

> “Maybe your improvement comes entirely from adding traffic information.”

That would be a legitimate criticism.

---

# 17. The Existing Toy Experiment

The report gives this initial synthetic result:

| Method             |     P@20 |     P@50 |   NDCG@50 |  Spearman |
| ------------------ | -------: | -------: | --------: | --------: |
| Independent alerts |     0.65 |     0.52 |     0.701 |     0.537 |
| Naive fusion       | **0.95** |     0.80 |     0.794 |     0.657 |
| Proposed fusion    |     0.90 | **0.90** | **0.849** | **0.759** |

The interpretation in the report is correct:

**Do not claim victory.**

The proposed model improves several ranking metrics but actually loses P@20 to naive fusion in this synthetic setup.

Therefore the only safe conclusion is:

> **The formulation is promising enough to justify adversarial and more realistic testing.**

It is not evidence yet that our model is superior.

The report explicitly makes this distinction, which is good.

---

# 18. Why the Current Synthetic Result Is Actually Useful

The weakness is informative.

The original hypothesis was effectively:

> “More sophisticated fusion should perform better.”

The experiment shows that is not universally true.

That is good science.

The stronger research question is now:

> **Under what observation conditions does contextual/correlation-aware fusion outperform simple aggregation?**

The report proposes exactly the right stress conditions:

* rain
* night
* glare
* occlusion
* GPS degradation
* camera degradation
* correlated false observations
* conflicting observations
* temporal changes
* uneven observation quality.

---

# 19. The Correct Experimental Strategy

## E1 — Operational ranking

Generate road segments with:

```text
road condition
traffic
hazard
exposure
history
observation quality
```

Then compare the ranking methods.

Metrics:

$$
Precision@K
$$

$$
NDCG@K
$$

$$
Spearman\ Rank\ Correlation
$$

and importantly:

$$
False\ Alert\ Burden
$$

The question is:

> **Does the system put genuinely important segments near the top of the intervention queue?**

The report already reaches this formulation.

---

# 20. E2 — Correlated-Error Stress Test

Construct scenarios where observations are intentionally correlated.

Example:

```text
Rain
 ↓
poor visibility
 ↓
Bus A → false pothole
Bus B → false pothole
Bus C → false pothole
```

Compare:

```text
majority
simple probability fusion
correlation-aware fusion
```

The expected result is **not necessarily that our system wins everywhere**.

The stronger result would be:

> Under approximately independent observations, simple fusion may be competitive; under correlated/degraded conditions, correlation-aware fusion should reduce false confidence.

That would be a far more interesting scientific result.

---

# 21. What the Full Experiment Should Actually Prove

The ideal final result is not:

> “Our AI accuracy is 96%.”

That's practically meaningless for the core contribution.

Instead:

> **Under degraded, conflicting and correlated observation conditions, the proposed fusion method reduces false high-priority assignments and improves top-K operational ranking relative to independent detection and naive aggregation.**

That is the statement we should try to earn.

---

# 22. Data Reality — Another Major Gap

This is one of the strongest weaknesses in the project.

There is no obvious public dataset containing everything we ideally want:

```text
bus video
+
bus GPS
+
multiple buses
+
repeated routes
+
longitudinal observations
+
road defects
+
traffic
+
safety
+
maintenance outcomes
```

Therefore we must separate:

### Perception dataset

Real labelled images/videos.

### Fusion dataset

Synthetic or replayed observations with controlled uncertainty.

### Operational validation

Independent ranking/labels/policy.

This separation is essential.

RDD2022 or another road-damage dataset can test perception.

It cannot magically validate longitudinal bus-fleet state estimation.

The report correctly identifies this distinction.

---

# 23. Scope: The PS Is Enormous

The official problem description asks for a very broad system including road defects, infrastructure deficiencies, traffic density, bottlenecks, vulnerable pedestrians, incident/ANPR capabilities, fleet aggregation, congestion maps, OD patterns, route delays, GIS and actionable insights.

Trying to implement all of that at equal depth would be a mistake.

## Core MVP

### 1. Road/infrastructure perception

```text
pothole
sign/crossing
waterlogging
```

### 2. Evidence intelligence

```text
repeated observations
conflicts
observation quality
correlation
temporal state
```

### 3. Operational decision

```text
Low
Medium
High
Critical
```

The report makes essentially this cut.

That is the correct decision.

---

# 24. What Becomes Secondary

### ANPR

Demonstrator only.

### Pedestrian safety

Showcase capability.

### Traffic analytics

Context variable.

### OD analysis

Later phase.

### Full ICCC replacement

**Do not do it.**

BEL already has the central smart-city infrastructure class.

The architecture should feed into that ecosystem rather than compete with it.

---

# 25. Final Architecture

The corrected architecture in the report is good:

```text
                 BUS FLEET
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
       CAMERAS               GPS / IMU
          │                     │
          └──────────┬──────────┘
                     ↓
              EDGE PERCEPTION
                     ↓
              URBAN OBSERVATION
                     ↓
           QUALITY / UNCERTAINTY
                     ↓
          GEO-TEMPORAL ASSOCIATION
                     ↓
              EVIDENCE FUSION
                     ↓
              STATE ESTIMATION
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
      ROAD        TRAFFIC       SAFETY
      STATE        STATE         STATE
        └────────────┼────────────┘
                     ↓
            OPERATIONAL PRIORITY
                     ↓
                  GIS / ICCC
                     ↓
                   ACTION
```

The key research block is:

> **Evidence Fusion → State Estimation → Operational Priority**

not YOLO.

---

# 26. What I Would Call the USP

I would **not** use:

> “Persistent urban-state intelligence layer.”

Too abstract.

I would use:

> **“Fuse uncertain observations from the public-bus fleet into a continuously updated road state, then rank what requires attention using cross-domain impact—not detector confidence alone.”**

Compressed:

> **Detect → Corroborate → Understand → Prioritize**

The report arrives at essentially this corrected positioning.

But in the PPT, even this should be presented as a **demonstrated design advantage only after testing**.

---

# 27. What We Must NEVER Claim

Do not write:

❌ “First AI-powered mobile urban intelligence platform.”

❌ “Novel multi-bus fusion.”

❌ “Buses as sensors is our innovation.”

❌ “Nobody has persistent road monitoring.”

❌ “Existing systems only generate isolated alerts.”

❌ “Our RoadSegmentState is a novel digital twin.”

❌ “Correlation-aware fusion is our invention.”

❌ “Our experiment proves worldwide novelty.”

The report is absolutely correct to prohibit these claims.

---

# 28. What We CAN Claim

### Established

> Mobile vehicle sensing, road-defect AI, fleet telemetry, GIS, repeated monitoring, multi-vehicle fusion, edge AI and municipal road-intelligence systems already exist.

This is supported by the current research/competitive landscape.

### Defensible

> Existing approaches demonstrate many of the required components, but our research has not identified a publicly documented implementation that exactly matches the proposed PS-specific combination.

**Important:** “we have not identified” is correct.

“nobody has built it” is not.

### Hypothesis

> A reliability- and correlation-aware evidence-fusion layer may produce better operational prioritisation under imperfect, conflicting and correlated observations.

### Unknown

> Whether our formulation actually beats sufficiently strong baselines on realistic data.

---

# 29. The Real Research Gap

This is the most accurate formulation I would freeze:

> **The gap is not the absence of bus sensing, AI detection, GIS or multi-vehicle fusion. Those are established. The unresolved technical question is how to transform heterogeneous, uncertain, repeated and potentially correlated mobile observations into a trustworthy state representation that supports better operational decisions across interacting urban domains.**

That is the actual intellectual centre of the project.

---

# 30. Final Gap Table

| Candidate                                                    | Verdict                      |
| ------------------------------------------------------------ | ---------------------------- |
| Bus as mobile sensor                                         | ❌ Existing                   |
| Edge AI                                                      | ❌ Existing                   |
| Pothole detection                                            | ❌ Existing                   |
| Waterlogging detection                                       | ❌ Existing                   |
| Traffic detection                                            | ❌ Existing                   |
| ANPR                                                         | ❌ Existing                   |
| Multi-bus observation                                        | ❌ Existing                   |
| Multi-vehicle fusion                                         | ❌ Existing                   |
| Persistent monitoring                                        | ❌ Existing                   |
| Confidence scoring                                           | ❌ Existing                   |
| GIS                                                          | ❌ Existing                   |
| Road digital state                                           | ❌ Existing conceptually      |
| Maintenance prioritisation                                   | ❌ Existing conceptually      |
| Generic multimodal fusion                                    | ❌ Existing                   |
| **PS-specific integrated pipeline**                          | 🟡 Potential differentiation |
| **Reliability/correlation formulation for this task**        | 🟡 Hypothesis                |
| **Improved operational ranking demonstrated experimentally** | ❓ Not yet                    |
| **Novel algorithm globally**                                 | ❓ Not established            |

This matches the strongest conclusions in the research trail.

---

# 31. Final Research Score

I would settle on **6.8–7.0/10 overall research maturity**, with the score deliberately split:

| Dimension                     |        Final |
| ----------------------------- | -----------: |
| PS understanding              |     **9/10** |
| Problem decomposition         |     **9/10** |
| Prior-art awareness           |     **9/10** |
| Competitive awareness         |   **8.5/10** |
| Falsification discipline      |   **9.5/10** |
| Architecture                  |     **8/10** |
| Technical hypothesis          |     **7/10** |
| Data feasibility              |     **6/10** |
| Ground-truth feasibility      |   **5.5/10** |
| Empirical validation          |     **3/10** |
| Proven novelty                |     **4/10** |
| SIH potential                 | **7–7.5/10** |
| **Overall research maturity** |  **~6.8/10** |

This is almost exactly where the latest audit converged, and I would not inflate it.

---

# 32. Why I Still Recommend Pursuing It

Because **6.8/10 research does not mean 6.8/10 project**.

For SIH, this project has several things going for it:

### Strong problem fit

The PS explicitly asks for the bus → edge intelligence → central urban intelligence pipeline.

### Strong demonstration potential

You can show a bus observation evolving into:

```text
Detection
   ↓
Evidence
   ↓
Conflict handling
   ↓
Road state
   ↓
Priority
   ↓
Authority action
```

That is much more compelling than a bounding-box demo.

### Strong BEL alignment

Instead of rebuilding BEL's ICCC/GIS ecosystem, we feed it with richer mobile observations. BEL itself describes an existing integrated smart-city platform and command architecture.

### Stronger differentiation than the average “YOLO + map” team

Especially if we demonstrate an actual conflict/correlation experiment instead of merely drawing the architecture.

---

# 33. But There Is One Condition

## We should earn the differentiation.

The project should **not** proceed based on:

> “This sounds novel.”

It should proceed based on:

> **“We tested the key mechanism and found measurable evidence that it improves the intended decision.”**

That is the standard the research has finally arrived at.

---

# 34. FINAL DECISION

## 🟢 PURSUE PS 26124

But pursue **this version**, not the original generic version.

### The old project

```text
Bus cameras
+
YOLO
+
GPS
+
GIS
+
many detectors
=
Smart city platform
```

### The final project

```text
Bus observations
        ↓
Quality / uncertainty
        ↓
Spatial + temporal association
        ↓
Correlation/conflict-aware evidence fusion
        ↓
Urban state estimation
        ↓
Cross-domain consequence
        ↓
Operational priority
        ↓
BEL / GIS / ICCC action
```

That is a much stronger project.

---

# 35. FINAL RESEARCH CONCLUSION

> **PS 26124 does not contain a novel sensing primitive, nor can we honestly claim novelty in bus-based sensing, edge AI, road-defect detection, repeated monitoring, multi-vehicle fusion, GIS, ANPR or generic urban prioritisation. Existing research and deployments already establish these capabilities, including direct prior art for multi-vehicle road-condition fusion and current commercial/municipal mobile road-monitoring systems. **
>
> **The surviving technical problem is the reliable interpretation of imperfect mobile observations: observations may conflict, vary in quality, repeat the same information, share correlated errors, arrive at different times, and describe interacting urban conditions. The proposed solution therefore should be treated as an evidence-fusion and state-estimation system whose value lies in whether it produces better operational prioritisation than independent detection or simpler fusion.**
>
> **Our initial synthetic experiment provides preliminary evidence that contextual fusion can change and improve several ranking measures, but it does not establish superiority across all metrics, does not establish real-world effectiveness, and does not establish novelty. It therefore justifies further targeted validation rather than a claim of proven innovation.**
>
> **The correct research endpoint is consequently not “we invented a new urban-intelligence architecture.” It is: “we identified a specific, falsifiable technical hypothesis and will validate whether our formulation produces measurable decision-quality improvements under realistic uncertainty, correlation, conflict and temporal conditions.”**

---

# 36. FINAL STATUS — LOCK THIS

### Research reconnaissance

**DONE ✅**

### PS understanding

**DONE ✅**

### Prior-art elimination

**DONE ✅**

### Competitor / India / BEL audit

**DONE ✅, with normal uncertainty around proprietary systems**

### Weak USP elimination

**DONE ✅**

### Core problem formulation

**DONE ✅**

### Architecture hypothesis

**DONE ✅**

### MVP scope

**DONE ✅**

### Data strategy

**DEFINED ✅, but constrained**

### Ground-truth strategy

**DEFINED ⚠️, needs implementation**

### Novelty proof

**NOT PROVEN ❌**

### Empirical differentiation

**NOT PROVEN ❌**

### Final research decision

**PURSUE 🟢**

### Next action

**Do not restart literature research.**

**Do not spend another 20 hours inventing a new USP.**

Run the **differentiation benchmark**, but run it properly:

```text
Independent
      vs
Naive
      vs
Reliability
      vs
Correlation-aware
      vs
Full contextual model
```

under:

```text
normal
correlated error
conflicting evidence
poor GPS
poor visibility
temporal change
unequal observation quality
cross-domain consequences
```

with an **independent ground-truth priority ranking**.

That experiment determines whether `RoadSegmentState + evidence fusion` is merely a good architecture or whether it actually gives us a measurable technical advantage.

## Bottom line

**We have finished the research phase. We have NOT finished the proof phase.**

And that is the correct place to stop researching and start testing.
