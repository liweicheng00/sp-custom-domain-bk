from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR
import datetime

from app.cron_job.background import subgraph_mission
from app.routers import ws, login, metadata
from app.config import settings
from app.utils.redis import MetadataRedisPool
from app.setup import init_db

app = FastAPI(docs_url=settings.docs_url, redoc_url=None)

app.include_router(ws.router)
app.include_router(login.router)
app.include_router(metadata.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts
)

Schedule = AsyncIOScheduler()
Schedule.start()

metadata_redis = MetadataRedisPool()
app.redis = metadata_redis


def listener(arg):
    print(arg)
    Schedule.add_job(metadata_redis.subscribe, id='subscribe_redis')


@app.on_event("startup")
async def startup_event():
    print('startup')
    init_db()
    await metadata_redis.init_redis_data()
    Schedule.add_job(metadata_redis.subscribe, id='subscribe_redis')
    Schedule.add_listener(listener, mask=EVENT_JOB_ERROR)


@app.on_event("shutdown")
async def startup_event():
    print('shotdown')
    Schedule.remove_job("subscribe_redis")


@app.get("/")
def read_root():
    return {"Hello": "World", "env": settings.runtime_env}


@app.get("/ping")
def ping():
    return "is ok"


@app.get('/background')
def do_background(background_tasks: BackgroundTasks):
    background_tasks.add_task(subgraph_mission)
    return 'Do background job once.'


@app.get("/time")
def get_server_time():
    return datetime.datetime.now().timestamp()
