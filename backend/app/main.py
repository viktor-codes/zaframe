from fastapi import FastAPI

app = FastAPI(title="ZaFrame API")

@app.get("/")
async def root():
    return {"message": "Welcome to ZaFrame API - Irish Dance & Yoga Booking"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}