from __future__ import annotations

import argparse
from pathlib import Path

import folium
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs/scored_segments.csv")
    parser.add_argument("--output", default="outputs/maps/priority_map.html")
    parser.add_argument("--top-n", type=int, default=None)
    return parser.parse_args()


def label_color(label: str) -> str:
    return {
        "aligned": "green",
        "monitor": "blue",
        "review": "orange",
        "high_priority_review": "red",
    }.get(label, "gray")


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Scored dataset not found at {input_path}. Run scripts/02_score_segments.py first."
        )

    df = pd.read_csv(input_path)

    required = {"latitude", "longitude", "priority_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for map generation: {sorted(missing)}")

    if args.top_n is not None:
        df = df.nsmallest(args.top_n, "speed_safety_score")

    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

    for _, row in df.iterrows():
        popup = folium.Popup(
            (
                f"<b>Segment:</b> {row.get('segment_id', 'unknown')}<br>"
                f"<b>Priority:</b> {row.get('priority_label', 'unknown')}<br>"
                f"<b>Score:</b> {round(float(row.get('speed_safety_score', 0.0)), 2)}<br>"
                f"<b>Posted speed:</b> {row.get('posted_speed_limit_kph', 'NA')}<br>"
                f"<b>Reference speed:</b> {row.get('safe_system_reference_speed_kph', 'NA')}"
            ),
            max_width=300,
        )

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color=label_color(str(row["priority_label"])),
            fill=True,
            fill_opacity=0.8,
            popup=popup,
        ).add_to(fmap)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(output_path)
    print(f"Saved interactive map to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
