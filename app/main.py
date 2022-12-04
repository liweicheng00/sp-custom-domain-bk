from fastapi import FastAPI
from app.routers import cloud
from pulumi import automation as auto

app = FastAPI(redoc_url=None)

app.include_router(cloud.router)


def ensure_plugins():
    ws = auto.LocalWorkspace()
    ws.install_plugin("aws", "v4.0.0")


ensure_plugins()


@app.get("/")
def read_root():
    return {"Hello": "World"}
