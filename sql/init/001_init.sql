-- Version: v0.1.0 | Date: 2026-03-24
create schema if not exists raw;
create schema if not exists silver;
create schema if not exists gold;

create table if not exists raw.bronze_enemy_scan_raw (
    scan_id text primary key,
    ingested_at_utc timestamptz not null,
    raw_text text not null,
    row_count integer not null
);

create table if not exists raw.bronze_enemy_scan_rows (
    scan_id text not null,
    ingested_at_utc timestamptz not null,
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

create index if not exists ix_bronze_enemy_scan_rows_scan_id on raw.bronze_enemy_scan_rows(scan_id);
create index if not exists ix_bronze_enemy_scan_rows_coord_key on raw.bronze_enemy_scan_rows(coord_key);
create index if not exists ix_bronze_enemy_scan_rows_owner_key on raw.bronze_enemy_scan_rows(owner_key);
create index if not exists ix_bronze_enemy_scan_rows_alliance_key on raw.bronze_enemy_scan_rows(alliance_key);
