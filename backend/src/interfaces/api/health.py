from fastapi import APIRouter

from infrastructure.db import check_database


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    db_ok = check_database()

    if db_ok:
        return {
            "status": "ok",
            "db": "ok",
        }

    return {
        "status": "degraded",
        "db": "fail",
    }