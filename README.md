# AI for Safer Roads — Phase 1 Submission

## Overview
This repository contains a Phase 1 analytical workflow for road-segment speed safety assessment in Thailand and Maharashtra, India.

The project evaluates whether posted speed limits are aligned with Safe System principles, identifies road segments where vulnerable road user risk is elevated, and produces transparent, reproducible, reviewer-friendly outputs for prioritization and inspection.

## Deliverable Scope
This repository is submitted for the **Analytical model** deliverable of the ADB **AI for Safer Roads Innovation Challenge**.

It includes:
- Documented code and methodology
- A transparent and interpretable speed safety scoring approach
- Reproducible batch processing scripts
- Ranked summary outputs
- Scored tabular and geospatial artifacts
- Interactive HTML map outputs for review

## Study Areas
- Thailand
- Maharashtra, India

## Repository Contents
- `docs/score_definition.md` — score definition and methodology
- `configs/scoring.yaml` — configurable scoring thresholds and weights
- `src/ai4saferroads/speed_safety_score.py` — scoring implementation
- `scripts/01_prepare_data.py` — data preparation pipeline
- `scripts/02_score_segments.py` — batch scoring pipeline
- `outputs/summary/` — ranked reviewer-first summary outputs
- `outputs/viz/` — visualization-ready layers
- `outputs/scored/` — full scored artifacts for inspection
- `outputs/maps/` — interactive HTML maps

## Method Summary
The workflow computes a segment-level **Speed Safety Score** using prepared road-segment attributes and Safe System-oriented logic.

The model is intentionally interpretable and policy-oriented. It is designed to support **speed limit review prioritization**, not to claim direct crash prediction.

The score evaluates:
- Whether posted speed limits are aligned with Safe System reference speeds
- Whether operating speeds exceed the posted speed environment
- Whether vulnerable road user exposure is elevated
- Whether road context suggests higher conflict risk

## Inputs Used
Key fields used in scoring include:
- `posted_speed_limit_kph`
- `operating_speed_kph`
- `road_type`
- `area_type`
- `pedestrian_presence`
- `cyclist_presence`
- `ptw_presence`
- `urban_flag`
- `intersection_density_flag`

Only segments with `score_eligible_flag == 1` are included in the official scored output.

## Speed Safety Score
The score combines four interpretable subscores:
1. Speed limit gap score
2. Operating speed score
3. VRU exposure score
4. Context score

The final weighted score is clipped to the range 0–100 and mapped to priority labels:
- `aligned`
- `monitor`
- `review`
- `high_priority_review`

See `docs/score_definition.md` for the full methodology.

## Key Outputs

### Reviewer-first outputs
- `outputs/summary/top_100_riskiest_segments_combined.csv`
- `outputs/summary/top_20_per_country.csv`
- `outputs/maps/thailand_speed_safety_map.html`
- `outputs/maps/maharashtra_speed_safety_map.html`

### Full scored artifacts
- `outputs/scored/thailand_scored.csv`
- `outputs/scored/thailand_scored.geojson`
- `outputs/scored/maharashtra_scored.csv`
- `outputs/scored/maharashtra_scored.geojson`

## Repository Structure
```text
docs/
configs/
scripts/
src/
outputs/
  summary/
  viz/
  scored/
  maps/
```

## Setup

### Option 1: Google Colab
Clone the repository in Colab:
```bash
git clone https://github.com/Sharqascc/madel-.git
cd madel-
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Local environment
```bash
git clone https://github.com/Sharqascc/madel-.git
cd madel-
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run

### Step 1: Prepare data
```bash
python scripts/01_prepare_data.py
```

### Step 2: Score segments
```bash
python scripts/02_score_segments.py
```

## Reproducibility Notes
The repository includes committed Phase 1 outputs for reviewer access and reproducibility. Re-running the scripts should regenerate the summary tables, scored outputs, and map artifacts, subject to the same prepared inputs and configuration.

## Reviewer Guidance
Recommended review order:
1. `docs/score_definition.md`
2. `outputs/summary/top_100_riskiest_segments_combined.csv`
3. `outputs/summary/top_20_per_country.csv`
4. `outputs/maps/thailand_speed_safety_map.html`
5. `outputs/maps/maharashtra_speed_safety_map.html`
6. `outputs/scored/` full artifacts for auditability and inspection

## Evaluation Methodology
This repository uses a transparent rule-based evaluation methodology centered on Safe System alignment and elevated vulnerable road user risk.

The methodology documents:
- input assumptions
- Safe System reference speeds
- scoring logic
- weighting
- threshold bands
- escalation logic
- priority mapping

This supports reproducible and interpretable prioritization for transport policy workflows.

## Notes
- The model is rule-based and intentionally interpretable.
- The outputs are designed for policy review and prioritization.
- Interactive HTML maps are included for geospatial inspection.
- The workflow is designed to be transferable to similar road safety contexts.

## Status
Current repository state includes committed Phase 1 outputs, scored reviewer-inspection artifacts, and interactive map deliverables.
