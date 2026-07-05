from fastapi import APIRouter

from aquant.portfolio import watchlist
from server.schemas.watchlist import CodeIn, Codes

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=Codes)
def get_watchlist() -> Codes:
    return Codes(codes=watchlist.list_codes())


@router.post("", response_model=Codes)
def add_watchlist(body: CodeIn) -> Codes:
    watchlist.add(body.code)
    return Codes(codes=watchlist.list_codes())


@router.delete("/{code}", response_model=Codes)
def remove_watchlist(code: str) -> Codes:
    watchlist.remove(code)
    return Codes(codes=watchlist.list_codes())
