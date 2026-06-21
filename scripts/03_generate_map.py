from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a simple review map/table artifact from scored segments.")
    parser.add_argument("--input", required=True, help="Path to scored CSV.")
    parser.add_argument("--output", required=True, help="Path to HTML output.")
    parser.add_argument(
        "--top-n",
        type=int,
        default=200,
        help="Number of highest-priority rows to include in the HTML artifact.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    sort_cols = [c for c in ["speed_safety_score"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=True)

    top_n = min(args.top_n, len(df))
    preview = df.head(top_n)

    title = "AI for Safer Roads Priority Review Map"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ margin-bottom: 8px; }}
    p {{ margin-top: 0; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid #d0d0d0; padding: 8px; text-align: left; }}
    th {{ background: #f3f3f3; position: sticky; top: 0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .meta {{ margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">Showing top {top_n} highest-priority scored segments ordered by lowest speed safety score.</p>
  {preview.to_html(index=False, border=0)}
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")

    print(f"Loaded {len(df)} scored segments")
    print(f"Saved HTML artifact to: {output_path}")


if __name__ == "__main__":
    main()
