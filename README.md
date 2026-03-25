````md
# Evony Enemy Analytics

Version: v0.2.5  
Date: 2026-03-25

## Overview

Evony Enemy Analytics is a local analytics system for manual intelligence gathering from Evony command-pane outputs.

It supports:

- hostile scan ingestion from `searchenemies`
- world scan ingestion from `\listcastles x1,y1 x2,y2 maxtowns`
- Bronze / Silver / Gold data modeling
- PostgreSQL + dbt warehouse views
- Streamlit operator console
- owner/alliance search
- top target scoring
- CSV export and copyable hit lists

The system is designed for manual command execution in NeatBot with manual paste-based ingestion into the app.

---

## Current Features

### Bronze ingest
- paste raw `searchenemies` output
- paste raw `listcastles` output
- preserve raw scan text
- preserve parsed row-level observations

### Silver / Gold models
- latest hostile enemy master
- alliance summary
- owner summary
- target scoring
- world castle master
- world tile density summary

### Streamlit UI
- Bronze ingest page
- latest enemies page
- alliance summary page
- owner summary page
- top targets page
- world scan console
- world search
- owner rollup
- alliance rollup

### Exports
- CSV download for summary/result pages
- copyable hit list output for owner/alliance world searches

---

## Stack

- Python
- pandas
- PostgreSQL 16
- dbt
- Streamlit
- Parquet
- Docker
- uv

---

## Project Structure

```text
evony_enemy_analytics/
  app/
    __init__.py
    config.py
    db.py
    parser.py
    transforms.py
    seed_world_tiles.py
    streamlit_app.py
  data/
    bronze/
      raw/
      parsed/
    silver/
    gold/
  dbt/
    models/
      staging/
      marts/
  sql/
    init/
  docs/
  exports/
  logs/
  tests/
  tree/
  .dbt/
  .env.example
  .gitignore
  docker-compose.yml
  requirements.txt
  dbt_project.yml
  README.md
````

---

## Data Flow

### Source commands

* `searchenemies`
* `searchcastle <owner>` if needed later
* `\listcastles x1,y1 x2,y2 maxtowns`

### Bronze

Raw pasted command output is stored exactly as received.

### Silver

Normalized row-level sighting views.

### Gold

Operational views for:

* latest castle/enemy state
* alliance and owner summaries
* target prioritization
* world search
* tile density

---

## Manual World Scan Workflow

The world scan process is manual by design.

### Operator workflow

1. Open **World Scan Console**
2. Click a queue command
3. Copy the generated `\listcastles ...` command
4. Run it in the NeatBot command pane
5. Paste the returned result into the app
6. Ingest the scan
7. Repeat

### Tile status meanings

* `pending` — not yet scanned
* `copied` — command copied / in progress
* `complete` — returned rows below cap
* `empty` — no rows returned
* `saturated` — returned rows hit cap
* `split` — parent tile subdivided into child tiles

---

## Search and Analytics

### World Search

Search by:

* owner
* alliance

Results are sorted by:

* distance ascending
* then prestige descending

### Hit List

World Search also generates:

* a copyable text hit list
* downloadable CSV search results

### Rollups

Dedicated pages provide:

* owner rollup
* alliance rollup

### Teleport Efficiency

Tile density summary helps identify:

* dense city groupings
* better teleport destinations
* areas with many reachable targets

---

## Setup

### 1. Copy environment file

```powershell
Copy-Item .env.example .env
```

### 2. Start PostgreSQL

```powershell
docker compose up -d
```

### 3. Create uv environment

```powershell
uv venv .venv
```

### 4. Install dependencies

```powershell
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
```

### 5. Apply SQL init scripts

If the database is already running and new init files were added, apply them manually as needed.

Example:

```powershell
Get-Content .\sql\init\002_world_scan.sql -Raw | docker exec -i evony_enemy_analytics_postgres psql -U postgres -d evony_enemy_analytics
```

### 6. Seed initial world tile queue

```powershell
uv run python app\seed_world_tiles.py
```

### 7. Run dbt

```powershell
$env:DBT_PROFILES_DIR='E:\Evony\evony_enemy_analytics\.dbt'
uv run dbt run
```

### 8. Run Streamlit

```powershell
uv run streamlit run app/streamlit_app.py
```

---

## dbt Notes

Current warehouse objects include hostile and world-scan models.

Examples:

* `public_silver.stg_bronze_enemy_scan_rows`
* `public_silver.stg_enemy_sightings`
* `public_gold.enemy_master`
* `public_gold.alliance_summary`
* `public_gold.owner_summary`
* `public_gold.target_scoring`
* `public_silver.stg_world_castle_sightings`
* `public_gold.world_castle_master`
* `public_gold.world_tile_summary`

---

## Data Modeling Notes

This project is fact-first and history-preserving.

### Current pattern

* append-only raw sightings
* latest-state gold views built from those sightings

### Slowly changing dimensions

This system is intended to evolve toward SCD-aware modeling for:

* city coordinates
* city ownership
* alliance membership
* prestige
* honor
* castle names
* city level and status

For now, history is preserved in fact-like observation tables and latest-state views are computed on top.

---

## Current Limitations

* NeatBot commands must be run manually
* command output must be pasted manually
* scout XML integration is currently deferred
* some map-density workflows may still require tile subdivision in dense regions

---
