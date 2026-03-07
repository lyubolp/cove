"""Entry point for the Cove FastAPI application.

Registers all route routers and exposes a /health endpoint.
"""

from importlib.metadata import version

from fastapi import FastAPI

from cove.routes import api_keys, key_value, projects, users

app = FastAPI(version=version("cove"))


app.include_router(api_keys.router)
app.include_router(key_value.router)
app.include_router(projects.router)
app.include_router(users.router)


@app.get("/health")
async def ping():
    """Health-check endpoint. Returns a simple status payload."""
    return {"message": "healthy"}
