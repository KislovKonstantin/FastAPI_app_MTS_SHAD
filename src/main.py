from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from icecream import ic

from src.configurations.database import create_db_and_tables, global_init
from src.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ic("Inicializing app...")
    global_init()
    await create_db_and_tables()
    ic("App started!")
    yield

app = FastAPI(
    title="Book Shop App",
    description="Итоговый проект по Python для MTS Shad",
    version="0.0.1",
    responses={404: {"description": "Object not found!"}},
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

@app.get("/main", include_in_schema=False)
async def main():
    return "Hello World!"


app.include_router(api_router)
