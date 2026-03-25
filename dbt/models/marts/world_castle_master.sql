select *
from (
    select
        coord_key,
        x,
        y,
        coords,
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
        honor,
        tile_key,
        min(ingested_at_utc) over (partition by coord_key) as first_seen_at_utc,
        max(ingested_at_utc) over (partition by coord_key) as last_seen_at_utc,
        count(*) over (partition by coord_key) as times_seen,
        world_scan_id as latest_world_scan_id,
        row_number() over (
            partition by coord_key
            order by ingested_at_utc desc, world_scan_id desc
        ) as rn
    from {{ ref('stg_world_castle_sightings') }}
) ranked
where rn = 1