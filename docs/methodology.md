# Methodology

This repository operationalizes a Safe System-oriented screening method for identifying road segments where speed environments may be incompatible with severe-injury prevention goals.

## Conceptual basis

The method assumes that survivable speed is context-dependent. Segments with high pedestrian activity, cyclist activity, school influence, market activity, or strong roadside conflict should be evaluated against lower reference speeds than controlled-access or lower-conflict corridors.

## Analytical structure

The pipeline produces a segment-level `speed_safety_score` on a 0-100 scale where higher values indicate safer alignment. The score is a weighted composite of four components:

\[
\text{speed\_safety\_score} =
0.35 \cdot S_{gap} +
0.20 \cdot S_{operating} +
0.25 \cdot S_{vru} +
0.20 \cdot S_{context}
\]

These weights are loaded from `configs/scoring.yaml`, enabling transparent calibration.

## Reference speed logic

The method derives a `safe_system_reference_speed_kph` from road context. Mixed-VRU environments are assigned 30 km/h, side-conflict environments 50 km/h, and lower-conflict/head-on environments 70 km/h.

This is implemented as rule-based inference rather than black-box prediction so reviewers can inspect and audit every branch.

## Component construction

- `speed_limit_gap_score` penalizes posted speeds above the derived Safe System reference speed.
- `operating_speed_score` penalizes observed operating speeds above the posted speed limit.
- `vru_exposure_score` converts VRU risk indicators into an inverted safety score.
- `context_score` converts urban-form and conflict indicators into an inverted safety score.

All component scores are clipped to the 0-100 range.

## Escalation rule

A weighted average can sometimes smooth away dangerous high-VRU/high-speed combinations. To prevent this, the model includes a rule-based escalation override: if VRU risk is high, the reference speed environment is mixed-VRU, and the posted speed remains high, labels are escalated toward `high_priority_review`.

## Reproducibility

The repository is runnable without NDA-protected data because the synthetic data generator creates plausible road-segment attributes and coordinates. This allows reviewers to execute the full scoring and visualization workflow immediately.
