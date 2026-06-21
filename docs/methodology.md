# Methodology

## Overview

This project evaluates whether posted speed limits are plausibly aligned with Safe System principles using a transparent, rule-based scoring approach. The method integrates road-environment context, observed or inferred operating speed behavior, and vulnerable road user exposure into a segment-level screening framework.

## Analytical Objective

The analytical goal is not to estimate crash occurrence directly. Instead, it identifies road segments where current posted speeds appear structurally inconsistent with the severity of conflict likely to occur if a crash happens. This makes the output suitable for network screening, policy triage, and prioritization of more detailed engineering review.

## Safe System Framing

The methodology follows a Safe System logic in which tolerable impact speeds depend on the exposure of vulnerable road users and the dominant conflict type. Environments with frequent pedestrian or cyclist interaction are assigned lower reference speeds than corridors with lower direct exposure or more separation.

The implementation currently uses three reference speed tiers:
- 30 km/h for mixed-VRU environments.
- 50 km/h for side-conflict environments.
- 70 km/h for lower-conflict or higher-separation environments.

## Data Layers

The pipeline is designed to work with the challenge data structure and can ingest the following data categories when available:

- Posted speed limits.
- Operating or proxy speed measures.
- Road-network characteristics such as urban classification, divided status, and intersection density.
- VRU and roadside-activity indicators such as schools, markets, crossings, transit stops, and commercial frontage.
- Segment identifiers and geometry for map output.

## Processing Pipeline

### 1. Prepare segment-level features

Input datasets are harmonized into a segment-level table. Continuous or categorical attributes are standardized into fields used by the scoring functions.

### 2. Derive Safe System reference speed

A rule-based function assigns `safe_system_reference_speed_kph` using context signals that indicate mixed VRU exposure, side-conflict likelihood, and higher-separation conditions.

### 3. Compute component scores

Four sub-scores are calculated on a 0-100 scale where higher is safer:

- `speed_limit_gap_score`
- `operating_speed_score`
- `vru_exposure_score`
- `context_score`

The raw VRU and context risk expressions are inverted so that higher unmanaged risk lowers the final sub-score.

### 4. Compute composite score

The final `speed_safety_score` is a weighted linear combination of the four component scores. This provides a transparent and auditable summary measure rather than a black-box prediction.

### 5. Apply escalation override

A deterministic escalation rule ensures that extremely unsafe mixed-VRU conditions cannot be hidden by relatively stronger values in other components.

### 6. Generate map output

Scored segments are sorted and exported into an HTML visualization artifact to support rapid review of high-priority locations.

## Interpretation

The score should be read as a screening and prioritization tool:
- Higher scores indicate stronger alignment with the implemented Safe System speed logic.
- Lower scores indicate likely misalignment and higher need for intervention review.
- The categorical `priority_label` is intended for operational communication, not as a substitute for engineering diagnosis.

## Transparency and Reproducibility

The approach is intentionally rule-based and interpretable:
- Component weights are stored in configuration.
- Reference-speed assignment is deterministic.
- Threshold bands are explicit.
- VRU escalation conditions are explicit.
- Unit tests verify critical logic branches.

This design supports reproducibility, policy interpretability, and straightforward recalibration if challenge evaluators or local authorities require parameter updates.

## Limitations

This methodology is a screening framework, not a full crash reconstruction or causal inference model. Output quality depends on the completeness and fidelity of segment attributes, particularly operating speed proxies and VRU-related contextual indicators.

Where the input data are sparse, missing, or proxy-based, the output should be treated as an evidence-informed prioritization layer to be complemented by local expert review.

## Recommended Extensions

Potential future enhancements include:
- Calibration against observed crash severity outcomes where permitted.
- More granular conflict typing.
- Separate treatment for school zones, transit corridors, and market streets.
- Confidence scoring for segments with sparse supporting data.
- Spatial smoothing or corridor-level aggregation for policy packaging.
