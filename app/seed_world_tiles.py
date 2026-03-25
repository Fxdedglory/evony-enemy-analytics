# Version: v0.1.0 | Date: 2026-03-25
from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import get_engine
from sqlalchemy import text


def build_tile_key(x1: int, y1: int, x2: int, y2: int) -> str:
    return f"{x1}_{y1}__{x2}_{y2}"


def seed_initial_tiles(tile_size: int = 100, map_max: int = 799, maxtowns: int = 1000) -> int:
    rows = []
    for y1 in range(0, map_max + 1, tile_size):
        for x1 in range(0, map_max + 1, tile_size):
            x2 = min(x1 + tile_size - 1, map_max)
            y2 = min(y1 + tile_size - 1, map_max)
            rows.append(
                {
                    "tile_key": build_tile_key(x1, y1, x2, y2),
                    "parent_tile_key": None,
                    "depth": 0,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "maxtowns": maxtowns,
                    "status": "pending",
                    "notes": "seeded initial world queue",
                }
            )

    engine = get_engine()
    sql = text("""
        insert into ops.world_scan_tiles (
            tile_key, parent_tile_key, depth, x1, y1, x2, y2, maxtowns, status, notes
        )
        values (
            :tile_key, :parent_tile_key, :depth, :x1, :y1, :x2, :y2, :maxtowns, :status, :notes
        )
        on conflict (tile_key) do nothing
    """)
    with engine.begin() as conn:
        conn.execute(sql, rows)

    return len(rows)


if __name__ == "__main__":
    inserted = seed_initial_tiles()
    print(f"Seeded up to {inserted} tiles.")