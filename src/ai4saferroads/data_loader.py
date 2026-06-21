from __future__ import annotations

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd


def generate_synthetic_segments(n: int = 250, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    road_types = np.array(["local", "collector", "urban_arterial", "divided_highway", "rural_arterial"])
    area_types = np.array(["urban", "peri_urban", "built_up", "rural", "market_area"])

    df = pd.DataFrame({
        "segment_id": [f"seg_{i:04d}" for i in range(n)],
        "road_type": rng.choice(road_types, size=n, p=[0.22, 0.22, 0.24, 0.14, 0.18]),
        "area_type": rng.choice(area_types, size=n, p=[0.28, 0.18, 0.20, 0.24, 0.10]),
        "posted_speed_limit_kph": rng.choice([30, 40, 50, 60, 70, 80], size=n, p=[0.10, 0.15, 0.28, 0.22, 0.17, 0.08]),
    })

    df["urban_flag"] = df["area_type"].isin(["urban", "peri_urban", "built_up", "market_area"]).astype(int)
    df["school_zone_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.14, 0.03)).astype(int)
    df["market_zone_flag"] = (df["area_type"].eq("market_area") | (rng.random(n) < 0.06)).astype(int)

    df["pedestrian_presence"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.62, 0.16)).astype(int)
    df["cyclist_presence"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.35, 0.10)).astype(int)
    df["ptw_presence"] = (rng.random(n) < 0.42).astype(int)

    df["crossing_density_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.48, 0.08)).astype(int)
    df["commercial_frontage_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.40, 0.06)).astype(int)
    df["transit_stop_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.28, 0.03)).astype(int)
    df["intersection_density_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.46, 0.12)).astype(int)
    df["roadside_activity_flag"] = (rng.random(n) < np.where(df["urban_flag"].eq(1), 0.44, 0.09)).astype(int)
    df["non_separated_traffic_flag"] = (~df["road_type"].isin(["divided_highway"])).astype(int)

    speed_noise = rng.normal(4.0, 6.0, size=n)
    urban_penalty = np.where(df["urban_flag"].eq(1), -2.0, 2.0)
    df["operating_speed_kph"] = (df["posted_speed_limit_kph"] + speed_noise + urban_penalty).clip(lower=20).round(1)

    base_lat, base_lon = 23.5, 90.2
    df["latitude"] = base_lat + rng.normal(0, 0.18, size=n)
    df["longitude"] = base_lon + rng.normal(0, 0.18, size=n)

    return df


def load_or_generate_segments(input_path: Optional[str | Path] = None, n: int = 250, seed: int = 42) -> pd.DataFrame:
    if input_path is None:
        return generate_synthetic_segments(n=n, seed=seed)

    path = Path(input_path)
    if path.exists():
        return pd.read_csv(path)

    return generate_synthetic_segments(n=n, seed=seed)
