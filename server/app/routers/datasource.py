from fastapi import APIRouter

from ..engine import duck
from ..validators import guards


router = APIRouter(prefix="/datasource", tags=["datasource"])


def _error(message: str, suggestion: str = "Retry with valid data files and schema."):
    return {"error": message, "suggestion": suggestion}


@router.post("/refresh")
def refresh_datasource():
    try:
        built = duck.build_parquet_cache()
        views = duck.ensure_views()
        counts = duck.table_counts()
        duck.clear_cache()
        return {
            "status": "ok",
            "parquet_built": built,
            "views": views,
            "counts": counts,
        }
    except Exception as e:
        return _error(str(e), "Check CSV paths, permissions, and formats.")
