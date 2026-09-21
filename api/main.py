from fastapi import FastAPI

app = FastAPI(
    title="SAKU Smart POS API",
    description="Backend API untuk SAKU Smart POS",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "message": "SAKU Smart POS API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }