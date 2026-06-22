# Speed Safety Score

## Purpose

The Speed Safety Score prioritizes road segments for speed limit review using a transparent, reproducible, and policy-oriented method aligned with Safe System principles.

## Inputs

The scoring pipeline uses the prepared segment-level dataset produced by `scripts/01_prepare_data.py`. Key fields used in scoring are:

- `posted_speed_limit_kph`
- `operating_speed_kph`
- `road_type`
- `area_type`
- `pedestrian_presence`
- `cyclist_presence`
- `ptw_presence`
- `urban_flag`
- `intersection_density_flag`

Only segments with `score_eligible_flag == 1` are included in the official score output.

## Safe System reference speed

A reference speed is assigned to each segment:

- 30 kph for segments with mixed vulnerable road user presence.
- 50 kph for side-conflict environments, including urban or intersection-related contexts.
- 70 kph for higher-speed head-on environments with lower direct conflict exposure.

## Score components

Each segment receives four subscores from 0 to 100, where higher is safer:

1. **Speed limit gap score**
   - Based on the difference between posted speed and the Safe System reference speed.
   - Larger positive gaps reduce the score.

2. **Operating speed score**
   - Based on the difference between operating speed and posted speed.
   - Speeds above the posted limit reduce the score.

3. **VRU exposure score**
   - Based on pedestrian, cyclist, and powered two-wheeler presence.
   - More vulnerable road user exposure reduces the score.

4. **Context score**
   - Based on urban context, intersection density, and road type.
   - More conflict-prone contexts reduce the score.

## Weighted final score

The final score is computed as:

- 35% speed limit gap score
- 20% operating speed score
- 25% VRU exposure score
- 20% context score

The final score is clipped to the range 0 to 100.

## Priority labels

Priority labels are assigned from the final score:

- `aligned`: score >= 75
- `monitor`: 55 <= score < 75
- `review`: 35 <= score < 55
- `high_priority_review`: score < 35

An escalation rule can still assign `high_priority_review` where vulnerable road user risk is high and posted speed remains materially above the Safe System reference speed.

## Notes

- The model is intentionally interpretable and rule-based.
- The score is designed to support review prioritization, not to claim direct crash prediction.
- Thresholds were calibrated to produce usable prioritization bands for reviewer and policy workflows.
