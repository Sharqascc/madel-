# Methodology

## Objective

This project identifies road segments where posted speeds may be inconsistent with Safe System principles and where vulnerable users may face elevated crash severity risk. The objective is not to predict crashes directly, but to build a transparent screening tool for prioritizing speed-management review.

## Safe System Framing

The methodology assumes that safe posted speeds should depend on the conflict environment rather than roadway speed alone. Segments with pedestrian, cyclist, school, market, or dense urban interaction are assigned lower reference speeds than lower-conflict corridors. This reflects the principle that survivable impact speeds are lower in mixed-use or high-exposure environments.

## Data Layers

The pipeline is designed to work with four broad data layers:

1. Posted and observed speed variables, including posted speed limits and operating speeds.
2. Road environment variables, such as urban setting, separation, and intersection density.
3. Vulnerable road user exposure proxies, such as pedestrian activity, cycling presence, school zones, transit stops, and roadside commercial activity.
4. Segment geometry and location fields needed to preserve a geospatial output.

The synthetic demo data mirrors this structure so the repository remains runnable before restricted challenge data are available.

## Scoring Logic

The analytical model assigns a context-sensitive Safe System reference speed, computes four component scores, and combines them into a weighted safety index. All component scores are oriented so that higher values are safer and lower values indicate more severe misalignment.

This design choice improves interpretability: reviewers can read the score as a safety-alignment index rather than as a penalty count. It also makes map visualization more intuitive because low values correspond to warmer, higher-risk map categories.

## Escalation Logic

A weighted composite can smooth out severe local risks. To prevent that, the pipeline applies a deterministic override for segments that combine high posted speeds with mixed-VRU environments and high unmanaged VRU risk. This ensures that especially hazardous contexts are not hidden by otherwise favorable component values.

## Reproducibility

The repository is structured so the full workflow can be run from scripts:
1. `scripts/01_prepare_data.py`
2. `scripts/02_score_segments.py`
3. `scripts/03_generate_map.py`

Configuration values are externalized through `configs/scoring.yaml`, while the core scoring logic resides in `src/ai4saferroads/speed_safety_score.py`. This separation supports recalibration without changing the analytical structure.

## Demo Data Strategy

Because challenge data may be restricted pending agreement execution, the repository includes synthetic reviewer-friendly data generation. The synthetic data are intentionally stratified to exercise multiple score bands and map categories, allowing reviewers to observe how the model responds to safer and riskier segment profiles.

## Output Products

The pipeline produces:
- a prepared segment dataset,
- a scored segment CSV with component and final scores,
- and an interactive HTML map for segment-level visualization.

Together these outputs support both technical inspection and policy-facing communication.
