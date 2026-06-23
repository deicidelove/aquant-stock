from fastapi import FastAPI

from server.routers import health


def create_app(start_scheduler: bool = True) -> FastAPI:
    app = FastAPI(title="Aquant API", version="2.0")
    app.include_router(health.router)
    # 调度器在 Task 6 接入；此处保留参数占位
    app.state.start_scheduler = start_scheduler
    return app
