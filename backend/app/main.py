from fastapi import FastAPI

app = FastAPI(title="Electronics Sales Agent")


@app.get("/health")
def health_check():
    return {"status": "ok"}
