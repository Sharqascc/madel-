
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
import geopandas as gpd

class ADBDataAdapter:
    ROAD_CLASS_MAP = {
        "motorway": "expressway",
        "trunk": "arterial",
        "primary": "primary",
        "secondary": "secondary",
    }

    def load_data(self, file_path: Path) -> gpd.GeoDataFrame:
        return gpd.read_file(file_path)

    def _num(self, v, default=np.nan):
        try:
            if v is None or (isinstance(v, str) and v.strip() == ""):
                return default
            return float(v)
        except Exception:
            return default

    def map_road_class(self, road_class: str) -> str:
        if road_class is None:
            return "unknown"
        s = str(road_class).strip().lower()
        if s in self.ROAD_CLASS_MAP:
            return self.ROAD_CLASS_MAP[s]
        if "motor" in s or "express" in s:
            return "expressway"
        if "trunk" in s or "arterial" in s:
            return "arterial"
        if "primary" in s:
            return "primary"
        if "secondary" in s or "collector" in s:
            return "secondary"
        if "local" in s or "street" in s:
            return "local"
        return "unknown"

    def map_area_type(self, land_use: str) -> str:
        if land_use is None or pd.isna(land_use):
            return "unknown"
        s = str(land_use).strip().upper()
        if s == "URBAN":
            return "urban"
        if s == "RURAL":
            return "rural"
        return "unknown"

    def derive_intersection_density_flag(self, row: pd.Series) -> int:
        length_m = self._num(row.get("Shape_Length", row.get("RoadLength")), np.nan)
        area_type = self.map_area_type(row.get("LandUse"))
        road_type = self.map_road_class(row.get("RoadClass"))
        if np.isnan(length_m):
            return 1 if area_type == "urban" and road_type in {"secondary", "local", "primary"} else 0
        if area_type == "urban" and length_m < 5000:
            return 1
        if area_type == "urban" and road_type in {"secondary", "local"} and length_m < 8000:
            return 1
        return 0

    def compute_vru_proxies(self, row: pd.Series) -> Dict[str, int]:
        area_type = self.map_area_type(row.get("LandUse"))
        road_type = self.map_road_class(row.get("RoadClass"))
        urban = area_type == "urban"
        pedestrian = int(urban and road_type in {"secondary", "local", "primary"})
        cyclist = int(urban and road_type in {"secondary", "local"})
        ptw = int(urban and road_type != "expressway")
        return {
            "pedestrian_presence": pedestrian,
            "cyclist_presence": cyclist,
            "ptw_presence": ptw,
        }

    def compute_context_proxies(self, row: pd.Series) -> Dict[str, int]:
        area_type = self.map_area_type(row.get("LandUse"))
        road_type = self.map_road_class(row.get("RoadClass"))
        urban_flag = int(area_type == "urban")
        roadside_activity_flag = int(area_type == "urban" and road_type in {"secondary", "local", "primary"})
        non_separated_traffic_flag = int(road_type != "expressway")
        intersection_density_flag = self.derive_intersection_density_flag(row)
        return {
            "urban_flag": urban_flag,
            "intersection_density_flag": intersection_density_flag,
            "roadside_activity_flag": roadside_activity_flag,
            "non_separated_traffic_flag": non_separated_traffic_flag,
        }

    def adapt_row(self, row: pd.Series, idx: int, country: str) -> Dict[str, Any]:
        operating = self._num(row.get("F85thPercentileSpeed"), np.nan)
        if np.isnan(operating) or operating <= 0:
            operating = self._num(row.get("MedianSpeed"), np.nan)

        posted = self._num(row.get("SpeedLimit"), np.nan)
        sample_size = self._num(row.get("SampleSize_avg", row.get("Sample_Size_Total")), 0.0)
        weighted_sample = self._num(row.get("WeightedSample"), 0.0)
        percent_over = self._num(row.get("PercentOverLimit"), np.nan)
        ranked_pct = self._num(row.get("RankedPercentile"), np.nan)

        segment_id = row.get("OBJECTID", row.get("OvertureID", row.get("DISSOLVE_ID", idx)))
        raw_road_class = row.get("RoadClass")
        if raw_road_class is None or (isinstance(raw_road_class, float) and np.isnan(raw_road_class)):
            raw_road_class = row.get("class")
        road_type = self.map_road_class(raw_road_class)
        area_type = self.map_area_type(row.get("LandUse"))

        if not np.isnan(operating) and operating <= 0:
            operating = np.nan

        result = {
            "segment_id": str(segment_id),
            "country": country,
            "posted_speed_limit_kph": posted,
            "operating_speed_kph": operating,
            "road_type": road_type,
            "area_type": area_type,
            "sample_size": sample_size,
            "weighted_sample": weighted_sample,
            "percent_over_limit": percent_over,
            "ranked_percentile": ranked_pct,
            "speed_gap_kph": operating - posted if not np.isnan(operating) and not np.isnan(posted) else np.nan,
            "source_name": row.get("english_ro", row.get("names_primary")),
            "source_streetimagelink": row.get("StreetImageLink"),
            "source_analysis_status": row.get("AnalysisStatus"),
            "geometry": row.geometry,
        }

        result.update(self.compute_vru_proxies(row))
        result.update(self.compute_context_proxies(row))

        result["data_quality_flag"] = int(
            (not np.isnan(result["posted_speed_limit_kph"])) and
            (not np.isnan(result["operating_speed_kph"])) and
            (result["weighted_sample"] > 0)
        )
        result["score_eligible_flag"] = int(
            (not np.isnan(result["posted_speed_limit_kph"])) and
            (not np.isnan(result["operating_speed_kph"])) and
            (result["weighted_sample"] >= 1)
        )
        result["context_only_flag"] = int(
            (result["road_type"] != "unknown") or (result["area_type"] != "unknown")
        )
        return result

    def adapt_dataset(self, gdf: gpd.GeoDataFrame, country: str) -> gpd.GeoDataFrame:
        records = [self.adapt_row(row, idx, country) for idx, row in gdf.iterrows()]
        out = gpd.GeoDataFrame(records, geometry="geometry", crs=gdf.crs)
        return out

def prepare_data_for_scoring(input_path: Path, output_path: Path, country: str) -> gpd.GeoDataFrame:
    adapter = ADBDataAdapter()
    gdf = adapter.load_data(input_path)
    out = adapter.adapt_dataset(gdf, country=country)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(output_path, driver="GeoJSON")
    out.drop(columns=["geometry"], errors="ignore").to_csv(output_path.with_suffix(".csv"), index=False)
    return out
