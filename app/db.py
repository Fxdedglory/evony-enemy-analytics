# Version: v0.1.2 | Date: 2026-03-25
from pathlib import Path
import sys
from datetime import datetime, timezone

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import create_engine, text
from config import sqlalchemy_url


def get_engine():
    return create_engine(sqlalchemy_url(), future=True)


def test_connection() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    return True


def insert_bronze_raw(scan_id: str, raw_text: str, row_count: int) -> None:
    engine = get_engine()
    payload = pd.DataFrame(
        [
            {
                "scan_id": scan_id,
                "ingested_at_utc": datetime.now(timezone.utc),
                "raw_text": raw_text,
                "row_count": row_count,
            }
        ]
    )
    payload.to_sql("bronze_enemy_scan_raw", engine, schema="raw", if_exists="append", index=False)


def insert_bronze_rows(df: pd.DataFrame) -> None:
    engine = get_engine()
    df.to_sql("bronze_enemy_scan_rows", engine, schema="raw", if_exists="append", index=False)


def insert_world_scan_raw(
    world_scan_id: str,
    command_text: str,
    scan_type: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    maxtowns: int,
    returned_rows: int,
    is_saturated: bool,
    raw_text: str,
) -> None:
    engine = get_engine()
    payload = pd.DataFrame(
        [
            {
                "world_scan_id": world_scan_id,
                "ingested_at_utc": datetime.now(timezone.utc),
                "command_text": command_text,
                "scan_type": scan_type,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "maxtowns": maxtowns,
                "returned_rows": returned_rows,
                "is_saturated": is_saturated,
                "raw_text": raw_text,
            }
        ]
    )
    payload.to_sql("bronze_world_scan_raw", engine, schema="raw", if_exists="append", index=False)


def insert_world_scan_rows(df: pd.DataFrame) -> None:
    engine = get_engine()
    df.to_sql("bronze_world_scan_rows", engine, schema="raw", if_exists="append", index=False)


def upsert_world_scan_tile(
    tile_key: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    maxtowns: int,
    status: str,
    returned_rows: int,
    is_saturated: bool,
    world_scan_id: str,
) -> None:
    engine = get_engine()
    sql = text("""
        insert into ops.world_scan_tiles (
            tile_key, parent_tile_key, depth, x1, y1, x2, y2, maxtowns,
            status, last_scan_id, last_scanned_at_utc, last_returned_rows, is_saturated, needs_rescan, notes
        )
        values (
            :tile_key, null, 0, :x1, :y1, :x2, :y2, :maxtowns,
            :status, :world_scan_id, now(), :returned_rows, :is_saturated, false, null
        )
        on conflict (tile_key) do update set
            x1 = excluded.x1,
            y1 = excluded.y1,
            x2 = excluded.x2,
            y2 = excluded.y2,
            maxtowns = excluded.maxtowns,
            status = excluded.status,
            last_scan_id = excluded.last_scan_id,
            last_scanned_at_utc = excluded.last_scanned_at_utc,
            last_returned_rows = excluded.last_returned_rows,
            is_saturated = excluded.is_saturated,
            needs_rescan = false
    """)
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "tile_key": tile_key,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "maxtowns": maxtowns,
                "status": status,
                "world_scan_id": world_scan_id,
                "returned_rows": returned_rows,
                "is_saturated": is_saturated,
            },
        )
def mark_world_scan_tile_status(tile_key: str, status: str, notes: str | None = None) -> None:
    engine = get_engine()
    sql = text("""
        update ops.world_scan_tiles
        set
            status = :status,
            notes = coalesce(:notes, notes)
        where tile_key = :tile_key
    """)
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "tile_key": tile_key,
                "status": status,
                "notes": notes,
            },
        )

def split_world_scan_tile(tile_key: str) -> int:
    engine = get_engine()

    fetch_sql = text("""
        select tile_key, parent_tile_key, depth, x1, y1, x2, y2, maxtowns, status
        from ops.world_scan_tiles
        where tile_key = :tile_key
    """)

    update_parent_sql = text("""
        update ops.world_scan_tiles
        set status = 'split',
            notes = coalesce(notes, '') || case when notes is null or notes = '' then '' else ' | ' end || 'auto-split into child quadrants'
        where tile_key = :tile_key
    """)

    insert_child_sql = text("""
        insert into ops.world_scan_tiles (
            tile_key, parent_tile_key, depth, x1, y1, x2, y2, maxtowns, status,
            last_scan_id, last_scanned_at_utc, last_returned_rows, is_saturated, needs_rescan, notes
        )
        values (
            :tile_key, :parent_tile_key, :depth, :x1, :y1, :x2, :y2, :maxtowns, 'pending',
            null, null, null, null, false, 'created by parent split'
        )
        on conflict (tile_key) do nothing
    """)

    with engine.begin() as conn:
        parent = conn.execute(fetch_sql, {"tile_key": tile_key}).mappings().first()
        if not parent:
            raise ValueError(f"Tile not found: {tile_key}")

        x1, y1, x2, y2 = parent["x1"], parent["y1"], parent["x2"], parent["y2"]

        if x1 == x2 and y1 == y2:
            return 0

        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2

        children = [
            (x1, y1, mid_x, mid_y),
            (mid_x + 1, y1, x2, mid_y),
            (x1, mid_y + 1, mid_x, y2),
            (mid_x + 1, mid_y + 1, x2, y2),
        ]

        valid_children = []
        for cx1, cy1, cx2, cy2 in children:
            if cx1 <= cx2 and cy1 <= cy2:
                valid_children.append(
                    {
                        "tile_key": f"{cx1}_{cy1}__{cx2}_{cy2}",
                        "parent_tile_key": parent["tile_key"],
                        "depth": int(parent["depth"]) + 1,
                        "x1": cx1,
                        "y1": cy1,
                        "x2": cx2,
                        "y2": cy2,
                        "maxtowns": int(parent["maxtowns"]),
                    }
                )

        conn.execute(update_parent_sql, {"tile_key": tile_key})

        inserted = 0
        for child in valid_children:
            result = conn.execute(insert_child_sql, child)
            inserted += result.rowcount if result.rowcount is not None else 0

    return inserted


def mark_tiles_for_rescan(days_old: int = 7) -> int:
    engine = get_engine()
    sql = text("""
        update ops.world_scan_tiles
        set needs_rescan = true,
            notes = coalesce(notes, '') || case when notes is null or notes = '' then '' else ' | ' end || 'marked for rescan'
        where last_scanned_at_utc is not null
          and last_scanned_at_utc < (now() - make_interval(days => :days_old))
          and status in ('complete', 'empty', 'saturated')
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {"days_old": days_old})
        return result.rowcount if result.rowcount is not None else 0