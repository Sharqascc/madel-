from __future__ import annotations

from pathlib import Path
from typing import Optional
import folium
import pandas as pd


COLOR_MAP = {
    "high_priority_review": "#d73027",
    "review": "#fdae61",
    "monitor": "#fee08b",
    "aligned": "#1a9850",
}


def create_priority_map(scored_df: pd.DataFrame, output_path: Optional[str | Path] = None) -> folium.Map:
    center_lat = float(scored_df["latitude"].mean()) if "latitude" in scored_df.columns else 23.5
    center_lon = float(scored_df["longitude"].mean()) if "longitude" in scored_df.columns else 90.2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="CartoDB positron")

    if {"latitude", "longitude"}.issubset(scored_df.columns):
        for _, row in scored_df.iterrows():
            color = COLOR_MAP.get(row["priority_label"], "#808080")
            popup = (
                f"Segment: {row.get('segment_id', 'NA')}<br>"
                f"Score: {row.get('speed_safety_score', 'NA')}<br>"
                f"Priority: {row.get('priority_label', 'NA')}<br>"
                f"Posted: {row.get('posted_speed_limit_kph', 'NA')} km/h<br>"
                f"Reference: {row.get('safe_system_reference_speed_kph', 'NA')} km/h"
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                opacity=0.9,
                popup=popup,
                tooltip=f"{row.get('segment_id', 'NA')} | {row.get('priority_label', 'NA')}",
            ).add_to(m)

    legend = """
    <div style="
        position: fixed;
        bottom: 40px; left: 40px; width: 220px;
        background: white; z-index: 9999; border: 2px solid #999;
        padding: 12px; font-size: 14px;">
      <b>Priority labels</b><br>
      <div><span style="display:inline-block;width:14px;height:14px;background:#d73027;margin-right:8px;"></span>high_priority_review</div>
      <div><span style="display:inline-block;width:14px;height:14px;background:#fdae61;margin-right:8px;"></span>review</div>
      <div><span style="display:inline-block;width:14px;height:14px;background:#fee08b;margin-right:8px;"></span>monitor</div>
      <div><span style="display:inline-block;width:14px;height:14px;background:#1a9850;margin-right:8px;"></span>aligned</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(output_path))

    return m
