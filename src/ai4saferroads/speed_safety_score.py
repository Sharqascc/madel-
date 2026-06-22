
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import yaml

DEFAULT_WEIGHTS: Dict[str, float] = {
    "speed_gap": 0.35,
    "operating_speed": 0.25,
    "vru_exposure": 0.20,
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
    uncertainty: Dict[str, float] = field(default_factory=lambda: {
        "missing_context_penalty": 10.0,
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

    uncertainty = {"missing_context_penalty": 10.0}
    uncertainty.update(raw.get("uncertainty", {}) or {})

    safe_speeds = raw.get("safe_speeds", {}) or {}

    return ScoreConfig(
        safe_speed_mixed_vru_kph=float(safe_speeds.get("mixed_vru", 30.0)),
        safe_speed_side_conflict_kph=float(safe_speeds.get("side_conflict", 50.0)),
        safe_speed_head_on_kph=float(safe_speeds.get("head_on", 70.0)),
        weights=weights,
        thresholds=thresholds,
        escalation=escalation,
        uncertainty=uncertainty,
    )

def _clip_0_100(values) -> pd.Series:
    if isinstance(values, pd.Series):
        return values.clip(lower=0.0, upper=100.0)
    return pd.Series(np.clip(values, 0.0, 100.0))

def _series(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(default).astype(float)
    return pd.Series(default, index=df.index, dtype=float)

def derive_safe_system_reference_speed(df: pd.DataFrame, config: ScoreConfig) -> pd.Series:
    ped = _series(df, "pedestrian_presence", 0.0)
    cyc = _series(df, "cyclist_presence", 0.0)
    ptw = _series(df, "ptw_presence", 0.0)
    urban = _series(df, "urban_flag", 0.0)
    intersection = _series(df, "intersection_density_flag", 0.0)
    road_type = df.get("road_type", pd.Series("unknown", index=df.index)).astype(str).str.lower()

    mixed_vru = (ped > 0) | (cyc > 0) | (ptw > 0)
    side_conflict = (urban > 0) | (intersection > 0) | road_type.isin(["secondary", "primary", "arterial"])

    ref = np.where(
        mixed_vru,
        config.safe_speed_mixed_vru_kph,
        np.where(side_conflict, config.safe_speed_side_conflict_kph, config.safe_speed_head_on_kph),
    )
    return pd.Series(ref, index=df.index, dtype=float)

def compute_speed_limit_gap_score(posted_speed_limit_kph: pd.Series, safe_ref_kph: pd.Series) -> pd.Series:
    gap = posted_speed_limit_kph - safe_ref_kph
    score = 100.0 - (gap * 2.5)
    return _clip_0_100(score)

def compute_operating_speed_score(operating_speed_kph: pd.Series, posted_speed_limit_kph: pd.Series) -> pd.Series:
    excess = operating_speed_kph - posted_speed_limit_kph
    score = 100.0 - (excess.clip(lower=0.0) * (100.0 / 30.0))
    return _clip_0_100(score)

def compute_vru_exposure_score(df: pd.DataFrame) -> pd.Series:
    ped = _series(df, "pedestrian_presence", np.nan)
    cyc = _series(df, "cyclist_presence", np.nan)
    ptw = _series(df, "ptw_presence", np.nan)

    known = pd.concat([ped, cyc, ptw], axis=1).notna().sum(axis=1)
    exposure = ped.fillna(0) + cyc.fillna(0) + ptw.fillna(0)

    score = 100.0 - (exposure * 22.5)
    score = score.where(known >= 2, np.minimum(score, 70.0))
    return _clip_0_100(score)

def compute_context_score(df: pd.DataFrame) -> pd.Series:
    urban = _series(df, "urban_flag", np.nan)
    intersection = _series(df, "intersection_density_flag", np.nan)
    road_type = df.get("road_type", pd.Series("unknown", index=df.index)).astype(str).str.lower()

    road_penalty = pd.Series(0.0, index=df.index, dtype=float)
    road_penalty = np.where(road_type.eq("secondary"), 25.0, road_penalty)
    road_penalty = np.where(pd.Series(road_type, index=df.index).eq("primary"), 18.0, road_penalty)
    road_penalty = np.where(pd.Series(road_type, index=df.index).eq("arterial"), 15.0, road_penalty)
    road_penalty = pd.Series(road_penalty, index=df.index, dtype=float)

    known = pd.concat([urban, intersection], axis=1).notna().sum(axis=1)

    score = 100.0 - urban.fillna(0) * 20.0 - intersection.fillna(0) * 15.0 - road_penalty
    score = score.where(known >= 2, np.minimum(score, 75.0))
    return _clip_0_100(score)

def compute_uncertainty_penalty(df: pd.DataFrame, config: ScoreConfig) -> pd.Series:
    cols = ["pedestrian_presence", "cyclist_presence", "ptw_presence", "urban_flag", "intersection_density_flag"]
    known = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in cols if c in df.columns], axis=1).notna().sum(axis=1)
    penalty = pd.Series(0.0, index=df.index, dtype=float)
    penalty = penalty + (known < 3).astype(float) * float(config.uncertainty["missing_context_penalty"])
    return penalty

def assign_priority_label(
    speed_safety_score: pd.Series,
    posted_speed_limit_kph: pd.Series | None = None,
    safe_system_reference_speed_kph: pd.Series | None = None,
    vru_exposure_score: pd.Series | None = None,
    config: ScoreConfig | None = None,
) -> pd.Series:
    config = config or ScoreConfig()
    thresholds = config.thresholds

    labels = pd.Series("aligned", index=speed_safety_score.index, dtype=object)
    labels = labels.mask(speed_safety_score < thresholds["monitor"], "monitor")
    labels = labels.mask(speed_safety_score < thresholds["review"], "review")
    labels = labels.mask(speed_safety_score < thresholds["high_priority_review"], "high_priority_review")

    if (
        config.escalation.get("enable_vru_escalation", True)
        and posted_speed_limit_kph is not None
        and safe_system_reference_speed_kph is not None
        and vru_exposure_score is not None
    ):
        over_safe = posted_speed_limit_kph > safe_system_reference_speed_kph
        vru_high_risk = vru_exposure_score < float(config.escalation["vru_high_risk_score_threshold"])
        posted_high = posted_speed_limit_kph >= float(config.escalation["posted_speed_escalation_threshold_kph"])
        labels = labels.mask(over_safe & vru_high_risk & posted_high, "high_priority_review")

    return labels

def score_segments(df: pd.DataFrame, config: ScoreConfig) -> pd.DataFrame:
    result = df.copy()

    posted = _series(df, "posted_speed_limit_kph", np.nan)
    operating = _series(df, "operating_speed_kph", np.nan)

    safe_ref = derive_safe_system_reference_speed(df, config)
    gap_score = compute_speed_limit_gap_score(posted, safe_ref)
    operating_score = compute_operating_speed_score(operating, posted)
    vru_score = compute_vru_exposure_score(df)
    context_score = compute_context_score(df)
    uncertainty_penalty = compute_uncertainty_penalty(df, config)

    final_score = (
        gap_score * config.weights["speed_gap"]
        + operating_score * config.weights["operating_speed"]
        + vru_score * config.weights["vru_exposure"]
        + context_score * config.weights["road_context"]
        - uncertainty_penalty
    )
    final_score = _clip_0_100(final_score)

    result["safe_system_reference_speed_kph"] = safe_ref
    result["speed_limit_gap_score"] = gap_score
    result["operating_speed_score"] = operating_score
    result["vru_exposure_score"] = vru_score
    result["context_score"] = context_score
    result["uncertainty_penalty"] = uncertainty_penalty
    result["speed_safety_score"] = final_score
    result["priority_label"] = assign_priority_label(
        final_score,
        posted_speed_limit_kph=posted,
        safe_system_reference_speed_kph=safe_ref,
        vru_exposure_score=vru_score,
        config=config,
    )
    return result
