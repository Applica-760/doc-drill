from fastapi import FastAPI

from app.routers import documents, questions

app = FastAPI()

app.include_router(documents.router)
app.include_router(questions.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
