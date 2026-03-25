select
    tile_key,
    count(*) as city_count,
    count(distinct owner_name) as owner_count,
    count(distinct alliance_name) as alliance_count,
    avg(distance) as avg_distance,
    min(distance) as min_distance,
    max(distance) as max_distance,
    max(prestige) as max_prestige,
    max(honor) as max_honor
from {{ ref('world_castle_master') }}
group by tile_key
order by city_count desc, max_prestige desc nulls last