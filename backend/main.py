from fastapi import FastAPI

app = FastAPI(title="Aegis Backend API", description="Backend for Aegis Digital Twin Framework")

@app.get("/")
def read_root():
    return {"message": "Welcome to Aegis Backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}