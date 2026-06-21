import argparse
from pathlib import Path

import pandas as pd


PRIORITY_ORDER = {
    "high_priority_review": 0,
    "review": 1,
    "monitor": 2,
    "aligned": 3,
}

PRIORITY_COLORS = {
    "high_priority_review": "#b42318",
    "review": "#f79009",
    "monitor": "#1570ef",
    "aligned": "#12b76a",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an HTML priority review artifact from scored segments.")
    parser.add_argument("--input", required=True, help="Path to scored CSV.")
    parser.add_argument("--output", required=True, help="Path to HTML output.")
    parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Number of top rows to display in the HTML artifact.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    if "priority_label" in df.columns:
        df["_priority_rank"] = df["priority_label"].map(PRIORITY_ORDER).fillna(999)

    sort_cols = [c for c in ["_priority_rank", "speed_safety_score"] if c in df.columns]
    if sort_cols:
        ascending = [True] * len(sort_cols)
        df = df.sort_values(by=sort_cols, ascending=ascending)

    top_n = min(args.top_n, len(df))
    preview = df.head(top_n).copy()

    if "_priority_rank" in preview.columns:
        preview = preview.drop(columns=["_priority_rank"])

    summary_parts = []
    if "priority_label" in df.columns:
        counts = df["priority_label"].value_counts()
        for label in ["high_priority_review", "review", "monitor", "aligned"]:
            if label in counts.index:
                summary_parts.append(f"{label}: {int(counts[label])}")

    badges = []
    for label in ["high_priority_review", "review", "monitor", "aligned"]:
        color = PRIORITY_COLORS[label]
        badges.append(
            f'<span class="badge" style="background:{color};">{label}</span>'
        )

    title = "AI for Safer Roads Priority Review Artifact"
    summary = " | ".join(summary_parts) if summary_parts else "Priority counts unavailable."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #0f172a;
      --muted: #475467;
      --border: #d0d5dd;
    }}
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      color: var(--text);
      background: var(--bg);
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    p {{
      margin-top: 0;
      color: var(--muted);
    }}
    .meta {{
      margin-bottom: 16px;
    }}
    .badges {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 12px 0 16px;
    }}
    .badge {{
      color: white;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: bold;
    }}
    .table-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 14px;
      background: white;
    }}
    th, td {{
      border: 1px solid #e4e7ec;
      padding: 8px;
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      background: #f2f4f7;
      position: sticky;
      top: 0;
    }}
    tr:nth-child(even) {{
      background: #fcfcfd;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">Showing top {top_n} segments prioritized first by policy label and then by lowest speed safety score.</p>
  <p class="meta">{summary}</p>
  <div class="badges">{''.join(badges)}</div>
  <div class="table-wrap">
    {preview.to_html(index=False, border=0)}
  </div>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
