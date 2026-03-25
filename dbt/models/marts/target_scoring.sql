select
    coord_key,
    owner_name,
    alliance_name,
    x,
    y,
    distance,
    prestige,
    honor,
    times_seen,
    1.0 / (distance + 1) as distance_score,
    ln((prestige + honor + 1)::numeric) as wealth_score,
    times_seen as activity_score,
    (
        (1.0 / (distance + 1)) * 0.5 +
        ln((prestige + honor + 1)::numeric) * 0.3 +
        times_seen * 0.2
    ) as total_score
from {{ ref('enemy_master') }}
order by total_score desc