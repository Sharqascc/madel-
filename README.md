# AI for Safer Roads — Phase 1 Submission

## Overview
This repository contains a Phase 1 road-segment risk prioritization workflow for Thailand and Maharashtra.
The project builds a transparent speed-safety score, ranks high-risk segments, and publishes reviewer-friendly tabular, geospatial, and interactive map outputs.

## What this repository includes
- A documented scoring definition in `docs/score_definition.md`
- Scoring configuration in `configs/scoring.yaml`
- Scoring implementation in `src/ai4saferroads/speed_safety_score.py`
- Batch scoring pipeline in `scripts/02_score_segments.py`
- Final ranked summary outputs in `outputs/summary/`
- Visualization-ready CSV and GeoJSON files in `outputs/viz/`
- Full scored reviewer-inspection artifacts in `outputs/scored/`
- Interactive HTML maps in `outputs/maps/`

## Study areas
- Thailand
- Maharashtra, India

## Method summary
The workflow computes a segment-level speed safety score from prepared road-segment attributes, applies calibrated threshold bands, and assigns review priority categories.
Outputs are designed to support transparent inspection, geospatial visualization, and downstream intervention prioritization.

## Key outputs
### Reviewer-first files
- `outputs/summary/top_100_riskiest_segments_combined.csv`
- `outputs/summary/top_20_per_country.csv`
- `outputs/maps/thailand_speed_safety_map.html`
- `outputs/maps/maharashtra_speed_safety_map.html`

### Full scored artifacts
- `outputs/scored/thailand_scored.csv`
- `outputs/scored/thailand_scored.geojson`
- `outputs/scored/maharashtra_scored.csv`
- `outputs/scored/maharashtra_scored.geojson`

## Repository structure
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

## How to reproduce in Colab
1. Clone the repository.
2. Install dependencies.
3. Run the data preparation and scoring pipeline.
4. Export summary tables, visualization layers, and HTML maps.

## Reviewer notes
Start with:
1. `docs/score_definition.md`
2. `outputs/summary/top_100_riskiest_segments_combined.csv`
3. Country HTML maps in `outputs/maps/`
4. Full scored artifacts in `outputs/scored/` for inspection and auditability

## Status
Current repository state includes committed Phase 1 outputs, map artifacts, and full scored reviewer-inspection files.
