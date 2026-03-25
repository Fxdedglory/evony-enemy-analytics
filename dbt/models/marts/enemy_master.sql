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
        min(ingested_at_utc) over (partition by coord_key) as first_seen_at_utc,
        max(ingested_at_utc) over (partition by coord_key) as last_seen_at_utc,
        count(*) over (partition by coord_key) as times_seen,
        scan_id as latest_scan_id,
        row_number() over (
            partition by coord_key
            order by ingested_at_utc desc, scan_id desc
        ) as rn
    from {{ ref('stg_enemy_sightings') }}
) ranked
where rn = 1