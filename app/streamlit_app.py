# Version: v0.2.5 | Date: 2026-03-25
from pathlib import Path
import sys
from uuid import uuid4

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from sqlalchemy import text

from config import BRONZE_PARSED_DIR, BRONZE_RAW_DIR
from db import (
    get_engine,
    insert_bronze_raw,
    insert_bronze_rows,
    insert_world_scan_raw,
    insert_world_scan_rows,
    upsert_world_scan_tile,
    mark_world_scan_tile_status,
    split_world_scan_tile,
    mark_tiles_for_rescan,
    test_connection,
)
from parser import parse_searchenemies_text
from transforms import build_bronze_rows, build_world_scan_rows


def build_tile_key(x1, y1, x2, y2):
    return f"{x1}_{y1}__{x2}_{y2}"


def build_cmd(x1, y1, x2, y2, maxtowns):
    return f"\\listcastles {x1},{y1} {x2},{y2} {maxtowns}"


def read_sql(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def queue_tile(row):
    st.session_state["pending_tile"] = {
        "x1": int(row["x1"]),
        "y1": int(row["y1"]),
        "x2": int(row["x2"]),
        "y2": int(row["y2"]),
        "maxtowns": int(row["maxtowns"]),
        "tile_key": row["tile_key"],
    }


def apply_pending_tile():
    data = st.session_state.pop("pending_tile", None)
    if data:
        st.session_state["x1"] = data["x1"]
        st.session_state["y1"] = data["y1"]
        st.session_state["x2"] = data["x2"]
        st.session_state["y2"] = data["y2"]
        st.session_state["maxtowns"] = data["maxtowns"]
        st.session_state["tile_key"] = data["tile_key"]


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def build_hit_list(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    lines = []
    for _, row in df.iterrows():
        coords = row.get("coords", "")
        owner = row.get("owner_name", "")
        alliance = row.get("alliance_name", "")
        castle = row.get("castle_name", "")
        distance = row.get("distance", "")
        prestige = row.get("prestige", "")
        honor = row.get("honor", "")
        lines.append(
            f"{coords} | dist={distance} | owner={owner} | alliance={alliance} | castle={castle} | prestige={prestige} | honor={honor}"
        )
    return "\n".join(lines)


st.set_page_config(layout="wide")
st.title("Evony Enemy Analytics")

with st.sidebar:
    st.subheader("System")
    try:
        test_connection()
        st.success("DB OK")
    except Exception as e:
        st.error(str(e))

tabs = st.tabs(
    [
        "Bronze Ingest",
        "Latest Enemies",
        "Alliance Summary",
        "Owner Summary",
        "Top Targets",
        "World Scan Console",
        "World Search",
        "Owner Rollup",
        "Alliance Rollup",
    ]
)

(
    tab_ingest,
    tab_latest,
    tab_alliance,
    tab_owner,
    tab_targets,
    tab_world,
    tab_world_search,
    tab_owner_rollup,
    tab_alliance_rollup,
) = tabs


with tab_ingest:
    raw_text = st.text_area("Paste searchenemies", height=300)

    if st.button("Ingest Bronze"):
        parsed = parse_searchenemies_text(raw_text)
        scan_id = str(uuid4())
        df = build_bronze_rows(parsed, scan_id)

        raw_path = BRONZE_RAW_DIR / f"enemy_scan_{scan_id}.txt"
        parsed_path = BRONZE_PARSED_DIR / f"enemy_scan_{scan_id}.parquet"
        raw_path.write_text(raw_text, encoding="utf-8")
        df.to_parquet(parsed_path, index=False)

        insert_bronze_raw(scan_id, raw_text, len(df))
        insert_bronze_rows(df)

        st.success(f"Loaded {len(df)} rows")
        st.dataframe(df, use_container_width=True)


with tab_latest:
    try:
        df_latest = read_sql("""
            select *
            from public_gold.enemy_master
            order by distance asc nulls last, prestige desc nulls last
        """)
        st.download_button(
            "Download Latest Enemies CSV",
            data=df_to_csv_bytes(df_latest),
            file_name="latest_enemies.csv",
            mime="text/csv",
        )
        st.dataframe(df_latest, use_container_width=True, height=700)
    except Exception:
        st.info("Run dbt")


with tab_alliance:
    try:
        df_alliance = read_sql("""
            select *
            from public_gold.alliance_summary
            order by enemy_count desc, avg_prestige desc nulls last
        """)
        st.download_button(
            "Download Alliance Summary CSV",
            data=df_to_csv_bytes(df_alliance),
            file_name="alliance_summary.csv",
            mime="text/csv",
        )
        st.dataframe(df_alliance, use_container_width=True, height=700)
    except Exception:
        st.info("Run dbt")


with tab_owner:
    try:
        df_owner = read_sql("""
            select *
            from public_gold.owner_summary
            order by city_count desc, max_prestige desc nulls last
        """)
        st.download_button(
            "Download Owner Summary CSV",
            data=df_to_csv_bytes(df_owner),
            file_name="owner_summary.csv",
            mime="text/csv",
        )
        st.dataframe(df_owner, use_container_width=True, height=700)
    except Exception:
        st.info("Run dbt")


with tab_targets:
    try:
        df_targets = read_sql("""
            select *
            from public_gold.target_scoring
            order by total_score desc
        """)
        st.download_button(
            "Download Top Targets CSV",
            data=df_to_csv_bytes(df_targets),
            file_name="top_targets.csv",
            mime="text/csv",
        )
        st.dataframe(df_targets, use_container_width=True, height=700)
    except Exception:
        st.info("Run dbt")


with tab_world:
    st.subheader("World Scan Console")

    apply_pending_tile()

    st.session_state.setdefault("x1", 0)
    st.session_state.setdefault("y1", 0)
    st.session_state.setdefault("x2", 99)
    st.session_state.setdefault("y2", 99)
    st.session_state.setdefault("maxtowns", 1000)

    top_left, top_mid, top_right = st.columns([3, 2, 2])

    with top_left:
        st.markdown("### Scan Queue")
    with top_mid:
        if st.button("Mark 7d+ Tiles For Rescan"):
            try:
                updated = mark_tiles_for_rescan(7)
                st.success(f"Marked {updated} tiles for rescan")
                st.rerun()
            except Exception as exc:
                st.exception(exc)
    with top_right:
        st.caption("Saturated tiles can be split into child quadrants.")

    df = read_sql("""
        select *
        from ops.world_scan_tiles
        order by
            case status
                when 'pending' then 1
                when 'copied' then 2
                when 'saturated' then 3
                when 'split' then 4
                when 'complete' then 5
                when 'empty' then 6
                else 7
            end,
            needs_rescan desc,
            depth,
            y1,
            x1
        limit 25
    """)

    for _, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 1])

        cmd = build_cmd(row["x1"], row["y1"], row["x2"], row["y2"], row["maxtowns"])

        with col1:
            st.code(cmd)

        with col2:
            if st.button(f"Load {row['tile_key']}", key=f"L{row['tile_key']}"):
                queue_tile(row)
                st.rerun()

        with col3:
            if st.button(f"Copy {row['tile_key']}", key=f"C{row['tile_key']}"):
                mark_world_scan_tile_status(row["tile_key"], "copied")
                queue_tile(row)
                st.rerun()

        with col4:
            if str(row["status"]) == "saturated":
                if st.button(f"Split {row['tile_key']}", key=f"S{row['tile_key']}"):
                    try:
                        created = split_world_scan_tile(str(row["tile_key"]))
                        st.success(f"Split tile {row['tile_key']} into {created} child tiles")
                        st.rerun()
                    except Exception as exc:
                        st.exception(exc)
            else:
                st.caption("")

        with col5:
            badge = str(row["status"])
            if bool(row.get("needs_rescan", False)):
                badge += " | rescan"
            st.caption(badge)

    st.markdown("---")

    st.markdown("### Active Tile")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        x1 = st.number_input("x1", 0, 799, key="x1")
    with c2:
        y1 = st.number_input("y1", 0, 799, key="y1")
    with c3:
        x2 = st.number_input("x2", 0, 799, key="x2")
    with c4:
        y2 = st.number_input("y2", 0, 799, key="y2")
    with c5:
        maxtowns = st.number_input("maxtowns", 1, 5000, key="maxtowns")

    tile_key = build_tile_key(x1, y1, x2, y2)
    cmd = build_cmd(x1, y1, x2, y2, maxtowns)

    st.code(cmd)

    active_col1, active_col2 = st.columns([1, 1])
    with active_col1:
        if st.button("Mark Copied (Active)"):
            mark_world_scan_tile_status(tile_key, "copied")
            st.success(f"Marked copied: {tile_key}")
    with active_col2:
        if st.button("Split Active Tile"):
            try:
                created = split_world_scan_tile(tile_key)
                st.success(f"Split active tile into {created} child tiles")
                st.rerun()
            except Exception as exc:
                st.exception(exc)

    st.markdown("### Paste Result")

    raw = st.text_area("Paste listcastles output", height=300)

    if st.button("Ingest Scan", type="primary"):
        try:
            parsed = parse_searchenemies_text(raw)

            scan_id = str(uuid4())

            df_rows = build_world_scan_rows(
                parsed,
                world_scan_id=scan_id,
                tile_key=tile_key,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )

            count = len(df_rows)
            saturated = count == maxtowns
            status = "empty" if count == 0 else ("saturated" if saturated else "complete")

            insert_world_scan_raw(
                world_scan_id=scan_id,
                command_text=cmd,
                scan_type="listcastles",
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                maxtowns=maxtowns,
                returned_rows=count,
                is_saturated=saturated,
                raw_text=raw,
            )

            if count > 0:
                insert_world_scan_rows(df_rows)

            upsert_world_scan_tile(
                tile_key=tile_key,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                maxtowns=maxtowns,
                status=status,
                returned_rows=count,
                is_saturated=saturated,
                world_scan_id=scan_id,
            )

            st.success(f"{status.upper()} | rows={count}")

            if count > 0:
                st.dataframe(df_rows, use_container_width=True, height=300)

            st.rerun()

        except Exception as e:
            st.exception(e)


with tab_world_search:
    st.subheader("World Search")

    left, _ = st.columns([1, 3])

    with left:
        search_mode = st.radio("Search by", ["Owner", "Alliance"], horizontal=False)
        search_value = st.text_input("Search text")

    if search_value.strip():
        if search_mode == "Owner":
            sql = """
                select
                    coords,
                    distance,
                    state,
                    level,
                    castle_name,
                    owner_name,
                    alliance_name,
                    prestige,
                    honor,
                    x,
                    y,
                    times_seen,
                    last_seen_at_utc
                from public_gold.world_castle_master
                where owner_name ilike :pattern
                order by distance asc nulls last, prestige desc nulls last
            """
            download_name = f"owner_search_{search_value.strip()}.csv"
            hit_name = f"owner_hit_list_{search_value.strip()}.txt"
        else:
            sql = """
                select
                    coords,
                    distance,
                    state,
                    level,
                    castle_name,
                    owner_name,
                    alliance_name,
                    prestige,
                    honor,
                    x,
                    y,
                    times_seen,
                    last_seen_at_utc
                from public_gold.world_castle_master
                where alliance_name ilike :pattern
                order by distance asc nulls last, prestige desc nulls last
            """
            download_name = f"alliance_search_{search_value.strip()}.csv"
            hit_name = f"alliance_hit_list_{search_value.strip()}.txt"

        df_search = read_sql(sql, {"pattern": f"%{search_value.strip()}%"})
        hit_list = build_hit_list(df_search)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "Download Search Results CSV",
                data=df_to_csv_bytes(df_search),
                file_name=download_name,
                mime="text/csv",
            )
        with dl2:
            st.download_button(
                "Download Copyable Hit List TXT",
                data=hit_list.encode("utf-8"),
                file_name=hit_name,
                mime="text/plain",
            )

        st.markdown("### Copyable Hit List")
        st.text_area("Hit list", value=hit_list, height=180)

        st.markdown("### Matching Cities")
        st.dataframe(df_search, use_container_width=True, height=500)

        try:
            df_cluster = read_sql("""
                select
                    tile_key,
                    city_count,
                    owner_count,
                    alliance_count,
                    avg_distance,
                    min_distance,
                    max_distance,
                    max_prestige,
                    max_honor
                from public_gold.world_tile_summary
                order by city_count desc, max_prestige desc nulls last
                limit 25
            """)
            st.markdown("### Cluster Density")
            st.dataframe(df_cluster, use_container_width=True, height=300)
        except Exception:
            st.info("Run dbt model public_gold.world_tile_summary")
    else:
        st.caption("Enter an owner or alliance search term to view matching cities sorted by distance.")

        try:
            df_cluster = read_sql("""
                select
                    tile_key,
                    city_count,
                    owner_count,
                    alliance_count,
                    avg_distance,
                    min_distance,
                    max_distance,
                    max_prestige,
                    max_honor
                from public_gold.world_tile_summary
                order by city_count desc, max_prestige desc nulls last
                limit 25
            """)
            st.markdown("### Dense Target Areas")
            st.dataframe(df_cluster, use_container_width=True, height=400)
        except Exception:
            st.info("Run dbt model public_gold.world_tile_summary")


with tab_owner_rollup:
    st.subheader("Owner Rollup")

    try:
        df_owner_rollup = read_sql("""
            select
                owner_name,
                coalesce(nullif(alliance_name, ''), '(blank)') as alliance_name,
                count(*) as city_count,
                min(distance) as nearest_city_distance,
                avg(distance) as avg_distance,
                max(prestige) as max_prestige,
                max(honor) as max_honor,
                sum(times_seen) as total_sightings
            from public_gold.world_castle_master
            group by owner_name, coalesce(nullif(alliance_name, ''), '(blank)')
            order by city_count desc, max_prestige desc nulls last, nearest_city_distance asc nulls last
        """)
        st.download_button(
            "Download Owner Rollup CSV",
            data=df_to_csv_bytes(df_owner_rollup),
            file_name="owner_rollup.csv",
            mime="text/csv",
        )
        st.dataframe(df_owner_rollup, use_container_width=True, height=700)
    except Exception as exc:
        st.info(f"Owner rollup not ready yet: {exc}")


with tab_alliance_rollup:
    st.subheader("Alliance Rollup")

    try:
        df_alliance_rollup = read_sql("""
            select
                coalesce(nullif(alliance_name, ''), '(blank)') as alliance_name,
                count(*) as city_count,
                count(distinct owner_name) as owner_count,
                min(distance) as nearest_city_distance,
                avg(distance) as avg_distance,
                max(prestige) as max_prestige,
                max(honor) as max_honor,
                sum(times_seen) as total_sightings
            from public_gold.world_castle_master
            group by coalesce(nullif(alliance_name, ''), '(blank)')
            order by city_count desc, owner_count desc, max_prestige desc nulls last
        """)
        st.download_button(
            "Download Alliance Rollup CSV",
            data=df_to_csv_bytes(df_alliance_rollup),
            file_name="alliance_rollup.csv",
            mime="text/csv",
        )
        st.dataframe(df_alliance_rollup, use_container_width=True, height=700)
    except Exception as exc:
        st.info(f"Alliance rollup not ready yet: {exc}")