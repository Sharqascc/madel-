# AI for Safer Roads

Repository for the ADB AI for Safer Roads Innovation Challenge.

## Objective

This project screens road segments for potential speed-limit misalignment under Safe System principles. It generates a transparent segment-level `speed_safety_score`, interpretable priority labels, and a lightweight map artifact for reviewer-facing inspection.

## Repository Structure

- `configs/`: scoring weights, thresholds, and escalation settings.
- `docs/`: score definition and methodology.
- `src/ai4saferroads/`: core scoring package.
- `scripts/`: runnable preparation, scoring, and visualization pipeline scripts.
- `tests/`: unit tests for scoring logic.
- `outputs/maps/`: generated HTML map outputs.

## Pipeline

```bash
python scripts/01_prepare_data.py
python scripts/02_score_segments.py
python scripts/03_generate_map.py
```

## Core Logic

The scoring pipeline produces:
- `safe_system_reference_speed_kph`
- `speed_limit_gap_score`
- `operating_speed_score`
- `vru_exposure_score`
- `context_score`
- `speed_safety_score`
- `priority_label`

The composite index is designed so that higher scores indicate stronger alignment with the implemented Safe System logic, while lower scores indicate higher need for intervention review.

## Configuration

`configs/scoring.yaml` stores:
- reference speed tiers,
- component weights,
- priority thresholds,
- escalation settings.

## Testing

Run:

```bash
pytest -q
```

## Output

The expected submission-facing outputs are:
- a scored segment table,
- documentation of methodology and score logic,
- an HTML map artifact highlighting priority segments.
