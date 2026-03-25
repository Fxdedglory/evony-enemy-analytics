select
    coalesce(nullif(alliance_name, ''), '(blank)') as alliance_name,
    count(*) as enemy_count,
    avg(distance) as avg_distance,
    min(distance) as min_distance,
    max(distance) as max_distance,
    avg(prestige) as avg_prestige,
    avg(honor) as avg_honor,
    avg(level) as avg_level
from {{ ref('enemy_master') }}
group by 1
order by enemy_count desc, avg_prestige desc nulls last