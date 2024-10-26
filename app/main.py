from fastapi import FastAPI

app = FastAPI()

from app.api import routes
app.include_router(routes.router)