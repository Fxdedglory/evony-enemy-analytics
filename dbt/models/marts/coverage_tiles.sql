select
    tile_key,
    parent_tile_key,
    depth,
    x1,
    y1,
    x2,
    y2,
    maxtowns,
    status,
    last_scan_id,
    last_scanned_at_utc,
    last_returned_rows,
    is_saturated,
    needs_rescan,
    notes
from ops.world_scan_tiles
order by depth, y1, x1