from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.routers import cockpit, health, stock


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
    return app
