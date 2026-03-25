-- Version: v0.1.1 | Date: 2026-03-24
select
    scan_id,
    ingested_at_utc,
    coords,
    x,
    y,
    coord_key,
    trim(state) as state,
    level,
    trim(status) as status,
    distance,
    trim(castle) as castle_name,
    trim(owner) as owner_name,
    trim(owner_key) as owner_key,
    trim(alliance) as alliance_name,
    trim(alliance_key) as alliance_key,
    prestige,
    honor
from raw.bronze_enemy_scan_rows
