from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ai4saferroads.speed_safety_score import load_score_config, score_segments


DEFAULT_PREPARED = Path("outputs/prepared_segments.csv")
DEFAULT_SCORED = Path("outputs/scored_segments.csv")


def main() -> None:
    print("Loading scoring configuration...")
    config = load_score_config()

    if not DEFAULT_PREPARED.exists():
        raise FileNotFoundError(
            f"Prepared dataset not found at {DEFAULT_PREPARED}. "
            "Run scripts/01_prepare_data.py first."
        )

    df = pd.read_csv(DEFAULT_PREPARED)
    print(f"Scoring {len(df)} segments from: {DEFAULT_PREPARED}")

    scored = score_segments(df, config)

    DEFAULT_SCORED.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(DEFAULT_SCORED, index=False)
    print(f"Saved scored segments to: {DEFAULT_SCORED.resolve()}")

    print("\nPriority label counts:")
    print(scored["priority_label"].value_counts())

    print("\nScore summary:")
    print(scored["speed_safety_score"].describe().round(2).to_string())

    cols = [
        "segment_id",
        "posted_speed_limit_kph",
        "safe_system_reference_speed_kph",
        "speed_limit_gap_score",
        "operating_speed_score",
        "vru_exposure_score",
        "context_score",
        "speed_safety_score",
        "priority_label",
    ]
    preview_cols = [c for c in cols if c in scored.columns]
    print("\nPreview:")
    print(scored[preview_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
