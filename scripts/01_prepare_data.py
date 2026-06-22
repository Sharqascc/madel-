#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai4saferroads.adb_adapter import prepare_data_for_scoring

def main():
    data_dir = ROOT / "data"
    out_dir = ROOT / "outputs" / "prepared"
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("ADB_Innovation_Thailand.geojson", "thailand_prepared.geojson", "Thailand"),
        ("ADB_Innovation_Maharashtra.geojson", "maharashtra_prepared.geojson", "Maharashtra"),
    ]

    for infile, outfile, country in jobs:
        path = data_dir / infile
        if path.exists():
            print(f"Preparing {country}: {path}")
            out = prepare_data_for_scoring(path, out_dir / outfile, country)
            print(country, len(out), "rows")
            print(out[[
                "segment_id","posted_speed_limit_kph","operating_speed_kph","road_type","area_type",
                "pedestrian_presence","cyclist_presence","ptw_presence","urban_flag",
                "intersection_density_flag","data_quality_flag"
            ]].head(3).to_string(index=False))
        else:
            print(f"Missing input: {path}")

if __name__ == "__main__":
    main()
