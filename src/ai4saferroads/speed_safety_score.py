from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd


DEFAULT_WEIGHTS = {
    "speed_gap": 0.35,
    "operating_speed": 0.20,
    "vru_exposure": 0.25,
    "road_context": 0.20,
}


@dataclass
class ScoreConfig:
    safe_speed_mixed_vru_kph: float = 30.0
    safe_speed_side_conflict_kph: float = 50.0
    safe_speed_head_on_kph: float = 70.0
    weights: Dict[str, float] | None = None

    def __post_init__(self):
        if self.weights is None:
            self.weights = DEFAULT_WEIGHTS.copy()


def _clip_0_100(value: pd.Series) -> pd.Series:
    return value.clip(lower=0, upper=100)


def _normalize_flag(series: pd.Series) -> pd.Series:
    return series.fillna(0).astype(float).clip(0, 1)


def compute_speed_limit_gap_score(
    posted_speed_limit_kph: pd.Series,
    safe_system_reference_speed_kph: pd.Series
) -> pd.Series:
    gap = posted_speed_limit_kph - safe_system_reference_speed_kph
    return _clip_0_100((gap.clip(lower=0) / 40.0) * 100.0)


def compute_operating_speed_score(
    operating_speed_kph: pd.Series,
    posted_speed_limit_kph: pd.Series
) -> pd.Series:
    excess = (operating_speed_kph - posted_speed_limit_kph).clip(lower=0)
    return _clip_0_100((excess / 20.0) * 100.0)


def compute_vru_exposure_score(df: pd.DataFrame) -> pd.Series:
    ped = _normalize_flag(df["pedestrian_presence"])
    cyc = _normalize_flag(df["cyclist_presence"])
    ptw = _normalize_flag(df["ptw_presence"])
    cross = _normalize_flag(df["crossing_density_flag"])
    comm = _normalize_flag(df["commercial_frontage_flag"])
    transit = _normalize_flag(df["transit_stop_flag"])
    school = _normalize_flag(df["school_zone_flag"])

    score = (
        ped * 30
        + cyc * 20
        + ptw * 15
        + cross * 15
        + comm * 10
        + transit * 5
        + school * 5
    )
    return _clip_0_100(score)


def compute_context_score(df: pd.DataFrame) -> pd.Series:
    urban = _normalize_flag(df["urban_flag"])
    intersection = _normalize_flag(df["intersection_density_flag"])
    roadside = _normalize_flag(df["roadside_activity_flag"])
    non_sep = _normalize_flag(df["non_separated_traffic_flag"])

    score = (
        urban * 30
        + intersection * 25
        + roadside * 25
        + non_sep * 20
    )
    return _clip_0_100(score)


def assign_priority_label(
    speed_safety_score: pd.Series,
    vru_exposure_score: pd.Series | None = None,
    speed_limit_gap_score: pd.Series | None = None
) -> pd.Series:
    if vru_exposure_score is None or speed_limit_gap_score is None:
        return pd.Series(
            np.select(
                [
                    speed_safety_score >= 80,
                    speed_safety_score >= 60,
                    speed_safety_score >= 40,
                ],
                [
                    "high_priority_review",
                    "review",
                    "monitor",
                ],
                default="aligned",
            ),
            index=speed_safety_score.index,
        )

    critical_vru = (vru_exposure_score >= 40) & (speed_limit_gap_score >= 70)

    return pd.Series(
        np.select(
            [
                (speed_safety_score >= 80) | critical_vru,
                speed_safety_score >= 60,
                speed_safety_score >= 40,
            ],
            [
                "high_priority_review",
                "review",
                "monitor",
            ],
            default="aligned",
        ),
        index=speed_safety_score.index,
    )


def score_segments(
    df: pd.DataFrame,
    config: ScoreConfig | None = None
) -> pd.DataFrame:
    if config is None:
        config = ScoreConfig()

    result = df.copy()

    required_defaults: Dict[str, Any] = {
        "posted_speed_limit_kph": np.nan,
        "operating_speed_kph": np.nan,
        "road_type": "",
        "area_type": "",
        "pedestrian_presence": 0,
        "cyclist_presence": 0,
        "ptw_presence": 0,
        "crossing_density_flag": 0,
        "commercial_frontage_flag": 0,
        "transit_stop_flag": 0,
        "school_zone_flag": 0,
        "urban_flag": 0,
        "intersection_density_flag": 0,
        "roadside_activity_flag": 0,
        "non_separated_traffic_flag": 0,
    }

    for col, default_value in required_defaults.items():
        if col not in result.columns:
            result[col] = default_value

    road_type = result["road_type"].astype(str).str.strip().str.lower()
    area_type = result["area_type"].astype(str).str.strip().str.lower()
    vru_presence = result[
        ["pedestrian_presence", "cyclist_presence", "ptw_presence"]
    ].max(axis=1).fillna(0)

    # Conservative default:
    # unknown contexts fall back to 70 km/h unless clear urban/VRU-sensitive
    # evidence indicates a lower Safe System reference speed.
    conditions = [
        area_type.isin({"urban", "peri_urban", "built_up", "school_zone", "market_area"}) & (vru_presence > 0),
        road_type.isin({"local", "collector", "urban_arterial"}) & (vru_presence > 0),
        area_type.isin({"urban", "peri_urban", "built_up"}),
        road_type.isin({"expressway", "motorway", "freeway", "divided_highway"}),
        road_type.isin({"undivided_highway", "two_way_rural", "rural_arterial"}),
    ]

    choices = [
        config.safe_speed_mixed_vru_kph,
        config.safe_speed_mixed_vru_kph,
        config.safe_speed_side_conflict_kph,
        config.safe_speed_head_on_kph,
        config.safe_speed_head_on_kph,
    ]

    result["safe_system_reference_speed_kph"] = np.select(
        conditions,
        choices,
        default=config.safe_speed_head_on_kph,
    )

    result["speed_limit_gap_kph"] = (
        result["posted_speed_limit_kph"] - result["safe_system_reference_speed_kph"]
    )

    result["speed_limit_gap_score"] = compute_speed_limit_gap_score(
        result["posted_speed_limit_kph"],
        result["safe_system_reference_speed_kph"],
    )

    clamped_operating = np.maximum(
        result["operating_speed_kph"].fillna(result["posted_speed_limit_kph"]),
        result["posted_speed_limit_kph"],
    )

    result["operating_speed_score"] = compute_operating_speed_score(
        clamped_operating,
        result["posted_speed_limit_kph"],
    )

    result["vru_exposure_score"] = compute_vru_exposure_score(result)
    result["context_score"] = compute_context_score(result)

    weights = config.weights
    result["speed_safety_score"] = (
        result["speed_limit_gap_score"] * weights["speed_gap"]
        + result["operating_speed_score"] * weights["operating_speed"]
        + result["vru_exposure_score"] * weights["vru_exposure"]
        + result["context_score"] * weights["road_context"]
    ).round(2)

    result["priority_label"] = assign_priority_label(
        result["speed_safety_score"],
        result["vru_exposure_score"],
        result["speed_limit_gap_score"],
    )

    return result


if __name__ == "__main__":
    sample = pd.DataFrame([
        {
            "posted_speed_limit_kph": 60,
            "operating_speed_kph": 67,
            "road_type": "collector",
            "area_type": "urban",
            "pedestrian_presence": 1,
            "cyclist_presence": 0,
            "ptw_presence": 1,
            "crossing_density_flag": 1,
            "commercial_frontage_flag": 1,
            "transit_stop_flag": 0,
            "school_zone_flag": 0,
            "urban_flag": 1,
            "intersection_density_flag": 1,
            "roadside_activity_flag": 1,
            "non_separated_traffic_flag": 1,
        }
    ])

    scored = score_segments(sample)
    print(scored[[
        "posted_speed_limit_kph",
        "safe_system_reference_speed_kph",
        "speed_limit_gap_score",
        "operating_speed_score",
        "vru_exposure_score",
        "context_score",
        "speed_safety_score",
        "priority_label",
    ]].to_string(index=False))
