# Speed Safety Score Definition

This document defines the component scores, weights, formulas, threshold bands, and interpretation logic used to generate the segment-level `speed_safety_score` and `priority_label`.

## Purpose

The score supports proactive screening of road segments where posted speed limits deviate from Safe System principles. It combines structural speed-limit alignment, operating speed behavior, vulnerable road user exposure, and road context into a transparent composite index.

## Output Fields

| Field | Meaning |
|---|---|
| `posted_speed_limit_kph` | Posted speed limit associated with the segment. |
| `safe_system_reference_speed_kph` | Reference speed judged to be safer for the segment context under Safe System rules. |
| `speed_limit_gap_score` | Measure of posted speed alignment with the reference speed; 100 means fully aligned. |
| `operating_speed_score` | Measure of behavioral speed compliance; 100 means no excess operating speed penalty. |
| `vru_exposure_score` | Measure of unmanaged VRU risk after inversion; 100 means lowest unmanaged VRU risk. |
| `context_score` | Measure of road-context safety after inversion; 100 means lowest contextual risk in the rule set. |
| `speed_safety_score` | Final weighted composite score on a 0-100 scale; higher is safer. |
| `priority_label` | Final action-oriented label for intervention prioritization. |

## Scoring Direction

All component scores are normalized to a 0-100 scale where:
- `100` means strongest alignment with the safer target condition.
- `0` means strongest indication of systemic risk or misalignment.
- Higher final scores indicate better alignment with Safe System speed management.
- Lower final scores indicate higher intervention priority.

## Composite Formula

The final index is calculated as:

\[
\text{speed\_safety\_score} =
w_{gap} \cdot S_{gap} +
w_{operating} \cdot S_{operating} +
w_{vru} \cdot S_{vru} +
w_{context} \cdot S_{context}
\]

Where:
- \(S_{gap}\) = `speed_limit_gap_score`
- \(S_{operating}\) = `operating_speed_score`
- \(S_{vru}\) = `vru_exposure_score`
- \(S_{context}\) = `context_score`

## Weights

| Component | Symbol | Weight | Interpretation |
|---|---|---:|---|
| Speed limit gap | \(w_{gap}\) | 0.35 | Primary policy lever: alignment between posted speed and Safe System reference speed. |
| Operating speed | \(w_{operating}\) | 0.20 | Behavioral layer: captures excess speed beyond the posted limit. |
| VRU exposure | \(w_{vru}\) | 0.25 | Consequence layer: emphasizes severity where vulnerable users are exposed. |
| Context | \(w_{context}\) | 0.20 | Environmental layer: captures urban form and conflict potential. |

\[
0.35 + 0.20 + 0.25 + 0.20 = 1.00
\]

The configuration file `configs/scoring.yaml` is the authoritative source for production tuning.

## Safe System Reference Speeds

The implementation uses three baseline reference speeds:
- 30 km/h for mixed-VRU environments.
- 50 km/h for side-conflict environments.
- 70 km/h for lower-conflict or head-on-dominant environments.

The exact branch logic is implemented in code using contextual indicators such as VRU presence, urban setting, and conflict-related road attributes.

## Component Logic

### Speed Limit Gap Score

The structural speed gap is:

\[
\Delta_{limit} = \max(0,\; V_{posted} - V_{safe})
\]

The component score is:

\[
S_{gap} = \max(0,\; 100 - (\Delta_{limit}/40)\cdot100)
\]

A zero gap yields a score of 100, while a 40 km/h or larger positive gap yields 0.

### Operating Speed Score

The behavioral excess speed is:

\[
\Delta_{excess} = \max(0,\; V_{operating} - V_{posted})
\]

The component score is:

\[
S_{operating} = \max(0,\; 100 - (\Delta_{excess}/30)\cdot100)
\]

A compliant operating speed yields 100, while a 30 km/h or larger excess yields 0.

### VRU Exposure Score

The raw VRU risk expression is:

\[
R_{vru} =
30(Pedestrian) +
20(Cyclist) +
15(PTW) +
15(CrossingDensity) +
10(CommercialFrontage) +
5(TransitStop) +
5(SchoolZone)
\]

The component score is:

\[
S_{vru} = \max(0,\; 100 - R_{vru})
\]

Higher unmanaged VRU exposure reduces the score.

### Context Score

The raw context risk expression is:

\[
R_{context} =
30(Urban) +
25(IntersectionDensity) +
25(RoadsideActivity) +
20(NonSeparatedTraffic)
\]

The component score is:

\[
S_{context} = \max(0,\; 100 - R_{context})
\]

More conflict-prone context reduces the score.

## Priority Labels

| Final Score Band | Priority Label | Meaning |
|---|---|---|
| 80.00 – 100.00 | `aligned` | Broadly aligned with the Safe System logic used in the pipeline. |
| 60.00 – 79.99 | `monitor` | Some safety concerns exist; continue corridor screening and review. |
| 40.00 – 59.99 | `review` | Meaningful misalignment is present and the segment should be reviewed. |
| 0.00 – 39.99 | `high_priority_review` | High-risk segment requiring urgent attention or intervention. |

## Escalation Override

To avoid severe VRU risk being masked by stronger scores in other components, the implementation applies a structural escalation override.

Rule:
- If VRU risk is high (`vru_exposure_score < 50`),
- and the segment is in a mixed-VRU reference-speed environment (`safe_system_reference_speed_kph <= 30`),
- and the posted speed limit remains high (`posted_speed_limit_kph >= 60`),
- then `priority_label` is forced to `high_priority_review`.

## Example

For an urban mixed-VRU segment:
- `posted_speed_limit_kph = 60`
- `safe_system_reference_speed_kph = 30`
- `operating_speed_kph = 68`

Component math:
- `speed_limit_gap_score = 100 - ((60 - 30)/40)*100 = 25.00`
- `operating_speed_score = 100 - ((68 - 60)/30)*100 = 73.33`

If the segment also has:
- `vru_exposure_score = 5.00`
- `context_score = 0.00`

Then the composite score is:

\[
0.35(25.00) + 0.20(73.33) + 0.25(5.00) + 0.20(0.00) = 24.67
\]

This maps directly to `high_priority_review`.

## Implementation Notes

- `configs/scoring.yaml` controls tunable weights, thresholds, and escalation settings.
- `src/ai4saferroads/speed_safety_score.py` remains the authoritative implementation.
- Reviewer-facing outputs should retain both the final score and the component scores for interpretability.
