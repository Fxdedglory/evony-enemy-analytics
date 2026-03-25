# Version: v0.1.0 | Date: 2026-03-24
import csv
import io
from typing import List
import pandas as pd

EXPECTED_COLUMNS = ["Coords", "State", "Level", "Status", "Distance", "Castle", "Owner", "Alliance", "Prestige", "Honor"]

def _extract_csv_lines(raw_text: str) -> List[str]:
    lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('"') and stripped.count('"') >= 2:
            lines.append(stripped)
    return lines

def parse_searchenemies_text(raw_text: str) -> pd.DataFrame:
    csv_lines = _extract_csv_lines(raw_text)
    if not csv_lines:
        raise ValueError("No quoted CSV lines were found in the pasted text.")

    reader = csv.reader(io.StringIO("\n".join(csv_lines)))
    rows = list(reader)
    if not rows:
        raise ValueError("No CSV rows were parsed from the pasted text.")

    header = rows[0]
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected header. Expected {EXPECTED_COLUMNS} but got {header}")

    data_rows = rows[1:]
    if not data_rows:
        raise ValueError("Header found, but no enemy rows were present.")

    df = pd.DataFrame(
        data_rows,
        columns=[
            "coords", "state", "level", "status", "distance",
            "castle", "owner", "alliance", "prestige", "honor"
        ]
    )

    coords = df["coords"].str.split(",", n=1, expand=True)
    df["x"] = pd.to_numeric(coords[0], errors="coerce").astype("Int64")
    df["y"] = pd.to_numeric(coords[1], errors="coerce").astype("Int64")
    df["level"] = pd.to_numeric(df["level"], errors="coerce").astype("Int64")
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce")
    df["prestige"] = pd.to_numeric(df["prestige"], errors="coerce").astype("Int64")
    df["honor"] = pd.to_numeric(df["honor"], errors="coerce").astype("Int64")

    return df


