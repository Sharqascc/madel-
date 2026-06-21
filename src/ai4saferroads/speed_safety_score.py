from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import warnings

import numpy as np
import pandas as pd
import yaml


DEFAULT_SAFE_SPEEDS: Dict[str, float] = {
    "mixed_vru": 30.0,
    "side_conflict": 50.0,
    "head_on": 70.0,
}

DEFAULT_WEIGHTS: Dict[str, float] = {
    "speed_gap": 0.35,
    "operating_speed": 0.20,
    "vru_exposure": 0.25,
    "road_context": 0.20,
}

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "high_priority_review": 40.0,
    "review": 60.0,
    "monitor": 80.0,
}

DEFAULT_ESCALATION: Dict[str, Any] = {
    "enable_vru_escalation": True,
    "vru_high_risk_score_threshold": 50.0,
    "posted_speed_escalation_threshold_kph": 60.0,
}


@dataclass
class ScoreConfig:
    safe_speeds: Dict[str, float] = field(default_factory=lambda: DEFAULT_SAFE_SPEEDS.copy())
    weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    thresholds: Dict[str, float] = field(default_factory=lambda: DEFAULT_THRESHOLDS.copy())
    escalation: Dict[str, Any] = field(default_factory=lambda: DEFAULT_ESCALATION.copy())

    def __post_init__(self) -> None:
        for key in ("mixed_vru", "side_conflict", "head_on"):
            if key not in self.safe_speeds:
                raise ValueError(f"Missing safe_speeds key: {key}")

        for key in ("speed_gap", "operating_speed", "vru_exposure", "road_context"):
            if key not in self.weights:
                raise ValueError(f"Missing weights key: {key}")

        total = sum(self.weights.values())
        if not np.isclose(total, 1.0, atol=0.01):
            warnings.warn(
                f"Scoring weights sum to {total:.4f}, not 1.0. Check configs/scoring.yaml.",
                stacklevel=2,
            )


def load_score_config(config_path: Optional[str | Path] = None) -> ScoreConfig:
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "configs" / "scoring.yaml"
    path = Path(config_path)

    if not path.exists():
        warnings.warn(f"Config file not found at {path}. Using defaults.", stacklevel=2)
        return ScoreConfig()

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    return ScoreConfig(
        safe_speeds={**DEFAULT_SAFE_SPEEDS, **(raw.get("safe_speeds", {}) or {})},
        weights={**DEFAULT_WEIGHTS, **(raw.get("weights", {}) or {})},
        thresholds={**DEFAULT_THRESHOLDS, **(raw.get("thresholds", {}) or {})},
        escalation={**DEFAULT_ESCALATION, **(raw.get("escalation", {}) or {})},
    )


def clip100(series: pd.Series | np.ndarray) -> pd.Series:
    return pd.Series(series).clip(lower=0.0, upper=100.0)


def flag(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0).clip(0.0, 1.0)


def numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def derive_safe_system_reference_speed(df: pd.DataFrame, config: ScoreConfig) -> pd.Series:
    ped = flag(df, "pedestrian_presence")
    cyc = flag(df, "cyclist_presence")
    ptw = flag(df, "ptw_presence")
    vru = ((ped + cyc + ptw) > 0).astype(float)

    urban = flag(df, "urban_flag")
    school = flag(df, "school_zone_flag")
    market = flag(df, "market_zone_flag")
    sensitive = ((urban + school + market) > 0).astype(float)

    roadtype = (
        df["road_type"].fillna("").astype(str).str.strip().str.lower()
        if "road_type" in df.columns else pd.Series("", index=df.index)
    )
    areatype = (
        df["area_type"].fillna("").astype(str).str.strip().str.lower()
        if "area_type" in df.columns else pd.Series("", index=df.index)
    )

    lower_order = roadtype.isin(["local", "collector", "urban_arterial"])
    urban_area = areatype.isin(["urban", "peri_urban", "built_up", "school_zone", "market_area"])
    high_speed = roadtype.isin(["expressway", "motorway", "freeway", "divided_highway"])

    ref = pd.Series(config.safe_speeds["head_on"], index=df.index, dtype=float)
    ref = ref.where(~(urban_area), other=config.safe_speeds["side_conflict"])
    ref = ref.where(~(vru.eq(1) & lower_order), other=config.safe_speeds["side_conflict"])
    ref = ref.where(~(vru.eq(1) & (sensitive.eq(1) | urban_area)), other=config.safe_speeds["mixed_vru"])
    ref = ref.where(~high_speed, other=config.safe_speeds["head_on"])
    return ref


def compute_speed_limit_gap_score(posted_speed_limit_kph: pd.Series, safe_system_reference_speed_kph: pd.Series) -> pd.Series:
    gap = posted_speed_limit_kph - safe_system_reference_speed_kph
    penalty = clip100((gap / 40.0) * 100.0)
    return clip100(100.0 - penalty)


def compute_operating_speed_score(operating_speed_kph: pd.Series, posted_speed_limit_kph: pd.Series) -> pd.Series:
    opspeed = operating_speed_kph.fillna(posted_speed_limit_kph)
    excess = opspeed - posted_speed_limit_kph
    penalty = clip100((excess / 30.0) * 100.0)
    return clip100(100.0 - penalty)


def compute_vru_exposure_score(df: pd.DataFrame) -> pd.Series:
    risk = (
        flag(df, "pedestrian_presence") * 30
        + flag(df, "cyclist_presence") * 20
        + flag(df, "ptw_presence") * 15
        + flag(df, "crossing_density_flag") * 15
        + flag(df, "commercial_frontage_flag") * 10
        + flag(df, "transit_stop_flag") * 5
        + flag(df, "school_zone_flag") * 5
    )
    return clip100(100.0 - risk)


def compute_context_score(df: pd.DataFrame) -> pd.Series:
    risk = (
        flag(df, "urban_flag") * 30
        + flag(df, "intersection_density_flag") * 25
        + flag(df, "roadside_activity_flag") * 25
        + flag(df, "non_separated_traffic_flag") * 20
    )
    return clip100(100.0 - risk)


def compute_speed_safety_score(
    speed_limit_gap_score: pd.Series,
    operating_speed_score: pd.Series,
    vru_exposure_score: pd.Series,
    context_score: pd.Series,
    weights: Dict[str, float],
) -> pd.Series:
    composite = (
        speed_limit_gap_score * weights["speed_gap"]
        + operating_speed_score * weights["operating_speed"]
        + vru_exposure_score * weights["vru_exposure"]
        + context_score * weights["road_context"]
    )
    return clip100(composite.round(2))


def assign_priority_label(
    score: pd.Series,
    posted_speed_limit_kph: pd.Series,
    safe_system_reference_speed_kph: pd.Series,
    vru_exposure_score: pd.Series,
    config: ScoreConfig,
) -> pd.Series:
    t = config.thresholds
    label = pd.Series("high_priority_review", index=score.index, dtype=object)
    label = label.where(score < t["review"], other="review")
    label = label.where(score < t["monitor"], other="monitor")
    label = label.where(score < 1000, other="aligned")
    label.loc[score >= t["monitor"]] = "aligned"

    esc = config.escalation
    if esc.get("enable_vru_escalation", True):
        vru_thresh = float(esc.get("vru_high_risk_score_threshold", 50.0))
        speed_thresh = float(esc.get("posted_speed_escalation_threshold_kph", 60.0))
        mixed_vru_ref = safe_system_reference_speed_kph <= float(config.safe_speeds["mixed_vru"])
        escalate_mask = (
            (vru_exposure_score < vru_thresh)
            & (posted_speed_limit_kph >= speed_thresh)
            & mixed_vru_ref
            & label.isin(["monitor", "review"])
        )
        escalation_map = {
            "monitor": "review",
            "review": "high_priority_review",
        }
        label = label.where(~escalate_mask, other=label.map(escalation_map).fillna(label))
    return label


def score_segments(df: pd.DataFrame, config: Optional[ScoreConfig] = None) -> pd.DataFrame:
    if config is None:
        config = load_score_config()

    result = df.copy()

    if "posted_speed_limit_kph" not in result.columns:
        result["posted_speed_limit_kph"] = np.nan
    if "operating_speed_kph" not in result.columns:
        result["operating_speed_kph"] = np.nan

    result["safe_system_reference_speed_kph"] = derive_safe_system_reference_speed(result, config)
    result["speed_limit_gap_kph"] = numeric(result, "posted_speed_limit_kph", np.nan) - result["safe_system_reference_speed_kph"]
    result["speed_limit_gap_score"] = compute_speed_limit_gap_score(
        numeric(result, "posted_speed_limit_kph", np.nan),
        result["safe_system_reference_speed_kph"],
    )
    result["operating_speed_score"] = compute_operating_speed_score(
        numeric(result, "operating_speed_kph", np.nan),
        numeric(result, "posted_speed_limit_kph", np.nan),
    )
    result["vru_exposure_score"] = compute_vru_exposure_score(result)
    result["context_score"] = compute_context_score(result)
    result["speed_safety_score"] = compute_speed_safety_score(
        result["speed_limit_gap_score"],
        result["operating_speed_score"],
        result["vru_exposure_score"],
        result["context_score"],
        config.weights,
    )
    result["priority_label"] = assign_priority_label(
        result["speed_safety_score"],
        numeric(result, "posted_speed_limit_kph", np.nan),
        result["safe_system_reference_speed_kph"],
        result["vru_exposure_score"],
        config,
    )
    return result
