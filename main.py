from fastapi import FastAPI
from app.controllers.co2_controller import router as co2_router
from app.controllers.fuel_surcharge_controller import router as fuel_surcharge_router
from app.controllers.waste_management_controller import router as waste_management_router
from app.controllers.employee_controller import router as employee_router
from app.controllers.training_controller import router as training_router

app = FastAPI(title="ESG Nouvelair API")

# Include routers
app.include_router(co2_router)
app.include_router(fuel_surcharge_router)
app.include_router(waste_management_router)
app.include_router(employee_router)
app.include_router(training_router)

@app.get("/")
def root():
    return {"message": "ESG Nouvelair API fonctionne!"}