select
    scan_id,
    ingested_at_utc,
    coords,
    x,
    y,
    coord_key,
    state,
    level,
    status,
    distance,
    castle_name,
    owner_name,
    owner_key,
    alliance_name,
    alliance_key,
    prestige,
    honor
from {{ ref('stg_bronze_enemy_scan_rows') }}
where coord_key is not null