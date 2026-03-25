select
    coalesce(nullif(owner_name, ''), '(blank)') as owner_name,
    coalesce(nullif(alliance_name, ''), '(blank)') as alliance_name,
    count(*) as city_count,
    avg(distance) as avg_distance,
    max(prestige) as max_prestige,
    max(honor) as max_honor,
    sum(times_seen) as total_sightings
from {{ ref('enemy_master') }}
group by 1,2
order by city_count desc, max_prestige desc nulls last