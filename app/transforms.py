# Version: v0.1.1 | Date: 2026-03-25
from datetime import datetime, timezone
import pandas as pd


def build_bronze_rows(df: pd.DataFrame, scan_id: str) -> pd.DataFrame:
    out = df.copy()
    now = datetime.now(timezone.utc)
    out["scan_id"] = scan_id
    out["ingested_at_utc"] = now
    out["coord_key"] = out["x"].astype(str) + "," + out["y"].astype(str)
    out["owner_key"] = out["owner"].fillna("").str.strip().str.lower()
    out["alliance_key"] = out["alliance"].fillna("").str.strip().str.lower()

    return out[
        [
            "scan_id", "ingested_at_utc", "coords", "x", "y", "coord_key",
            "state", "level", "status", "distance", "castle", "owner",
            "owner_key", "alliance", "alliance_key", "prestige", "honor"
        ]
    ]


def build_world_scan_rows(
    df: pd.DataFrame,
    world_scan_id: str,
    tile_key: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> pd.DataFrame:
    out = df.copy()
    now = datetime.now(timezone.utc)
    out["world_scan_id"] = world_scan_id
    out["ingested_at_utc"] = now
    out["scan_scope"] = "world"
    out["tile_key"] = tile_key
    out["x1"] = x1
    out["y1"] = y1
    out["x2"] = x2
    out["y2"] = y2
    out["coord_key"] = out["x"].astype(str) + "," + out["y"].astype(str)
    out["owner_key"] = out["owner"].fillna("").str.strip().str.lower()
    out["alliance_key"] = out["alliance"].fillna("").str.strip().str.lower()

    return out[
        [
            "world_scan_id", "ingested_at_utc", "scan_scope", "tile_key",
            "x1", "y1", "x2", "y2",
            "coords", "x", "y", "coord_key",
            "state", "level", "status", "distance", "castle", "owner",
            "owner_key", "alliance", "alliance_key", "prestige", "honor"
        ]
    ]