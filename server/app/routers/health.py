import os
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck():
    try:
        return {
            "status": "ok",
            "data_dir": os.environ.get("DATA_DIR", "./server/data"),
            "service": "api",
        }
    except Exception as e:
        return {"error": str(e), "suggestion": "Restart the server and retry."}
