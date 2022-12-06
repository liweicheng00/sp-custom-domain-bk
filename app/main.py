from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cloud

app = FastAPI(redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(cloud.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
