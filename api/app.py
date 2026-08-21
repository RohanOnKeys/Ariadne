"""
app.py

FastAPI application factory: mounts the catalog/objects/conjunctions
routers, enables CORS for the dashboard's origin, and turns any
`AriadneError` the routers let through into a JSON error response
instead of a 500 traceback (mirrors how the CLI catches `AriadneError`
at its boundary, see `ariadne/cli/*`).

Run with: uvicorn api.app:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import catalog, conjunctions, objects
from ariadne.config.settings import CORS_ORIGINS
from ariadne.exceptions import AriadneError, FetchError


def create_app() -> FastAPI:
    app = FastAPI(title="Ariadne API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(catalog.router)
    app.include_router(objects.router)
    app.include_router(conjunctions.router)

    @app.exception_handler(AriadneError)
    def handle_ariadne_error(request: Request, exc: AriadneError) -> JSONResponse:
        status_code = 502 if isinstance(exc, FetchError) else 400
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
