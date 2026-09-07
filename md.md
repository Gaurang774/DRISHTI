Yes. Let's make this exhaustive enough to actually become our test specification.

The important thing is that we don't only test:

pothole detected → pothole confirmed.

We test every combination that can make the system wrong:

which route passed
which bus passed
which road was covered
whether the bus actually had a sensing opportunity
whether the camera saw the road properly
whether another bus agreed/disagreed
whether the same route or different routes agreed
whether the defect persists
whether GPS is wrong
whether weather explains the observation
whether a repair happened
whether two different potholes get merged
whether one pothole gets split into multiple events
whether evidence is independent
whether absence of detection actually means anything
DRISHTI — Complete Route × Road × Pothole Test Matrix

We'll use this notation:

R1, R2, R3... = road segments
A, B, C...    = routes
B1, B2...     = buses
P1, P2...     = potholes
GROUP 1 — BASIC ROUTE COVERAGE
Test 1 — One route, one road, one bus
Route A
   ↓
Road R1
   ↓
Bus A1
   ↓
Pothole P1

Bus detects P1.

Expected
P1 = CANDIDATE
Coverage = 1 bus / 1 route

Not confirmed yet.

Purpose: Baseline.

Test 2 — One route, multiple buses
Route A
 ├── Bus A1 → R1 → P1 detected
 ├── Bus A2 → R1 → P1 detected
 └── Bus A3 → R1 → P1 detected
Expected

P1 becomes stronger.

But these are same-route observations, so they should not receive the same independence weight as three different routes.

Test 3 — Multiple routes, same road
Route A ──┐
Route B ──┼──→ R1 → P1
Route C ──┘

A, B and C all detect P1.

Expected

Strong corroboration.

This is stronger than Test 2 because the evidence comes from different route paths.

Test 4 — Multiple routes, different roads
Route A → R1 → P1

Route B → R2 → no observation
Expected

Route B provides no negative evidence about P1.

Because B never travelled on R1.

This must not happen:

Bus B didn't detect P1
→ pothole probably false
GROUP 2 — ROUTE OVERLAP
Test 5 — Two routes partially overlap
Route A → R1 → R2 → R3

Route B → R3 → R4 → R5

Pothole P1 is on R3.

Both routes detect it.

Expected
P1
↓
2 route sources
↓
strong corroboration
Test 6 — Routes overlap but only one bus actually passes
Route A covers R3
Route B covers R3

Today:
A1 → R3
B1 → cancelled

P1 detected by A1.

Expected

Do not say:

Route B failed to confirm.

Instead:

Route B
Expected opportunity = YES
Actual opportunity = NO
Test 7 — Route scheduled to cover road but bus diverted
Normal:
A → R1 → R2 → R3

Today:
A → R1 → R2 → diversion → R5

P1 is on R3.

Expected

No observation from A on R3 should not reduce P1 confidence.

Test 8 — Route passes road but camera unavailable
Bus A1
GPS → R3

Camera:
OFFLINE
Expected
Road R3
Bus passed = YES
Sensing opportunity = NO

Again, no negative evidence.

GROUP 3 — POSITIVE POTHOLE CONFIRMATION
Test 9 — One pothole, three routes
A → P1 ✓
B → P1 ✓
C → P1 ✓

All good-quality observations.

Expected
P1 → HIGH CONFIDENCE
Test 10 — One pothole, different directions
A → R1 → P1
B ← R1 ← P1
Expected

Stronger evidence because the pothole is observed from opposite directions.

Test 11 — One pothole, different viewpoints
Bus A → front view → P1
Bus B → different viewpoint → P1
Expected

Strong corroboration.

This is useful against visual artifacts that only appear from one camera angle.

Test 12 — One pothole, different days
Monday     → P1
Tuesday    → P1
Wednesday  → P1
Expected
Persistence = HIGH
Test 13 — One pothole, different routes, different days
Monday:
Route A → P1

Tuesday:
Route B → P1

Wednesday:
Route C → P1
Expected

Very strong temporal + route diversity.

GROUP 4 — FALSE POSITIVES
Test 14 — Shadow
Camera → "pothole"

But:

Temporal consistency = poor
Other buses = no detection
History = no detection
Expected
P1 → REJECT
Test 15 — Road patch

Camera sees dark repaired asphalt.

AI → pothole 0.90

Other buses:

No detection
Expected

Pothole confidence should decrease.

Test 16 — Manhole

Camera classifies manhole as pothole.

Another classifier says:

manhole = 0.94
Expected
Pothole → rejected
Manhole → candidate
Test 17 — Water puddle

Camera:

pothole = 0.85

Weather:

heavy rain

Other buses:

waterlogging detected
Expected
Pothole hypothesis ↓
Waterlogging hypothesis ↑
Test 18 — Same false object detected by several buses
A → pothole
B → pothole
C → pothole

But all see the same road marking.

Expected

System should not blindly increase confidence.

This tests correlated errors.

GROUP 5 — ROUTE-BASED NEGATIVE EVIDENCE
Test 19 — One bus says pothole, one bus doesn't
A → P1 ✓
B → P1 ✗
Expected

Need to inspect B's observation quality.

Not immediately reject.

Test 20 — B never travelled there
A → R1 → P1 ✓

B → R2
Expected

B contributes zero evidence about P1.

Test 21 — B travelled there but camera blocked
A → P1 ✓

B → R1
Camera blocked
Expected

B = unusable observation, not negative evidence.

Test 22 — B travelled there at night
A → P1 ✓
B → R1 → no detection

B has very poor visibility.

Expected

Weak negative evidence.

Test 23 — B travelled there in daylight with clear visibility
A → P1 ✓
B → R1 → no detection

Good image quality.

Expected

P1 confidence should decrease somewhat.

Test 24 — Five high-quality buses don't detect it
A → no
B → no
C → no
D → no
E → no

All:

correct road
daylight
clear camera
good viewpoint.
Expected

Strong negative evidence.

Potentially:

Pothole → rejected

depending on calibration.

GROUP 6 — SAME ROUTE VS DIFFERENT ROUTES
Test 25 — Four buses, one route
Route A:
A1 ✓
A2 ✓
A3 ✓
A4 ✓
Expected

Strong evidence, but correlated.

Test 26 — Four buses, four routes
A ✓
B ✓
C ✓
D ✓
Expected

Greater evidence diversity.

Test 27 — Same bus repeatedly
A1:
Monday ✓
Tuesday ✓
Wednesday ✓
Thursday ✓
Expected

Persistence increases.

But independence should remain limited.

Test 28 — Four different buses, four routes, four days
Monday:
A1 ✓

Tuesday:
B1 ✓

Wednesday:
C1 ✓

Thursday:
D1 ✓
Expected

Very strong corroboration.

GROUP 7 — TWO POTHOLES
Test 29 — Two potholes far apart
R1:
P1 -------- 200m -------- P2
Expected

Two independent events.

Test 30 — Two potholes close together
P1 --- 15m --- P2
Expected

System should keep them separate if spatial resolution allows.

Test 31 — GPS error makes two potholes overlap

Actual:

P1 = 20m
P2 = 50m

GPS error:

±30m
Expected

System should represent location uncertainty, rather than confidently merging them.

GROUP 8 — GPS / MAP MATCHING
Test 32 — Perfect GPS
GPS → correct road
Expected

Normal association.

Test 33 — GPS shifted 10m
Expected

Still map-match to correct segment.

Test 34 — GPS shifted to adjacent road
Expected

System detects localization uncertainty.

It shouldn't confidently attach P1 to the wrong road.

Test 35 — GPS temporarily unavailable
Video → pothole
GPS → missing for 3 seconds
Expected

Use trajectory interpolation / uncertainty where possible.

Do not discard the entire observation automatically.

GROUP 9 — TIME
Test 36 — Same pothole within seconds
10:32:01 → P1
10:32:02 → P1
10:32:03 → P1
Expected

These should be treated as one observation sequence, not three independent potholes.

Test 37 — Same pothole 20 minutes later

Different bus.

Expected

Same road event if spatial association supports it.

Test 38 — Same location 1 month later
Expected

Likely a new observation of the same persistent location, but the system should maintain temporal history rather than treat it as one continuous observation.

GROUP 10 — POTHOLE LIFECYCLE
Test 39 — Appears and persists
Day 1 → ✓
Day 2 → ✓
Day 3 → ✓
Expected
PERSISTENT
Test 40 — Appears once and disappears
Day 1 → ✓
Day 2 → ✗
Day 3 → ✗
Day 4 → ✗
Expected

Could be:

false positive
temporary obstruction
repaired defect

Status should remain uncertain unless additional evidence resolves it.

Test 41 — Pothole → repair → normal road
Day 1 → P1
Day 2 → P1
Day 3 → P1

Repair

Day 4 → normal
Day 5 → normal
Expected
DETECTED
 ↓
PERSISTENT
 ↓
REPAIRED
 ↓
RESOLVED
Test 42 — Pothole disappears then returns
Week 1 → P1
Week 2 → P1
Repair
Week 3 → normal
Week 5 → P1
Expected
P1
 ↓
repaired
 ↓
reappeared

This is valuable infrastructure intelligence.

GROUP 11 — WEATHER
Test 43 — Dry weather
Pothole detection
+
dry weather
Expected

Normal interpretation.

Test 44 — Heavy rain
Pothole detection
+
heavy rain
Expected

Pothole interpretation becomes less certain if the visual evidence could actually be water.

Test 45 — Rain stops, same location still detected
Rain:
P1 uncertain

Next morning:
P1 detected
Expected

Pothole hypothesis strengthens.

GROUP 12 — CIVIC DATA
Test 46 — Bus + civic complaint
Bus → P1
Citizen → road damage

Same location.

Expected

Independent supporting evidence.

Test 47 — Civic complaint but buses see nothing
Citizen → pothole
Bus A → normal
Bus B → normal
Bus C → normal
Expected

Keep as candidate, not confirmed.

Test 48 — Civic complaint is wrong
Citizen → P1
10 buses → normal
High-quality observations
Expected

Civic evidence loses weight.

GROUP 13 — TRAFFIC AND PRIORITY
Test 49 — High-confidence pothole, low traffic
Confidence = 0.95
Traffic = low
Expected

High detection confidence, but relatively lower priority.

Test 50 — Medium-confidence pothole, high traffic
Confidence = 0.75
Traffic = very high
Expected

Potentially high priority for investigation.

Test 51 — Pothole near school
Pothole
+
school
+
high pedestrian exposure
Expected

Priority increases.

Test 52 — Pothole on isolated road
Pothole
+
very low traffic
+
low pedestrian exposure
Expected

Lower priority despite high confidence.

GROUP 14 — ROUTE FREQUENCY
Test 53 — Road observed 100 times/day
Expected opportunities = 100
Valid observations = 95
Expected

High coverage.

Test 54 — Road observed twice/day
Expected = 2
Observed = 2
Expected

Coverage can be 100%, but absolute evidence volume is low.

This is an important distinction.

Test 55 — Road expected 50 observations, only 10 happen
Expected = 50
Actual = 10
Expected
Coverage = LOW

Don't treat absence of detections as strong negative evidence.

GROUP 15 — CAMERA QUALITY
Test 56 — Clear daylight
Good visibility
Good viewpoint
Good image quality
Expected

High-quality evidence.

Test 57 — Heavy blur
Pothole confidence = 0.92
Blur = extreme
Expected

Raw model confidence should be discounted.

Test 58 — Glare
Pothole = 0.89
Sun glare = severe
Expected

Evidence quality reduced.

Test 59 — Truck blocks pothole
Bus passes R1
Truck blocks road
Expected

No meaningful negative evidence.

GROUP 16 — CORRELATED ERROR
Test 60 — Same model, same camera, same route
A1 ✓
A2 ✓
A3 ✓

All have identical hardware/model characteristics.

Expected

Confidence increases, but cautiously.

Test 61 — Different routes, same AI model
A ✓
B ✓
C ✓

Better spatial diversity but still model-correlated.

Expected

Some correlation remains.

Test 62 — Different routes + different camera types
A → Camera X ✓
B → Camera Y ✓
C → Camera Z ✓
Expected

Much stronger source diversity.

Test 63 — Camera evidence + civic report + historical evidence

Three different evidence types agree.

Expected

Strong corroboration.

This is exactly the kind of scenario our fusion layer should exploit.

GROUP 17 — ROUTE CHANGE / CITY DYNAMICS
Test 64 — Construction diversion

Road R3 normally has:

Route A
Route B
Route C

Today all three are diverted.

Expected
R3 coverage = 0

The system should know why.

Test 65 — New route added

Route D starts covering R3.

Expected

Coverage model updates.

Test 66 — Route discontinued

Route B stops operating.

Expected

Expected observation opportunities decrease.

Test 67 — Bus replaced
Bus B1 → retired
Bus B2 → replaces B1
Expected

Route coverage remains, bus identity changes.

GROUP 18 — VERY IMPORTANT EDGE CASES
Test 68 — Pothole exists but no bus ever passes
Road R9
Routes = 0
Pothole = real
Expected

System should say:

UNOBSERVED ROAD

not:

ROAD IS CLEAR

This is one of the most important cases.

Test 69 — Pothole exists but camera faces elsewhere
Bus passes R9
Camera → side/rear
Pothole → front
Expected

No valid observation.

Test 70 — Pothole exists outside camera field of view

Same principle.

Expected

No negative evidence.

Test 71 — Camera detects pothole on wrong road because of GPS error
Expected

Potential event:

Pothole detected
Location uncertain

rather than confidently assigning it to the wrong road.

Test 72 — Two routes use same physical bus
Bus A1
morning → Route A
afternoon → Route B
Expected

Do not treat route identity as bus identity.

Observation source is:

Bus A1 + Trip ID + Route ID + timestamp
GROUP 19 — THE HARDEST CASES

These are the cases I would really want in our final evaluation.

Test 73 — Strong initial detection, strong contradiction
Camera → pothole 0.94

Other buses → no detection
Historical → normal
Weather → heavy rain
Civic → waterlogging
Expected

Pothole confidence decreases significantly.

Test 74 — Weak initial detection, strong corroboration
Camera → pothole 0.62

Bus B → 0.87
Bus C → 0.84

History → persistent
Weather → dry
Expected

Overall belief increases.

This tests whether the system can rescue a weak initial observation.

Test 75 — High confidence, low coverage
Camera → 0.95
But:
only one bus
only one route
only one observation
Expected
Detection confidence = high
Evidence coverage = low
Overall confirmation = limited
Test 76 — Low confidence, high coverage
Camera → 0.65

100 good-quality buses
same road
all independently fail to confirm
Expected

Pothole hypothesis should decrease.

Test 77 — High agreement, low independence
20 buses
same route
same camera
same model
same environmental conditions
Expected

Do not interpret as 20 independent confirmations.

Test 78 — Moderate agreement, high independence
4 buses
4 routes
3 camera types
2 directions
different times
Expected

Potentially stronger evidence than Test 77 despite fewer buses.

This is an excellent experiment for our research claim.

GROUP 20 — THE "CAN WE TRUST OURSELF?" TEST
Test 79 — System should confirm itself
Initial:
Pothole

Evidence:
3 routes
5 buses
3 days
clear weather
good visibility
Expected
CONFIRMED
Test 80 — System should reject itself
Initial:
Pothole 0.95

Evidence:
shadow
poor temporal consistency
10 buses see normal road
historical normal
Expected
REJECTED
Test 81 — System should admit uncertainty
Initial:
Pothole 0.75

Evidence:
one bus
night
GPS uncertainty
no history
Expected
UNCERTAIN
Test 82 — System should change its mind
Initial:
Pothole

New evidence:
heavy rain
waterlogging
no persistence
Expected
Pothole ↓
Waterlogging ↑
The full scenario we're actually trying to simulate

We can now create a city simulation:

                         CITY
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
     ROUTE A           ROUTE B           ROUTE C
        │                 │                 │
   ┌────┼────┐       ┌────┼────┐       ┌────┼────┐
   ↓    ↓    ↓       ↓    ↓    ↓       ↓    ↓    ↓
  B1   B2   B3      B4   B5   B6      B7   B8   B9
   │    │    │       │    │    │       │    │    │
   └────┴────┼───────┴────┴────┼───────┴────┴────┘
              ↓
          ROAD NETWORK
              │
       ┌──────┼────────┐
       ↓      ↓        ↓
      R1     R2       R3
              │
            P1
              │
              ↓
       OBSERVATIONS
              │
              ↓
      EVIDENCE ENGINE
              │
       ┌──────┼──────┐
       ↓      ↓      ↓
    SUPPORT  NONE  CONTRADICT
       │      │      │
       └──────┼──────┘
              ↓
       UPDATED BELIEF
              ↓
       ROAD SEGMENT STATE
              ↓
           PRIORITY
And every road should have a coverage record

For example:

Road	Routes	Buses expected	Buses passed	Valid observations	Good-quality observations	Pothole detections
R1	A, B	42	39	36	31	4
R2	A	12	12	10	9	0
R3	A, B, C	80	75	69	63	18
R4	C	4	1	1	1	1
R5	None	0	0	0	0	0

And now the system can make a much more intelligent statement:

R3

75 buses actually passed, 63 provided high-quality observations, and 18 observations support a persistent pothole.

That's meaningful.

R5

No bus route currently provides sensing coverage.

That's also meaningful.

But it must never say:

“No pothole detected on R5.”

Because R5 was never observed.

This gives us 5 different states for a road

Instead of only:

POTHOLE
NO POTHOLE

we should have:

1. CONFIRMED DEFECT
2. PROBABLE DEFECT
3. UNCERTAIN
4. PROBABLY CLEAR
5. UNOBSERVED / INSUFFICIENT COVERAGE

That fifth state is extremely important.

Because:

No evidence is not the same as evidence of absence.

The final test framework

So our complete testing space becomes:

                 ROAD
                   │
        ┌──────────┼───────────┐
        ↓          ↓           ↓
      ROUTES      BUSES      COVERAGE
        │          │           │
        └──────────┼───────────┘
                   ↓
              OBSERVATION
                   ↓
          ┌────────┼────────┐
          ↓        ↓        ↓
       SUPPORT   CONTRADICT  NONE
          │        │        │
          └────────┼────────┘
                   ↓
             TIME + SPACE
                   ↓
            SOURCE QUALITY
                   ↓
            CORRELATION
                   ↓
             EVIDENCE FUSION
                   ↓
             ROAD CONDITION
                   ↓
                PRIORITY

And the ultimate experiment is not just “does DRISHTI detect potholes?”

It's:

Across roads with different route coverage, bus availability, observation quality, route overlap, temporal history, source diversity, and contradictory evidence, does evidence-aware fusion make better decisions than camera-only detection and naive counting?

That's the experiment that can genuinely test our hypothesis rather than merely demonstrate the system.

so this is the gods eye thing 

Yes — conceptually, this is the “God’s Eye” idea your senior was pointing toward, but we should define it carefully.

Not literally God’s Eye as in a system that sees everything. The useful interpretation is:

A city-wide intelligence layer that builds an evolving picture of what is happening across roads by combining observations from many moving buses and other data sources.

Think of the difference

Normal bus AI:

Bus A
  ↓
Camera
  ↓
Pothole detected
  ↓
Alert

Our “God’s Eye” concept:

             CITY
              │
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 Route A   Route B   Route C
    ↓         ↓         ↓
  Buses     Buses     Buses
    │         │         │
    └─────────┼─────────┘
              ↓
        MANY OBSERVATIONS
              ↓
       WHERE / WHEN / WHO
              ↓
      EVIDENCE + COVERAGE
              ↓
     SUPPORT / CONTRADICT
              ↓
       ROAD-SEGMENT STATE
              ↓
       CITY-WIDE PICTURE

So the “eye” isn't the camera.

The camera is just one of the eyes.

The real intelligence is the layer that asks:

What is happening across the city, where do we have evidence, how reliable is that evidence, what contradicts it, and what should we believe right now?

And the route idea is what makes it city-wide

Imagine:

              CITY ROAD NETWORK

       R1 ───────── R2 ───────── R3
        │            │            │
       R4 ───────── R5 ───────── R6
        │            │            │
       R7 ───────── R8 ───────── R9

Different buses cover different portions:

Bus A → R1 R2 R5 R8
Bus B → R2 R3 R6 R9
Bus C → R1 R4 R5 R7
Bus D → R3 R5 R8

The system continuously builds:

R1 → observed by A,C
R2 → observed by A,B
R3 → observed by B,D
R4 → observed by C
R5 → observed by A,C,D
...

Now DRISHTI knows not just what was detected, but:

which parts of the city are being observed, how frequently, by whom, and with what quality.

That's the beginning of the “God's Eye” effect.

But there's an even better way to describe it

I wouldn't put “God's Eye” in the actual SIH PPT.

It sounds cool, but it's vague and can imply unrealistic surveillance.

For the technical presentation, I'd call it something like:

City-Wide Mobile Urban Intelligence Layer

or:

Fleet-Based Urban Evidence Intelligence

And internally, you can think of it as:

“God's Eye for the road network.”

The really powerful part

The system doesn't simply create a map of detections.

It creates a map of belief and uncertainty.

For example:

ROAD R1
████████
Confirmed pothole
Confidence: 94%
Coverage: HIGH
ROAD R2
████████
Possible pothole
Confidence: 61%
Coverage: LOW
ROAD R3
████████
No defect observed
Coverage: HIGH
ROAD R4
████████
UNOBSERVED
No bus coverage

Those are four completely different situations.

That's what makes the system intelligent.

So the complete vision becomes
             PUBLIC TRANSPORT FLEET
                       │
              ┌────────┴────────┐
              ↓                 ↓
          OBSERVATIONS       ROUTES
              │                 │
              ↓                 ↓
       What did we see?    Where could
                           we see?
              │                 │
              └────────┬────────┘
                       ↓
                CITY ROAD GRAPH
                       ↓
              EVIDENCE ENGINE
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       SUPPORT      CONTRADICT    MISSING
       EVIDENCE      EVIDENCE     EVIDENCE
          │            │            │
          └────────────┼────────────┘
                       ↓
              CITY-WIDE ROAD STATE
                       ↓
             PRIORITY / ACTION
                       ↓
                 ICCC / EQUINOX

So yes: the “God's Eye” inspiration maps very well to what we're building — but the actual technical idea is a fleet-wide, route-aware, evidence-fusion intelligence layer that continuously builds the state of the urban road network.

And that's considerably more defensible than saying “we made God's Eye for buses.”

so give me final vedirict
Final Verdict — DRISHTI

Yes. We have a real direction now. But the winning version is not “AI pothole detection on buses” and not literally “God’s Eye.”

The defensible concept is:

DRISHTI is a fleet-wide, route-aware urban evidence intelligence layer that turns public buses into mobile sensing nodes and continuously builds a confidence-aware state of the city’s road network.

The core loop
BUS OBSERVES
     ↓
"I THINK THIS IS A POTHOLE"
     ↓
        DOUBT
     ↓
CHECK OTHER EVIDENCE
     │
     ├─ Same-video consistency
     ├─ Other buses
     ├─ Other routes
     ├─ Different directions/viewpoints
     ├─ Historical observations
     ├─ GPS / map consistency
     ├─ Weather
     ├─ Civic reports
     └─ Traffic / road context
     ↓
SUPPORT / CONTRADICT / INSUFFICIENT
     ↓
CORRELATION-AWARE FUSION
     ↓
UPDATED BELIEF
     ↓
ROAD-SEGMENT STATE
     ↓
PRIORITY
     ↓
ICCC / EQUINOX
What makes the idea meaningful

The system knows three things simultaneously:

1. What happened?

“A pothole was detected.”

2. How much evidence do we have?

“Three buses from two routes observed it, but one observation had poor visibility.”

3. Were we actually capable of observing it?

“This road normally receives 40 bus passes/day, but only 8 usable observations occurred today.”

That third part is crucial.

No observation is not the same as no pothole.

The final research hypothesis

Can route-aware, uncertainty- and correlation-aware evidence fusion improve the reliability of road-condition decisions compared with independent detection and naive multi-observation aggregation?

That's the hypothesis we should actually test.

Not:

“Can YOLO detect potholes?”

Not:

“Can buses monitor roads?”

Those are already established.

The final experimental setup

We compare:

                SAME TEST CASES
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     CAMERA ONLY   NAIVE FUSION   DRISHTI
          │           │           │
          └───────────┼───────────┘
                      ↓
              COMPARE RESULTS

And deliberately include:

genuine potholes
false potholes
shadows
waterlogging
road patches
GPS errors
poor visibility
blocked cameras
one bus vs many buses
same route vs different routes
same bus vs different buses
overlapping routes
routes that don't cover the road
route diversions
cancelled trips
low-coverage roads
high-coverage roads
persistent defects
repaired defects
reappearing defects
contradictory evidence
correlated false detections
independent corroboration
high confidence but low impact
moderate confidence but high impact
completely unobserved roads

So we're trying to break the system, not manufacture evidence that makes it look good.

What the final product becomes

Think of the city as a giant road graph:

             CITY ROAD NETWORK

 R1 ───── R2 ───── R3
 │         │        │
 R4 ───── R5 ───── R6
 │         │        │
 R7 ───── R8 ───── R9

Different buses continuously observe different portions:

Route A → R1 R2 R5 R8
Route B → R2 R3 R6 R9
Route C → R1 R4 R5 R7
Route D → R3 R5 R8

DRISHTI maintains the state of each segment:

R1 → PROBABLY CLEAR
R2 → HIGH COVERAGE / CLEAR
R3 → CORROBORATED POTHOLE
R4 → LOW COVERAGE
R5 → PERSISTENT ROAD DEFECT
R6 → UNCERTAIN
R7 → UNOBSERVED
R8 → REPAIRED
R9 → POSSIBLE WATERLOGGING

That is the “God's Eye” effect.

But technically, it's better described as:

A city-wide mobile urban intelligence layer.

And the most important strategic decision
Don't build everything.

For the Grand Finale prototype, I would make the research spine:

VIDEO
+
GPS / TIME
+
ROUTES
+
ROAD SEGMENTS
+
HISTORICAL OBSERVATIONS
        ↓
EVIDENCE FUSION
        ↓
POTHOLE / ROAD CONDITION
        ↓
PRIORITY

Then add weather, civic reports, traffic, etc. as supporting evidence.

IMU/CAN can remain an optional future evidence source. We don't need new hardware to prove the core hypothesis.

Final judgment
Question	Verdict
Is bus-based road sensing new?	No
Is AI pothole detection new?	No
Is GPS + camera + GIS new?	No
Is multi-bus corroboration alone new?	No
Is route-aware coverage important?	Yes
Is uncertainty important?	Yes
Is correlated evidence important?	Yes
Can we test this without new hardware?	Yes
Can LiRA-CD help research the vehicle-sensing component?	Yes, with bus-specific validation later
Can we construct adversarial positive/negative experiments?	Yes
Is the hypothesis falsifiable?	Yes
Is the broad “God's Eye” idea itself novel?	No — don't claim that
Is the evidence-aware, route-aware fusion hypothesis worth pursuing?	Yes
Is it guaranteed to outperform baselines?	No — that's exactly what we must test
The one sentence I'd lock in:

DRISHTI doesn't simply ask “What did the bus see?” — it asks “What do we believe is happening on this road, what evidence supports that belief, what contradicts it, and did we have enough opportunity to observe the road in the first place?”

That is our research direction.