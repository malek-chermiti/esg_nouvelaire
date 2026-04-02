from fastapi import FastAPI
from app.controllers.co2_controller import router as co2_router

app = FastAPI(title="ESG Nouvelair API")

# Include routers
app.include_router(co2_router)

@app.get("/")
def root():
    return {"message": "ESG Nouvelair API fonctionne!"}