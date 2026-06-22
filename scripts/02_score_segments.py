
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import geopandas as gpd
import pandas as pd

from src.ai4saferroads.speed_safety_score import load_score_config, score_segments

PREPARED_DIR = Path("outputs/prepared")
SCORED_DIR = Path("outputs/scored")

COUNTRY_FILES = {
    "thailand": PREPARED_DIR / "thailand_prepared.geojson",
    "maharashtra": PREPARED_DIR / "maharashtra_prepared.geojson",
}

def main() -> None:
    print("Loading scoring configuration...")
    config = load_score_config()
    SCORED_DIR.mkdir(parents=True, exist_ok=True)

    for country, path in COUNTRY_FILES.items():
        if not path.exists():
            print(f"Skipping {country}: missing {path}")
            continue

        print(f"\nScoring {country}: {path}")
        gdf = gpd.read_file(path)

        if "score_eligible_flag" in gdf.columns:
            gdf = gdf[gdf["score_eligible_flag"] == 1].copy()

        print(f"Eligible segments: {len(gdf)}")
        if len(gdf) == 0:
            print("No eligible segments, skipping.")
            continue

        scored = score_segments(gdf, config)

        csv_path = SCORED_DIR / f"{country}_scored.csv"
        geojson_path = SCORED_DIR / f"{country}_scored.geojson"

        pd.DataFrame(scored.drop(columns="geometry", errors="ignore")).to_csv(csv_path, index=False)
        if "geometry" in scored.columns:
            gpd.GeoDataFrame(scored, geometry="geometry", crs=gdf.crs).to_file(geojson_path, driver="GeoJSON")

        print(f"Saved CSV: {csv_path}")
        print(f"Saved GeoJSON: {geojson_path}")
        print(scored['priority_label'].value_counts(dropna=False).to_string())
        print(scored['speed_safety_score'].describe().round(2).to_string())

if __name__ == "__main__":
    main()
