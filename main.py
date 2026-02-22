from fastapi import FastAPI

from cove.routes import key_value, projects

app = FastAPI()


app.include_router(key_value.router)
app.include_router(projects.router)


@app.get("/health")
async def ping():
    return {"message": "healthy"}
