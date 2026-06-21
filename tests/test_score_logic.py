import pandas as pd

from src.ai4saferroads.speed_safety_score import (
    ScoreConfig,
    assign_priority_label,
    compute_context_score,
    compute_operating_speed_score,
    compute_speed_limit_gap_score,
    compute_vru_exposure_score,
    derive_safe_system_reference_speed,
    score_segments,
)


def test_gap_score_inversion():
    posted = pd.Series([30.0, 60.0, 80.0])
    ref = pd.Series([30.0, 30.0, 30.0])
    scores = compute_speed_limit_gap_score(posted, ref)
    assert list(scores.round(2)) == [100.0, 25.0, 0.0]


def test_operating_speed_score_inversion():
    operating = pd.Series([30.0, 68.0, 95.0])
    posted = pd.Series([30.0, 60.0, 60.0])
    scores = compute_operating_speed_score(operating, posted)
    assert list(scores.round(2)) == [100.0, 73.33, 0.0]


def test_vru_score_penalizes_exposure():
    df = pd.DataFrame({
        "pedestrian_activity": [0, 1],
        "cyclist_activity": [0, 1],
        "ptw_activity": [0, 1],
        "crossing_density": [0, 1],
        "commercial_frontage": [0, 1],
        "transit_stop": [0, 1],
        "school_zone": [0, 1],
    })
    scores = compute_vru_exposure_score(df)
    assert float(scores.iloc[0]) == 100.0
    assert float(scores.iloc[1]) == 0.0


def test_context_score_penalizes_conflict():
    df = pd.DataFrame({
        "urban": [0, 1],
        "intersection_density": [0, 1],
        "roadside_activity": [0, 1],
        "non_separated_traffic": [0, 1],
    })
    scores = compute_context_score(df)
    assert float(scores.iloc[0]) == 100.0
    assert float(scores.iloc[1]) == 0.0


def test_reference_speed_mixed_vru_is_30():
    df = pd.DataFrame({
        "pedestrian_activity": [1],
        "cyclist_activity": [0],
        "school_zone": [0],
        "market_zone": [0],
        "urban": [1],
        "intersection_density": [1],
        "divided_road": [0],
    })
    ref = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(ref.iloc[0]) == 30.0


def test_reference_speed_side_conflict_is_50():
    df = pd.DataFrame({
        "pedestrian_activity": [0],
        "cyclist_activity": [0],
        "school_zone": [0],
        "market_zone": [0],
        "urban": [1],
        "intersection_density": [3],
        "divided_road": [0],
    })
    ref = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(ref.iloc[0]) == 50.0


def test_reference_speed_head_on_is_70():
    df = pd.DataFrame({
        "pedestrian_activity": [0],
        "cyclist_activity": [0],
        "school_zone": [0],
        "market_zone": [0],
        "urban": [0],
        "intersection_density": [0],
        "divided_road": [1],
    })
    ref = derive_safe_system_reference_speed(df, ScoreConfig())
    assert float(ref.iloc[0]) == 70.0


def test_priority_thresholds():
    score = pd.Series([85.0, 65.0, 45.0, 25.0])
    labels = assign_priority_label(score, config=ScoreConfig())
    assert list(labels) == ["aligned", "monitor", "review", "high_priority_review"]


def test_vru_escalation_override():
    score = pd.Series([72.0])
    posted = pd.Series([60.0])
    ref = pd.Series([30.0])
    vru_score = pd.Series([20.0])
    labels = assign_priority_label(
        score,
        posted_speed_limit_kph=posted,
        safe_system_reference_speed_kph=ref,
        vru_exposure_score=vru_score,
        config=ScoreConfig(),
    )
    assert labels.iloc[0] == "high_priority_review"


def test_score_segments_end_to_end():
    df = pd.DataFrame({
        "segment_id": ["seg_1", "seg_2"],
        "posted_speed_limit_kph": [30.0, 60.0],
        "operating_speed_kph": [28.0, 68.0],
        "pedestrian_activity": [1, 1],
        "cyclist_activity": [0, 1],
        "ptw_activity": [0, 1],
        "crossing_density": [0, 1],
        "commercial_frontage": [0, 1],
        "transit_stop": [0, 1],
        "school_zone": [1, 0],
        "market_zone": [0, 0],
        "urban": [1, 1],
        "intersection_density": [1, 1],
        "roadside_activity": [0, 1],
        "non_separated_traffic": [0, 1],
        "divided_road": [0, 0],
    })
    out = score_segments(df, ScoreConfig())
    assert "speed_safety_score" in out.columns
    assert "priority_label" in out.columns
    assert out.shape[0] == 2
