from fastapi import FastAPI

from app.routers import documents

app = FastAPI()

app.include_router(documents.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
