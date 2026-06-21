from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ai4saferroads.speed_safety_score import load_score_config, score_segments


def main() -> None:
    parser = argparse.ArgumentParser(description="Score road segments using Safe System speed logic.")
    parser.add_argument("--input", required=True, help="Path to input CSV with segment attributes.")
    parser.add_argument("--output", required=True, help="Path to output CSV for scored segments.")
    parser.add_argument(
        "--config",
        default="configs/scoring.yaml",
        help="Path to scoring config YAML.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    config = load_score_config(args.config)
    scored = score_segments(df, config=config)
    scored.to_csv(output_path, index=False)

    print(f"Scored {len(scored)} segments")
    print(f"Saved scored output to: {output_path}")


if __name__ == "__main__":
    main()
