from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cloud
from pulumi import automation as auto

app = FastAPI(redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(cloud.router)


def ensure_plugins():
    ws = auto.LocalWorkspace()
    ws.install_plugin("aws", "v4.0.0")


ensure_plugins()


@app.get("/")
def read_root():
    return {"Hello": "World"}
