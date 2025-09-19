from fastapi import FastAPI

# Ultra-minimal app for testing
app = FastAPI(title="Bible Verse Checker - Minimal Test")

@app.get("/")
def root():
    return {"message": "Hello from Bible Verse Checker!", "status": "minimal_test"}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "minimal"}

@app.get("/ping")
def ping():
    return {"ping": "pong"}