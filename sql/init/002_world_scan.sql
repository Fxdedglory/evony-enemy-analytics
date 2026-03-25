-- Version: v0.1.0 | Date: 2026-03-25

create schema if not exists ops;

create table if not exists raw.bronze_world_scan_raw (
    world_scan_id text primary key,
    ingested_at_utc timestamptz not null,
    command_text text not null,
    scan_type text not null,
    x1 integer not null,
    y1 integer not null,
    x2 integer not null,
    y2 integer not null,
    maxtowns integer not null,
    returned_rows integer not null,
    is_saturated boolean not null,
    raw_text text not null
);

create table if not exists raw.bronze_world_scan_rows (
    world_scan_id text not null,
    ingested_at_utc timestamptz not null,
    scan_scope text not null,
    tile_key text not null,
    x1 integer not null,
    y1 integer not null,
    x2 integer not null,
    y2 integer not null,
    coords text not null,
    x integer,
    y integer,
    coord_key text,
    state text,
    level integer,
    status text,
    distance double precision,
    castle text,
    owner text,
    owner_key text,
    alliance text,
    alliance_key text,
    prestige bigint,
    honor bigint
);

create table if not exists ops.world_scan_tiles (
    tile_key text primary key,
    parent_tile_key text,
    depth integer not null,
    x1 integer not null,
    y1 integer not null,
    x2 integer not null,
    y2 integer not null,
    maxtowns integer not null,
    status text not null,
    last_scan_id text,
    last_scanned_at_utc timestamptz,
    last_returned_rows integer,
    is_saturated boolean,
    needs_rescan boolean not null default false,
    notes text
);

create index if not exists ix_bronze_world_scan_rows_world_scan_id
    on raw.bronze_world_scan_rows(world_scan_id);

create index if not exists ix_bronze_world_scan_rows_tile_key
    on raw.bronze_world_scan_rows(tile_key);

create index if not exists ix_bronze_world_scan_rows_coord_key
    on raw.bronze_world_scan_rows(coord_key);

create index if not exists ix_world_scan_tiles_status
    on ops.world_scan_tiles(status);