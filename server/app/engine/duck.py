import os
from typing import Dict, List, Tuple, Any
import duckdb
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


_CONN = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _CONN
    if _CONN is None:
        _CONN = duckdb.connect(database=':memory:')
    return _CONN


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


def ensure_views() -> Dict[str, bool]:
    """Create or replace views for core tables over CSV or Parquet if present."""
    con = get_conn()
    tables = ["Customer", "Inventory", "Detail", "Pricelist"]
    created: Dict[str, bool] = {}

    def _lit(path: str) -> str:
        # SQL string literal escape for DuckDB
        return "'" + path.replace("'", "''") + "'"

    for t in tables:
        pq = _parquet_path(t)
        csv = _csv_path(t)
        if os.path.exists(pq):
            logger.info(f"Loading {t} from parquet: {pq}")
            con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet({_lit(pq)})")
            # Log row count
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            logger.info(f"  {t}: {count} rows loaded from parquet")
            created[t] = True
        elif os.path.exists(csv):
            logger.info(f"Loading {t} from CSV: {csv}")
            # Use read_csv_auto for flexible schema inference
            con.execute(
                f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_csv_auto({_lit(csv)}, HEADER=TRUE)"
            )
            # Log row count
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            logger.info(f"  {t}: {count} rows loaded from CSV")
            created[t] = True
        else:
            logger.warning(f"No data file found for {t}")
            created[t] = False
    
    # Log sample data to verify loading
    if created.get("Inventory"):
        sample = con.execute("SELECT * FROM Inventory LIMIT 3").fetchall()
        logger.info(f"Sample Inventory data: {sample}")
    
    return created


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
