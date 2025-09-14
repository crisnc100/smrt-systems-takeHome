import os
from typing import Dict, List, Tuple, Any, Optional
import duckdb
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
import logging
import json
import threading

logger = logging.getLogger(__name__)


# Thread-local storage for connections
_thread_local = threading.local()
# Global data version to track when data changes
_data_version = 0
_version_lock = threading.Lock()


def get_conn() -> duckdb.DuckDBPyConnection:
    global _data_version
    if not hasattr(_thread_local, 'conn'):
        _thread_local.conn = duckdb.connect(database=':memory:', read_only=False)
        _thread_local.views_created = False
        _thread_local.data_version = -1
    # Check if data has been updated
    if _thread_local.data_version != _data_version:
        # Create/recreate views for this connection
        _ensure_views_for_connection(_thread_local.conn)
        _thread_local.data_version = _data_version
        _thread_local.views_created = True
    return _thread_local.conn


def invalidate_all_connections():
    """Call this after uploading new data to force all threads to reload."""
    global _data_version
    with _version_lock:
        _data_version += 1


def get_data_dir() -> str:
    # Default to server/data when running from repo root
    env_dir = os.environ.get("DATA_DIR")
    if env_dir:
        return env_dir
    here = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(here, "data")


def _csv_path(name: str) -> str:
    return os.path.join(get_data_dir(), f"{name}.csv")


def _parquet_path(name: str) -> str:
    return os.path.join(get_data_dir(), f"{name}.parquet")


def _load_alias_map() -> Dict[str, Dict[str, List[str]]]:
    """Load alias_map.json from the data directory if present.
    Structure:
    {
      "customer": {"cid": ["customer_id", "CID"], "name": ["full_name", "name"], ...},
      "inventory": {"order_date": ["date", "orderDate", "order_date"], ...},
      ...
    }
    """
    path = os.path.join(get_data_dir(), "alias_map.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # normalize keys to lowercase
                norm: Dict[str, Dict[str, List[str]]] = {}
                for tbl, cols in (data or {}).items():
                    tkey = str(tbl).lower()
                    norm[tkey] = {}
                    for canon, syns in (cols or {}).items():
                        norm[tkey][str(canon).lower()] = [str(s).lower() for s in (syns or [])]
                return norm
    except Exception:
        pass
    return {}


def _ensure_views_for_connection(con: duckdb.DuckDBPyConnection) -> Dict[str, bool]:
    """Create or replace views for core tables over CSV or Parquet if present."""
    # Use the passed connection directly
    tables = ["Customer", "Inventory", "Detail", "Pricelist"]
    created: Dict[str, bool] = {}

    def _lit(path: str) -> str:
        # SQL string literal escape for DuckDB
        return "'" + path.replace("'", "''") + "'"

    alias_map = _load_alias_map()

    for t in tables:
        pq = _parquet_path(t)
        csv = _csv_path(t)
        raw_view = f"_{t}_raw"
        if os.path.exists(pq):
            logger.info(f"Loading {t} from parquet: {pq}")
            con.execute(f"CREATE OR REPLACE VIEW {raw_view} AS SELECT * FROM read_parquet({_lit(pq)})")
            created[t] = True
        elif os.path.exists(csv):
            logger.info(f"Loading {t} from CSV: {csv}")
            con.execute(
                f"CREATE OR REPLACE VIEW {raw_view} AS SELECT * FROM read_csv_auto({_lit(csv)}, HEADER=TRUE)"
            )
            created[t] = True
        else:
            logger.warning(f"No data file found for {t}")
            created[t] = False

        # If not created, skip aliasing
        if not created.get(t):
            continue

        # Apply alias mapping if present
        tbl_key = t.lower()
        tbl_alias = alias_map.get(tbl_key, {})
        if tbl_alias:
            # get raw columns
            try:
                desc = con.execute(f"SELECT * FROM {raw_view} LIMIT 0").description
                raw_cols = [c[0] for c in desc]
                lower_map = {c.lower(): c for c in raw_cols}
                select_list: List[str] = []
                for canon, syns in tbl_alias.items():
                    # include canon itself as a synonym fallback
                    candidates = [canon] + syns
                    found: Optional[str] = None
                    for cand in candidates:
                        if cand in lower_map:
                            found = lower_map[cand]
                            break
                    if found:
                        select_list.append(f'"{found}" AS {canon}')
                    else:
                        # keep column present as NULL if missing
                        select_list.append(f'NULL AS {canon}')
                # Always materialize to canonical view name
                projection = ", ".join(select_list) if select_list else "*"
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT {projection} FROM {raw_view}")
            except Exception as e:
                logger.warning(f"Alias mapping failed for {t}: {e}; falling back to raw view")
                con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM {raw_view}")
        else:
            # No alias mapping -> direct pass-through
            con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM {raw_view}")

        # Log row count and sample
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            logger.info(f"  {t}: {count} rows loaded")
            if t == "Inventory":
                sample = con.execute("SELECT * FROM Inventory LIMIT 3").fetchall()
                logger.info(f"Sample Inventory data: {sample}")
        except Exception:
            pass

    return created


def ensure_views() -> Dict[str, bool]:
    """Public function to ensure views are created for the current thread's connection."""
    con = get_conn()
    return {}


def build_parquet_cache() -> Dict[str, bool]:
    """Create Parquet cache files alongside CSVs if not present."""
    con = get_conn()
    tables = ["Customer", "Inventory", "Detail", "Pricelist"]
    built: Dict[str, bool] = {}
    for t in tables:
        csv = _csv_path(t)
        pq = _parquet_path(t)
        if os.path.exists(csv):
            # Always rebuild for simplicity; could skip if pq newer than csv
            csv_lit = "'" + csv.replace("'", "''") + "'"
            pq_lit = "'" + pq.replace("'", "''") + "'"
            con.execute(
                f"COPY (SELECT * FROM read_csv_auto({csv_lit}, HEADER=TRUE)) TO {pq_lit} (FORMAT PARQUET)"
            )
            built[t] = True
        else:
            built[t] = False
    return built


def table_counts() -> Dict[str, int]:
    con = get_conn()
    counts: Dict[str, int] = {}
    for t in ["Customer", "Inventory", "Detail", "Pricelist"]:
        try:
            counts[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            counts[t] = 0
    return counts


def query(sql: str, params: Tuple[Any, ...] = ()) -> List[tuple]:
    con = get_conn()
    return con.execute(sql, params).fetchall()


def query_df(sql: str, params: Tuple[Any, ...] = ()):  # type: ignore
    con = get_conn()
    try:
        import pandas as pd  # noqa: F401
        return con.execute(sql, params).fetchdf()
    except Exception:
        # Fallback to rows if pandas missing; callers should handle
        return None


# Simple LRU caching for repeated identical queries
@lru_cache(maxsize=128)
def _cached_rows(sql: str, params: Tuple[Any, ...]) -> Tuple[tuple, ...]:
    rows = tuple(query(sql, params))
    return rows


def cached_query(sql: str, params: Tuple[Any, ...] = ()) -> List[tuple]:
    return list(_cached_rows(sql, params))


def clear_cache():
    _cached_rows.cache_clear()


def query_with_timeout(sql: str, params: Tuple[Any, ...] = (), timeout_s: float = 2.0) -> List[tuple]:
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(query, sql, params)
        try:
            return fut.result(timeout=timeout_s)
        except FuturesTimeout:
            raise TimeoutError(f"Query exceeded timeout of {timeout_s} seconds")
