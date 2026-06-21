from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import yaml


DEFAULT_WEIGHTS: Dict[str, float] = {
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
    weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "high_priority_review": 40.0,
        "review": 60.0,
        "monitor": 80.0,
    })
    escalation: Dict[str, float | bool] = field(default_factory=lambda: {
        "enable_vru_escalation": True,
        "vru_high_risk_score_threshold": 50.0,
        "posted_speed_escalation_threshold_kph": 60.0,
    })


def load_score_config(config_path: str = "configs/scoring.yaml") -> ScoreConfig:
    path = Path(config_path)
    if not path.exists():
        return ScoreConfig()

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    weights = DEFAULT_WEIGHTS.copy()
    weights.update(raw.get("weights", {}) or {})

    thresholds = {
        "high_priority_review": 40.0,
        "review": 60.0,
        "monitor": 80.0,
    }
    thresholds.update(raw.get("thresholds", {}) or {})

    escalation = {
        "enable_vru_escalation": True,
        "vru_high_risk_score_threshold": 50.0,
        "posted_speed_escalation_threshold_kph": 60.0,
    }
    escalation.update(raw.get("escalation", {}) or {})

    safe_speeds = raw.get("safe_speeds", {}) or {}

    return ScoreConfig(
        safe_speed_mixed_vru_kph=float(safe_speeds.get("mixed_vru", 30.0)),
        safe_speed_side_conflict_kph=float(safe_speeds.get("side_conflict", 50.0)),
        safe_speed_head_on_kph=float(safe_speeds.get("head_on", 70.0)),
        weights=weights,
        thresholds=thresholds,
        escalation=escalation,
    )


def _clip_0_100(values: pd.Series | np.ndarray | float) -> pd.Series:
    if isinstance(values, pd.Series):
        return values.clip(lower=0.0, upper=100.0)
    return pd.Series(np.clip(values, 0.0, 100.0))


def _series(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


def derive_safe_system_reference_speed(df: pd.DataFrame, config: ScoreConfig) -> pd.Series:
    pedestrian = _series(df, "pedestrian_activity", 0.0)
    cyclist = _series(df, "cyclist_activity", 0.0)
    school_zone = _series(df, "school_zone", 0.0)
    market_zone = _series(df, "market_zone", 0.0)
    urban = _series(df, "urban", 0.0)
    intersection_density = _series(df, "intersection_density", 0.0)
    divided = _series(df, "divided_road", 0.0)

    mixed_vru = (
        (pedestrian > 0)
        | (cyclist > 0)
        | (school_zone > 0)
        | (market_zone > 0)
    )

    side_conflict = (
        (urban > 0)
        | (intersection_density >= 3)
        | (divided <= 0)
    )

    ref = np.where(
        mixed_vru,
        config.safe_speed_mixed_vru_kph,
        np.where(
            side_conflict,
            config.safe_speed_side_conflict_kph,
            config.safe_speed_head_on_kph,
        ),
    )
    return pd.Series(ref, index=df.index, dtype=float)


def compute_speed_limit_gap_score(
    posted_speed_limit_kph: pd.Series,
    safe_system_reference_speed_kph: pd.Series,
) -> pd.Series:
    gap = (posted_speed_limit_kph - safe_system_reference_speed_kph).clip(lower=0.0)
    raw = 100.0 - (gap / 40.0) * 100.0
    return _clip_0_100(raw)


def compute_operating_speed_score(
    operating_speed_kph: pd.Series,
    posted_speed_limit_kph: pd.Series,
) -> pd.Series:
    excess = (operating_speed_kph - posted_speed_limit_kph).clip(lower=0.0)
    raw = 100.0 - (excess / 30.0) * 100.0
    return _clip_0_100(raw)


def compute_vru_exposure_score(df: pd.DataFrame) -> pd.Series:
    pedestrian = _series(df, "pedestrian_activity", 0.0)
    cyclist = _series(df, "cyclist_activity", 0.0)
    ptw = _series(df, "ptw_activity", 0.0)
    crossing_density = _series(df, "crossing_density", 0.0)
    commercial_frontage = _series(df, "commercial_frontage", 0.0)
    transit_stop = _series(df, "transit_stop", 0.0)
    school_zone = _series(df, "school_zone", 0.0)

    raw_risk = (
        pedestrian * 30.0
        + cyclist * 20.0
        + ptw * 15.0
        + crossing_density * 15.0
        + commercial_frontage * 10.0
        + transit_stop * 5.0
        + school_zone * 5.0
    )
    return _clip_0_100(100.0 - raw_risk)


def compute_context_score(df: pd.DataFrame) -> pd.Series:
    urban = _series(df, "urban", 0.0)
    intersection_density = _series(df, "intersection_density", 0.0)
    roadside_activity = _series(df, "roadside_activity", 0.0)
    non_separated_traffic = _series(df, "non_separated_traffic", 0.0)

    raw_risk = (
        urban * 30.0
        + intersection_density * 25.0
        + roadside_activity * 25.0
        + non_separated_traffic * 20.0
    )
    return _clip_0_100(100.0 - raw_risk)


def compute_speed_safety_score(
    speed_limit_gap_score: pd.Series,
    operating_speed_score: pd.Series,
    vru_exposure_score: pd.Series,
    context_score: pd.Series,
    weights: Dict[str, float],
) -> pd.Series:
    total = (
        speed_limit_gap_score * weights["speed_gap"]
        + operating_speed_score * weights["operating_speed"]
        + vru_exposure_score * weights["vru_exposure"]
        + context_score * weights["road_context"]
    )
    return _clip_0_100(total)


def assign_priority_label(
    score: pd.Series,
    posted_speed_limit_kph: pd.Series | None = None,
    safe_system_reference_speed_kph: pd.Series | None = None,
    vru_exposure_score: pd.Series | None = None,
    config: ScoreConfig | None = None,
) -> pd.Series:
    if config is None:
        config = ScoreConfig()

    labels = pd.Series(index=score.index, dtype="object")
    labels.loc[score < config.thresholds["high_priority_review"]] = "high_priority_review"
    labels.loc[(score >= config.thresholds["high_priority_review"]) & (score < config.thresholds["review"])] = "review"
    labels.loc[(score >= config.thresholds["review"]) & (score < config.thresholds["monitor"])] = "monitor"
    labels.loc[score >= config.thresholds["monitor"]] = "aligned"

    if (
        config.escalation.get("enable_vru_escalation", True)
        and posted_speed_limit_kph is not None
        and safe_system_reference_speed_kph is not None
        and vru_exposure_score is not None
    ):
        vru_high_risk = vru_exposure_score < float(config.escalation["vru_high_risk_score_threshold"])
        mixed_vru_ref = safe_system_reference_speed_kph <= config.safe_speed_mixed_vru_kph
        high_posted = posted_speed_limit_kph >= float(config.escalation["posted_speed_escalation_threshold_kph"])

        escalate_mask = vru_high_risk & mixed_vru_ref & high_posted
        labels.loc[escalate_mask] = "high_priority_review"

    return labels


def score_segments(df: pd.DataFrame, config: ScoreConfig | None = None) -> pd.DataFrame:
    if config is None:
        config = load_score_config()

    out = df.copy()

    posted = _series(out, "posted_speed_limit_kph", 0.0)
    operating = _series(out, "operating_speed_kph", 0.0)

    out["safe_system_reference_speed_kph"] = derive_safe_system_reference_speed(out, config)
    out["speed_limit_gap_score"] = compute_speed_limit_gap_score(
        posted, out["safe_system_reference_speed_kph"]
    )
    out["operating_speed_score"] = compute_operating_speed_score(
        operating, posted
    )
    out["vru_exposure_score"] = compute_vru_exposure_score(out)
    out["context_score"] = compute_context_score(out)
    out["speed_safety_score"] = compute_speed_safety_score(
        out["speed_limit_gap_score"],
        out["operating_speed_score"],
        out["vru_exposure_score"],
        out["context_score"],
        config.weights,
    )
    out["priority_label"] = assign_priority_label(
        out["speed_safety_score"],
        posted_speed_limit_kph=posted,
        safe_system_reference_speed_kph=out["safe_system_reference_speed_kph"],
        vru_exposure_score=out["vru_exposure_score"],
        config=config,
    )

    return out
