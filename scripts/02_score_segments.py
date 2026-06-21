#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai4saferroads.data_loader import load_or_generate_segments
from ai4saferroads.geo_visualization import create_priority_map
from ai4saferroads.speed_safety_score import load_score_config, score_segments


def main() -> None:
    input_path = REPO_ROOT / "data" / "prepared_segments.csv"
    output_dir = REPO_ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)
    map_dir = output_dir / "maps"
    map_dir.mkdir(exist_ok=True)

    print("Loading scoring configuration...")
    config = load_score_config(REPO_ROOT / "configs" / "scoring.yaml")

    if input_path.exists():
        print(f"Loading real data from {input_path}")
        df = load_or_generate_segments(input_path=input_path)
    else:
        print("Prepared dataset not found; generating synthetic reviewer-friendly demo data.")
        df = load_or_generate_segments(input_path=None, n=250, seed=42)

    print(f"Scoring {len(df)} segments...")
    scored = score_segments(df, config=config)

    csv_path = output_dir / "scored_segments.csv"
    scored.to_csv(csv_path, index=False)

    html_map_path = map_dir / "priority_map.html"
    create_priority_map(scored, output_path=html_map_path)

    print(f"Saved scored segments to: {csv_path}")
    print(f"Saved interactive map to: {html_map_path}")
    print("\nPriority label counts:")
    print(scored["priority_label"].value_counts(dropna=False).to_string())
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
    preview = scored[cols].head(10)
    print("\nPreview:")
    print(preview.to_string(index=False))


if __name__ == "__main__":
    main()
