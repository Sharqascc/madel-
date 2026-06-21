# AI for Safer Roads

Repository for the ADB AI for Safer Roads Innovation Challenge.

## Structure
- docs/: methodology, evaluation, score definition
- src/ai4saferroads/: core package
- scripts/: runnable pipeline scripts
- outputs/maps/: generated map outputs

## Quick start
```bash
pip install -r requirements.txt
python scripts/01_prepare_data.py
python scripts/02_score_segments.py
python scripts/03_generate_map.py
```
