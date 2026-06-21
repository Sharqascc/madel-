# Speed Safety Score Definition

This document defines the formulas, weights, thresholds, and interpretation rules used to generate the segment-level `speed_safety_score` and `priority_label`.

## Purpose

The score supports proactive screening of road segments where posted speed limits may be inconsistent with Safe System principles. It combines structural speed alignment, operating speed behavior, vulnerable road user exposure, and roadway context into a single interpretable index.

## Output Fields

| Field | Meaning |
|---|---|
| `posted_speed_limit_kph` | Posted speed limit associated with the segment. |
| `safe_system_reference_speed_kph` | Context-sensitive reference speed judged to be safer under the implemented Safe System rules. |
| `speed_limit_gap_score` | Structural alignment score between posted speed and reference speed, scaled 0-100 where higher is safer. |
| `operating_speed_score` | Behavioral speed-compliance score, scaled 0-100 where higher is safer. |
| `vru_exposure_score` | Vulnerable road user exposure score after inversion, scaled 0-100 where higher is safer. |
| `context_score` | Road-context safety score after inversion, scaled 0-100 where higher is safer. |
| `speed_safety_score` | Final weighted composite score on a 0-100 scale where higher is safer. |
| `priority_label` | Action-oriented label used to prioritize review. |

## Score Direction

All component scores are normalized to a 0-100 scale.

- `100` = strongest alignment with the safer target condition.
- `0` = strongest indication of systemic risk or misalignment.
- Higher scores indicate safer conditions.
- Lower scores indicate higher priority for intervention or policy review.

## Composite Formula

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
| Speed limit gap | \(w_{gap}\) | 0.35 | Structural policy alignment between posted speed and Safe System reference speed. |
| Operating speed | \(w_{operating}\) | 0.20 | Behavioral non-compliance layer. |
| VRU exposure | \(w_{vru}\) | 0.25 | Severity amplifier for pedestrians, cyclists, and powered two-wheelers. |
| Context | \(w_{context}\) | 0.20 | Road environment and conflict potential. |

\[
0.35 + 0.20 + 0.25 + 0.20 = 1.00
\]

## Reference Speeds

The implementation uses three baseline reference speeds:
- 30 km/h for mixed-VRU environments;
- 50 km/h for side-conflict environments;
- 70 km/h for lower-conflict or head-on-dominant environments.

The exact assignment is performed by rule-based logic over contextual variables such as VRU presence, school or market activity, urban setting, intersection density, and roadway separation.

## Component Formulas

### 1. Speed Limit Gap Score

\[
\Delta_{limit} = \max(0,\; V_{posted} - V_{safe})
\]

\[
S_{gap} = \max(0,\; 100 - (\Delta_{limit}/40)\cdot100)
\]

A zero positive gap yields 100. A 40 km/h or greater positive gap yields 0.

### 2. Operating Speed Score

\[
\Delta_{excess} = \max(0,\; V_{operating} - V_{posted})
\]

\[
S_{operating} = \max(0,\; 100 - (\Delta_{excess}/30)\cdot100)
\]

A compliant operating speed yields 100. A 30 km/h or greater excess yields 0.

### 3. VRU Exposure Score

Raw VRU risk is computed as:

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

The safety-oriented score is:

\[
S_{vru} = \max(0,\; 100 - R_{vru})
\]

Higher unmanaged VRU exposure reduces the score.

### 4. Context Score

Raw context risk is computed as:

\[
R_{context} =
30(Urban) +
25(IntersectionDensity) +
25(RoadsideActivity) +
20(NonSeparatedTraffic)
\]

The safety-oriented score is:

\[
S_{context} = \max(0,\; 100 - R_{context})
\]

More conflict-prone context reduces the score.

## Priority Labels

| Final Score Band | Priority Label | Meaning |
|---|---|---|
| 80.00 – 100.00 | `aligned` | Broadly aligned with the implemented Safe System logic. |
| 60.00 – 79.99 | `monitor` | Some concerns exist; continue screening and analyst review. |
| 40.00 – 59.99 | `review` | Meaningful misalignment is present and the segment warrants attention. |
| 0.00 – 39.99 | `high_priority_review` | High-risk segment requiring urgent attention or intervention. |

## Escalation Override

The implementation applies a deterministic escalation override to avoid severe VRU risk being masked by stronger scores in other components.

A segment is forced to `high_priority_review` when:
- `vru_exposure_score < 50`,
- `safe_system_reference_speed_kph <= 30`,
- and `posted_speed_limit_kph >= 60`.

## Example

For a segment with:
- `posted_speed_limit_kph = 60`
- `safe_system_reference_speed_kph = 30`
- `operating_speed_kph = 68`
- `vru_exposure_score = 5`
- `context_score = 0`

The component scores include:
- `speed_limit_gap_score = 25.00`
- `operating_speed_score = 73.33`

The composite score is:

\[
0.35(25.00) + 0.20(73.33) + 0.25(5.00) + 0.20(0.00) = 24.67
\]

This maps to `high_priority_review`.

## Implementation Notes

- `configs/scoring.yaml` is the tunable configuration source for production values.
- `src/ai4saferroads/speed_safety_score.py` is the authoritative implementation.
- Reviewer-facing outputs should preserve both component scores and the final score for interpretability.
