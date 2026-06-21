from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("outputs/prepared_segments.csv")


def _base_row(i: int) -> dict:
    return {
        "segment_id": f"seg_{i:04d}",
        "posted_speed_limit_kph": 50.0,
        "operating_speed_kph": 50.0,
        "pedestrian_activity": 0,
        "cyclist_activity": 0,
        "ptw_activity": 0,
        "crossing_density": 0,
        "commercial_frontage": 0,
        "transit_stop": 0,
        "school_zone": 0,
        "market_zone": 0,
        "urban": 0,
        "intersection_density": 0,
        "roadside_activity": 0,
        "non_separated_traffic": 0,
        "divided_road": 1,
        "latitude": 23.50 + np.random.uniform(-0.25, 0.25),
        "longitude": 90.20 + np.random.uniform(-0.25, 0.25),
    }


def make_aligned(i: int) -> dict:
    row = _base_row(i)
    row.update({
        "posted_speed_limit_kph": float(np.random.choice([30, 50, 70])),
        "operating_speed_kph": 0.0,
    })

    scenario = np.random.choice(["school_safe", "urban_ok", "rural_ok"], p=[0.25, 0.35, 0.40])

    if scenario == "school_safe":
        row.update({
            "posted_speed_limit_kph": 30.0,
            "operating_speed_kph": float(np.random.uniform(24, 31)),
            "pedestrian_activity": 1,
            "school_zone": 1,
            "urban": 1,
            "divided_road": 0,
        })
    elif scenario == "urban_ok":
        row.update({
            "posted_speed_limit_kph": 50.0,
            "operating_speed_kph": float(np.random.uniform(42, 52)),
            "urban": 1,
            "intersection_density": int(np.random.choice([0, 1, 2])),
            "divided_road": 0,
        })
    else:
        row.update({
            "posted_speed_limit_kph": 70.0,
            "operating_speed_kph": float(np.random.uniform(62, 73)),
            "urban": 0,
            "divided_road": 1,
        })
    return row


def make_monitor(i: int) -> dict:
    row = _base_row(i)
    scenario = np.random.choice(["urban_arterial", "moderate_side_conflict", "mild_speed_gap"])

    if scenario == "urban_arterial":
        row.update({
            "posted_speed_limit_kph": 60.0,
            "operating_speed_kph": float(np.random.uniform(58, 66)),
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "divided_road": 0,
        })
    elif scenario == "moderate_side_conflict":
        row.update({
            "posted_speed_limit_kph": 70.0,
            "operating_speed_kph": float(np.random.uniform(68, 77)),
            "urban": 1,
            "intersection_density": 3,
            "divided_road": 0,
        })
    else:
        row.update({
            "posted_speed_limit_kph": 80.0,
            "operating_speed_kph": float(np.random.uniform(74, 82)),
            "urban": 0,
            "divided_road": 1,
        })
    return row


def make_review(i: int) -> dict:
    row = _base_row(i)
    scenario = np.random.choice(["urban_vru", "peri_urban_mixed", "high_speed_side_conflict"])

    if scenario == "urban_vru":
        row.update({
            "posted_speed_limit_kph": 50.0,
            "operating_speed_kph": float(np.random.uniform(56, 66)),
            "pedestrian_activity": 1,
            "cyclist_activity": int(np.random.choice([0, 1])),
            "ptw_activity": 1,
            "crossing_density": 1,
            "commercial_frontage": 1,
            "transit_stop": int(np.random.choice([0, 1])),
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "non_separated_traffic": 1,
            "divided_road": 0,
        })
    elif scenario == "peri_urban_mixed":
        row.update({
            "posted_speed_limit_kph": 60.0,
            "operating_speed_kph": float(np.random.uniform(64, 74)),
            "pedestrian_activity": 1,
            "ptw_activity": 1,
            "commercial_frontage": 1,
            "market_zone": 1,
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "divided_road": 0,
        })
    else:
        row.update({
            "posted_speed_limit_kph": 70.0,
            "operating_speed_kph": float(np.random.uniform(74, 84)),
            "urban": 1,
            "intersection_density": 3,
            "roadside_activity": 1,
            "non_separated_traffic": 1,
            "divided_road": 0,
        })
    return row


def make_high_priority(i: int) -> dict:
    row = _base_row(i)
    scenario = np.random.choice(["school_zone_violation", "dense_urban_arterial", "market_corridor"])

    if scenario == "school_zone_violation":
        row.update({
            "posted_speed_limit_kph": float(np.random.choice([50, 60])),
            "operating_speed_kph": float(np.random.uniform(58, 72)),
            "pedestrian_activity": 1,
            "cyclist_activity": 1,
            "ptw_activity": 1,
            "crossing_density": 1,
            "school_zone": 1,
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "non_separated_traffic": 1,
            "divided_road": 0,
        })
    elif scenario == "dense_urban_arterial":
        row.update({
            "posted_speed_limit_kph": float(np.random.choice([60, 70])),
            "operating_speed_kph": float(np.random.uniform(68, 82)),
            "pedestrian_activity": 1,
            "cyclist_activity": 1,
            "ptw_activity": 1,
            "crossing_density": 1,
            "commercial_frontage": 1,
            "transit_stop": 1,
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "non_separated_traffic": 1,
            "divided_road": 0,
        })
    else:
        row.update({
            "posted_speed_limit_kph": float(np.random.choice([60, 70, 80])),
            "operating_speed_kph": float(np.random.uniform(65, 85)),
            "pedestrian_activity": 1,
            "cyclist_activity": int(np.random.choice([0, 1])),
            "ptw_activity": 1,
            "crossing_density": 1,
            "commercial_frontage": 1,
            "transit_stop": 1,
            "market_zone": 1,
            "urban": 1,
            "intersection_density": 1,
            "roadside_activity": 1,
            "non_separated_traffic": 1,
            "divided_road": 0,
        })
    return row


def generate_stratified_synthetic_data(n: int = 250, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)

    target = {
        "aligned": round(n * 0.30),
        "monitor": round(n * 0.25),
        "review": round(n * 0.25),
        "high_priority_review": n - round(n * 0.30) - round(n * 0.25) - round(n * 0.25),
    }

    rows = []
    idx = 0

    for _ in range(target["aligned"]):
        rows.append(make_aligned(idx))
        idx += 1

    for _ in range(target["monitor"]):
        rows.append(make_monitor(idx))
        idx += 1

    for _ in range(target["review"]):
        rows.append(make_review(idx))
        idx += 1

    for _ in range(target["high_priority_review"]):
        rows.append(make_high_priority(idx))
        idx += 1

    df = pd.DataFrame(rows)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def main() -> None:
    print("Generating stratified synthetic reviewer-friendly demo data...")
    df = generate_stratified_synthetic_data(n=250, seed=42)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved prepared segments to: {OUTPUT_PATH.resolve()}")
    print("\nPrepared data preview:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
