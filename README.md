AI for Safer Roads — Phase 1 Submission
Overview
This repository contains a Phase 1 analytical workflow for road-segment speed safety assessment in Thailand and Maharashtra, India.

The project evaluates whether posted speed limits are aligned with Safe System principles, identifies road segments where vulnerable road user risk is elevated, and produces transparent, reproducible, reviewer-friendly outputs for prioritization and inspection.

Deliverable Scope
This repository is submitted for the Analytical model deliverable of the ADB AI for Safer Roads Innovation Challenge.

It includes:

Documented code and methodology

A transparent and interpretable speed safety scoring approach

Reproducible batch processing scripts

Ranked summary outputs

Scored tabular and geospatial artifacts

Interactive HTML map outputs for review

Study Areas
Thailand

Maharashtra, India

Repository Contents
docs/score_definition.md — score definition and methodology

configs/scoring.yaml — configurable scoring thresholds and weights

src/ai4saferroads/speed_safety_score.py — scoring implementation

scripts/01_prepare_data.py — data preparation pipeline

scripts/02_score_segments.py — batch scoring pipeline

outputs/summary/ — ranked reviewer-first summary outputs

outputs/viz/ — visualization-ready layers

outputs/scored/ — full scored artifacts for inspection

outputs/maps/ — interactive HTML maps

Method Summary
The workflow computes a segment-level Speed Safety Score using prepared road-segment attributes and Safe System-oriented logic.

The model is intentionally interpretable and policy-oriented; it is designed to support speed limit review prioritization, not to claim direct crash prediction.

The score evaluates:

Whether posted speed limits are aligned with Safe System reference speeds

Whether operating speeds exceed the posted speed environment

Whether vulnerable road user exposure is elevated

Whether road context suggests higher conflict risk

Inputs Used
Key fields used in scoring include:

posted_speed_limit_kph

operating_speed_kph

road_type

area_type

pedestrian_presence

cyclist_presence

ptw_presence

urban_flag

intersection_density_flag

Only segments with score_eligible_flag == 1 are included in the official scored output.

Speed Safety Score
The score combines four interpretable subscores:

Speed limit gap score

Operating speed score

VRU exposure score

Context score

The final weighted score is clipped to the range 0–100 and mapped to priority labels:

aligned

monitor

review

high_priority_review

See docs/score_definition.md for the full methodology.

Key Outputs
Reviewer-first outputs
outputs/summary/top_100_riskiest_segments_combined.csv

outputs/summary/top_20_per_country.csv

outputs/maps/thailand_speed_safety_map.html

outputs/maps/maharashtra_speed_safety_map.html

Full scored artifacts
outputs/scored/thailand_scored.csv

outputs/scored/thailand_scored.geojson

outputs/scored/maharashtra_scored.csv

outputs/scored/maharashtra_scored.geojson

Repository Structure
text
docs/
configs/
scripts/
src/
outputs/
  summary/
  viz/
  scored/
  maps/
Prerequisites
Python 3.x (tested with a recent 3.x version).

Git installed (for cloning the repository).

Ability to run commands from a terminal or Colab cell.

The workflow is designed to run from the committed Phase 1 inputs in this repository; no external raw datasets are required for reproduction by reviewers.

Setup
Option 1: Google Colab
From a Colab notebook cell:

bash
git clone https://github.com/Sharqascc/madel-.git
cd madel-
pip install -r requirements.txt
Option 2: Local environment (recommended)
From a terminal:

bash
git clone https://github.com/Sharqascc/madel-.git
cd madel-
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Run all commands from the repository root (madel-).

How to Run
Step 1: Prepare data
bash
python scripts/01_prepare_data.py
Step 2: Score segments
bash
python scripts/02_score_segments.py
This two-step workflow regenerates the scored artifacts, summary tables, and map outputs using the committed configuration and prepared inputs.

Expected Outcome
After running the two scripts successfully, you should see:

Updated summary tables in outputs/summary/

Updated scored artifacts in outputs/scored/

Updated visualization layers in outputs/viz/

Updated interactive map HTML files in outputs/maps/

These outputs will match the committed Phase 1 deliverables, subject to the same configuration and prepared inputs.

Reproducibility Notes
The repository includes committed Phase 1 outputs for reviewer access and reproducibility. Re-running the scripts from a clean clone with requirements.txt installed should regenerate the summary tables, scored outputs, and map artifacts.

Reviewer Guidance
Recommended review order:

docs/score_definition.md — methodology and score definition

outputs/summary/top_100_riskiest_segments_combined.csv — global top 100 segments

outputs/summary/top_20_per_country.csv — top segments per country

outputs/maps/thailand_speed_safety_map.html — interactive Thailand map

outputs/maps/maharashtra_speed_safety_map.html — interactive Maharashtra map

outputs/scored/ — full scored artifacts for auditability and inspection

Evaluation Methodology
This repository uses a transparent rule-based evaluation methodology centered on Safe System alignment and elevated vulnerable road user risk.

The methodology documents:

input assumptions

Safe System reference speeds

scoring logic

weighting

threshold bands

escalation logic

priority mapping

This supports reproducible and interpretable prioritization for transport policy workflows.

Notes
The model is rule-based and intentionally interpretable.

The outputs are designed for policy review and prioritization.

Interactive HTML maps are included for geospatial inspection.

The workflow is designed to be transferable to similar road safety contexts.

Status
Current repository state includes committed Phase 1 outputs, scored reviewer-inspection artifacts, and interactive map deliverables.
