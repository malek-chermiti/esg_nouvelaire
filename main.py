from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.co2_controller import router as co2_router
from app.controllers.fuel_surcharge_controller import router as fuel_surcharge_router
from app.controllers.waste_management_controller import router as waste_management_router
from app.controllers.employee_controller import router as employee_router
from app.controllers.training_controller import router as training_router
from app.controllers.work_accident_controller import router as work_accident_router
from app.controllers.payment_tracking_controller import router as payment_tracking_router
from app.controllers.tax_obligation_controller import router as tax_obligation_router
from app.controllers.aviation_license_controller import router as aviation_license_router
from app.controllers.user_controller import router as user_router
from app.controllers.pillar_controller import router as pillar_router

app = FastAPI(title="ESG Nouvelair API")

# Add CORS middleware to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(co2_router)
app.include_router(fuel_surcharge_router)
app.include_router(waste_management_router)
app.include_router(employee_router)
app.include_router(training_router)
app.include_router(work_accident_router)
app.include_router(payment_tracking_router)
app.include_router(tax_obligation_router)
app.include_router(aviation_license_router)
app.include_router(user_router)
app.include_router(pillar_router)

@app.get("/")
def root():
    return {"message": "ESG Nouvelair API fonctionne!"}