import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai4saferroads.speed_safety_score import (
    ScoreConfig,
    assign_priority_label,
    compute_context_score,
    compute_operating_speed_score,
    compute_speed_limit_gap_score,
    compute_speed_safety_score,
    compute_vru_exposure_score,
    derive_safe_system_reference_speed,
    load_score_config,
    score_segments,
)


def test_reference_speed_mixed_vru_is_30():
    df = pd.DataFrame(
        {
            "pedestrian_activity": [1],
            "cyclist_activity": [0],
            "school_zone": [0],
            "market_zone": [0],
            "urban": [1],
            "intersection_density": [5],
            "divided_road": [0],
        }
    )
    result = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(result.iloc[0]) == 30.0


def test_reference_speed_side_conflict_is_50():
    df = pd.DataFrame(
        {
            "pedestrian_activity": [0],
            "cyclist_activity": [0],
            "school_zone": [0],
            "market_zone": [0],
            "urban": [1],
            "intersection_density": [4],
            "divided_road": [1],
        }
    )
    result = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(result.iloc[0]) == 50.0


def test_reference_speed_head_on_is_70():
    df = pd.DataFrame(
        {
            "pedestrian_activity": [0],
            "cyclist_activity": [0],
            "school_zone": [0],
            "market_zone": [0],
            "urban": [0],
            "intersection_density": [0],
            "divided_road": [1],
        }
    )
    result = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(result.iloc[0]) == 70.0


def test_gap_score_alignment_is_100():
    score = compute_speed_limit_gap_score(
        pd.Series([30.0]),
        pd.Series([30.0]),
    )
    assert float(score.iloc[0]) == 100.0


def test_gap_score_large_positive_gap_is_low():
    score = compute_speed_limit_gap_score(
        pd.Series([60.0]),
        pd.Series([30.0]),
    )
    assert float(score.iloc[0]) == 25.0


def test_operating_speed_score_compliance_is_100():
    score = compute_operating_speed_score(
        pd.Series([50.0]),
        pd.Series([50.0]),
    )
    assert float(score.iloc[0]) == 100.0


def test_operating_speed_score_excess_is_penalized():
    score = compute_operating_speed_score(
        pd.Series([68.0]),
        pd.Series([60.0]),
    )
    assert float(score.iloc[0]) == pytest.approx(73.33, abs=0.01)


def test_vru_score_high_exposure_is_low():
    df = pd.DataFrame(
        {
            "pedestrian_activity": [1],
            "cyclist_activity": [1],
            "ptw_activity": [1],
            "crossing_density": [1],
            "commercial_frontage": [1],
            "transit_stop": [1],
            "school_zone": [1],
        }
    )
    score = compute_vru_exposure_score(df)
    assert float(score.iloc[0]) == 0.0


def test_context_score_high_risk_is_low():
    df = pd.DataFrame(
        {
            "urban": [1],
            "intersection_density": [1],
            "roadside_activity": [1],
            "non_separated_traffic": [1],
        }
    )
    score = compute_context_score(df)
    assert float(score.iloc[0]) == 0.0


def test_composite_score_matches_weighted_formula():
    weights = {
        "speed_gap": 0.35,
        "operating_speed": 0.20,
        "vru_exposure": 0.25,
        "road_context": 0.20,
    }
    score = compute_speed_safety_score(
        pd.Series([25.0]),
        pd.Series([73.3333333]),
        pd.Series([5.0]),
        pd.Series([0.0]),
        weights,
    )
    assert float(score.iloc[0]) == pytest.approx(24.67, abs=0.01)


def test_priority_label_escalates_to_high_priority_review():
    config = ScoreConfig()
    labels = assign_priority_label(
        pd.Series([72.0]),
        posted_speed_limit_kph=pd.Series([60.0]),
        safe_system_reference_speed_kph=pd.Series([30.0]),
        vru_exposure_score=pd.Series([20.0]),
        config=config,
    )
    assert labels.iloc[0] == "high_priority_review"


def test_priority_label_without_escalation_stays_monitor():
    config = ScoreConfig()
    labels = assign_priority_label(
        pd.Series([72.0]),
        posted_speed_limit_kph=pd.Series([50.0]),
        safe_system_reference_speed_kph=pd.Series([30.0]),
        vru_exposure_score=pd.Series([20.0]),
        config=config,
    )
    assert labels.iloc[0] == "monitor"


def test_score_segments_returns_expected_columns_and_label():
    df = pd.DataFrame(
        {
            "segment_id": ["seg_001"],
            "posted_speed_limit_kph": [60.0],
            "operating_speed_kph": [68.0],
            "pedestrian_activity": [1],
            "cyclist_activity": [1],
            "school_zone": [0],
            "market_zone": [0],
            "urban": [1],
            "intersection_density": [1],
            "divided_road": [0],
            "ptw_activity": [1],
            "crossing_density": [1],
            "commercial_frontage": [1],
            "transit_stop": [1],
            "roadside_activity": [1],
            "non_separated_traffic": [1],
        }
    )
    result = score_segments(df)
    expected = {
        "safe_system_reference_speed_kph",
        "speed_limit_gap_score",
        "operating_speed_score",
        "vru_exposure_score",
        "context_score",
        "speed_safety_score",
        "priority_label",
    }
    assert expected.issubset(result.columns)
    assert float(result.loc[0, "speed_limit_gap_score"]) == 25.0
    assert float(result.loc[0, "operating_speed_score"]) == pytest.approx(73.33, abs=0.01)
    assert float(result.loc[0, "vru_exposure_score"]) == 5.0
    assert float(result.loc[0, "context_score"]) == 0.0
    assert float(result.loc[0, "speed_safety_score"]) == pytest.approx(24.67, abs=0.01)
    assert result.loc[0, "priority_label"] == "high_priority_review"


def test_load_score_config_falls_back_to_defaults_when_missing(tmp_path):
    missing_path = tmp_path / "missing_scoring.yaml"
    config = load_score_config(str(missing_path))
    assert config.weights["speed_gap"] == 0.35
    assert config.weights["operating_speed"] == 0.20
    assert config.weights["vru_exposure"] == 0.25
    assert config.weights["road_context"] == 0.20
    assert config.thresholds["high_priority_review"] == 40.0
    assert config.thresholds["review"] == 60.0
    assert config.thresholds["monitor"] == 80.0
