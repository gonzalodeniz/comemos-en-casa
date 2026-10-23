from fastapi import FastAPI

app = FastAPI(title="Comemos en casa API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
