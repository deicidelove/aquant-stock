from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.routers import assist, cockpit, health, holdings, macro, quant, stock, watchlist


def create_app(start_scheduler: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sched = None
        if start_scheduler:
            from server.refresh.scheduler import build_scheduler
            sched = build_scheduler()
            sched.start()
        try:
            yield
        finally:
            if sched is not None:
                sched.shutdown(wait=False)

    app = FastAPI(title="Aquant API", version="2.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(cockpit.router)
    app.include_router(stock.router)
    app.include_router(holdings.router)
    app.include_router(assist.router)
    app.include_router(quant.router)
    app.include_router(macro.router)
    app.include_router(watchlist.router)
    return app
